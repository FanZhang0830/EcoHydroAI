# scripts/generate_portal_map.py

import os

import folium
from branca.element import MacroElement
from jinja2 import Template

from services.watershed_service import get_subwatersheds


OUTPUT_HTML = "outputs/portal_map.html"

# FastAPI backend URL
# Local default: http://127.0.0.1:8000
# Deployment: set ECOHYDROAI_API_BASE_URL to the public backend URL
API_BASE_URL = os.getenv(
    "ECOHYDROAI_API_BASE_URL",
    "http://127.0.0.1:8000"
)

# --------------------------------------------------
# Field detection helpers
# --------------------------------------------------

def detect_id_field(gdf):
    """
    Detect a suitable watershed ID field from the GeoDataFrame.
    """

    candidate_fields = [
        "OBJECTID",
        "OBJECTID_1",
        "FID",
        "ID",
        "id",
        "SubwatershedID",
        "SUBWATERSHED_ID",
    ]

    for field in candidate_fields:
        if field in gdf.columns:
            return field

    raise ValueError(
        f"No suitable ID field found. Available columns: {list(gdf.columns)}"
    )


def detect_name_field(gdf):
    """
    Detect a suitable watershed name field from the GeoDataFrame.
    """

    candidate_fields = [
        "Name",
        "NAME",
        "name",
        "Subwatershed",
        "SUBWATERSHED",
        "SubwatershedName",
        "SUBWATERSHED_NAME",
    ]

    for field in candidate_fields:
        if field in gdf.columns:
            return field

    return None


# --------------------------------------------------
# Basemap and raster layers
# --------------------------------------------------

def add_esri_world_imagery(m):
    """
    Add ESRI World Imagery as the main satellite basemap.
    """

    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery",
        name="ESRI World Imagery",
        overlay=False,
        control=True,
    ).add_to(m)

    return m


def add_cartodb_labels(m):
    """
    Add CartoDB label-only layer on top of satellite imagery.
    """

    folium.TileLayer(
        tiles=(
            "https://{s}.basemaps.cartocdn.com/light_only_labels/"
            "{z}/{x}/{y}{r}.png"
        ),
        attr="CartoDB / OpenStreetMap contributors",
        name="CartoDB Labels",
        overlay=True,
        control=True,
    ).add_to(m)

    return m


def add_nasa_gibs_layer(m):
    """
    Add NASA GIBS MODIS Terra Corrected Reflectance layer.

    This is a tiled WMTS layer. The TIME parameter is fixed here
    for stability. You can update the date later or make it dynamic.
    """

    nasa_gibs_url = (
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
        "MODIS_Terra_CorrectedReflectance_TrueColor/default/"
        "2024-07-01/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg"
    )

    folium.TileLayer(
        tiles=nasa_gibs_url,
        attr="NASA GIBS",
        name="NASA GIBS MODIS Terra True Color",
        overlay=True,
        control=True,
        opacity=0.65,
        max_zoom=9,
    ).add_to(m)

    return m


# --------------------------------------------------
# Custom JavaScript click handler
# --------------------------------------------------

class WeatherClickHandler(MacroElement):
    """
    Add JavaScript click behavior to a Folium GeoJson layer.

    When a watershed polygon is clicked, the browser calls the FastAPI
    weather endpoint and displays the returned forecast and chart
    in a popup.
    """

    def __init__(self, geojson_layer_name, api_base_url):
        super().__init__()
        self._name = "WeatherClickHandler"
        self.geojson_layer_name = geojson_layer_name
        self.api_base_url = api_base_url

        self._template = Template(
            """
            {% macro script(this, kwargs) %}

            const watershedLayer = {{ this.geojson_layer_name }};

            watershedLayer.eachLayer(function(layer) {

                layer.on("click", async function(e) {

                    const props = layer.feature.properties;
                    const watershedId = props.api_watershed_id;
                    const watershedName = props.api_watershed_name;

                    const loadingHtml = `
                        <div style="width: 420px; font-family: Arial, sans-serif;">
                            <h4 style="margin-bottom: 6px;">Watershed ${watershedName}</h4>
                            <p>Loading weather forecast...</p>
                        </div>
                    `;

                    layer.bindPopup(loadingHtml, {
                        maxWidth: 560
                    }).openPopup();

                    const url = "{{ this.api_base_url }}/api/v1/watersheds/"
                                + watershedId
                                + "/weather";

                    try {
                        const response = await fetch(url);

                        if (!response.ok) {
                            throw new Error("API request failed: " + response.status);
                        }

                        const data = await response.json();

                        let forecastRows = "";
                        let totalPrecip = 0;

                        data.forecast.forEach(function(item) {

                            totalPrecip += Number(item.precipitation_mm);

                            forecastRows += `
                                <tr>
                                    <td style="padding: 4px 6px;">${item.date}</td>
                                    <td style="padding: 4px 6px; text-align: right;">${item.temperature_max_c}</td>
                                    <td style="padding: 4px 6px; text-align: right;">${item.temperature_min_c}</td>
                                    <td style="padding: 4px 6px; text-align: right;">${item.precipitation_mm}</td>
                                </tr>
                            `;
                        });

                        let riskLevel = "Low";
                        let riskColor = "#2e7d32";
                        let riskText = "No major rainfall concern based on the 3-day forecast.";

                        if (totalPrecip >= 25) {
                            riskLevel = "High";
                            riskColor = "#c62828";
                            riskText = "Elevated rainfall risk. Monitor low-lying areas and tributaries.";
                        } else if (totalPrecip >= 10) {
                            riskLevel = "Moderate";
                            riskColor = "#ef6c00";
                            riskText = "Moderate rainfall expected. Continue monitoring forecast updates.";
                        }

                        const popupHtml = `
                            <div style="
                                width: 480px;
                                font-family: Arial, sans-serif;
                                line-height: 1.35;
                            ">
                                <h4 style="margin: 0 0 6px 0;">
                                    Watershed ${data.watershed_id}
                                </h4>

                                <div style="font-size: 12px; color: #555; margin-bottom: 8px;">
                                    Lat: ${data.location.lat}, Lon: ${data.location.lon}
                                </div>

                                <div style="
                                    padding: 8px;
                                    border-radius: 6px;
                                    background: #f7f7f7;
                                    border-left: 5px solid ${riskColor};
                                    margin-bottom: 10px;
                                ">
                                    <div style="font-weight: bold; color: ${riskColor};">
                                        3-Day Rainfall Risk: ${riskLevel}
                                    </div>
                                    <div style="font-size: 12px;">
                                        Total precipitation: ${totalPrecip.toFixed(1)} mm
                                    </div>
                                    <div style="font-size: 12px; margin-top: 4px;">
                                        ${riskText}
                                    </div>
                                </div>

                                <table style="
                                    border-collapse: collapse;
                                    width: 100%;
                                    font-size: 12px;
                                    margin-bottom: 10px;
                                ">
                                    <thead>
                                        <tr style="background: #f2f2f2;">
                                            <th style="padding: 4px 6px; text-align: left;">Date</th>
                                            <th style="padding: 4px 6px; text-align: right;">Max °C</th>
                                            <th style="padding: 4px 6px; text-align: right;">Min °C</th>
                                            <th style="padding: 4px 6px; text-align: right;">Precip mm</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${forecastRows}
                                    </tbody>
                                </table>

                                <img
                                    src="data:image/png;base64,${data.chart_base64}"
                                    style="
                                        width: 100%;
                                        border: 1px solid #ddd;
                                        border-radius: 4px;
                                    "
                                />

                                <div style="
                                    margin-top: 8px;
                                    font-size: 11px;
                                    color: #777;
                                ">
                                    Weather data: Open-Meteo. Chart generated by EcoHydroAI backend.
                                </div>
                            </div>
                        `;

                        layer.setPopupContent(popupHtml);

                    } catch (error) {

                        const errorHtml = `
                            <div style="width: 380px; font-family: Arial, sans-serif;">
                                <h4>Watershed ${watershedName}</h4>
                                <p style="color: red;">
                                    Failed to load weather forecast.
                                </p>
                                <p style="font-size: 12px;">
                                    ${error.message}
                                </p>
                                <p style="font-size: 12px; color: #777;">
                                    Make sure the FastAPI backend is running at:
                                    {{ this.api_base_url }}
                                </p>
                            </div>
                        `;

                        layer.setPopupContent(errorHtml);
                    }
                });
            });

            {% endmacro %}
            """
        )


# --------------------------------------------------
# Main map generation
# --------------------------------------------------

def main():
    """
    Generate the integrated EcoHydroAI WebGIS portal map.

    This portal includes:
    - ESRI World Imagery basemap
    - CartoDB labels
    - NASA GIBS MODIS True Color layer
    - Subwatershed polygons
    - Click interaction with FastAPI weather endpoint
    """

    print("Loading subwatersheds...")
    gdf = get_subwatersheds()

    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    id_field = detect_id_field(gdf)
    name_field = detect_name_field(gdf)

    print(f"Using ID field: {id_field}")
    print(f"Using name field: {name_field}")

    # Add clean API-facing fields for JavaScript use.
    gdf["api_watershed_id"] = gdf[id_field].astype(str)

    if name_field:
        gdf["api_watershed_name"] = gdf[name_field].astype(str)
    else:
        gdf["api_watershed_name"] = gdf[id_field].astype(str)

    print("Creating portal map...")

    # Use projected centroids to avoid centroid warnings.
    gdf_projected = gdf.to_crs(epsg=3857)
    center_projected = gdf_projected.geometry.centroid.unary_union.centroid
    center_gdf = gdf_projected.set_geometry(
        gdf_projected.geometry.centroid
    ).to_crs(epsg=4326)

    center = [
        center_gdf.geometry.y.mean(),
        center_gdf.geometry.x.mean(),
    ]

    m = folium.Map(
        location=center,
        zoom_start=9,
        tiles=None,
        control_scale=True,
    )

    print("Adding basemaps and raster layers...")
    add_esri_world_imagery(m)
    add_cartodb_labels(m)
    add_nasa_gibs_layer(m)

    print("Adding subwatershed polygons...")

    watershed_geojson = folium.GeoJson(
        gdf,
        name="Subwatersheds",
        style_function=lambda feature: {
            "fillColor": "#3388ff",
            "color": "#003366",
            "weight": 1,
            "fillOpacity": 0.22,
        },
        highlight_function=lambda feature: {
            "fillColor": "#ffff99",
            "color": "#ff6600",
            "weight": 3,
            "fillOpacity": 0.45,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["api_watershed_id", "api_watershed_name"],
            aliases=["Watershed ID:", "Name:"],
            sticky=True,
        ),
    ).add_to(m)

    print("Adding click interaction...")
    click_handler = WeatherClickHandler(
        geojson_layer_name=watershed_geojson.get_name(),
        api_base_url=API_BASE_URL,
    )

    m.get_root().add_child(click_handler)

    folium.LayerControl(collapsed=False).add_to(m)

    os.makedirs("outputs", exist_ok=True)

    print(f"Saving portal map to {OUTPUT_HTML}...")
    m.save(OUTPUT_HTML)

    print("Done.")
    print(f"Open this file in browser: {OUTPUT_HTML}")
    print("Make sure FastAPI is running:")
    print("uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()