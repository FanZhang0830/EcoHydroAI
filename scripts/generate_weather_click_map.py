# scripts/generate_weather_click_map.py

import os

import folium
from branca.element import MacroElement
from jinja2 import Template

from services.watershed_service import get_subwatersheds


OUTPUT_HTML = "outputs/weather_click_map.html"

API_BASE_URL = "http://127.0.0.1:8000"


def detect_id_field(gdf):
    """
    Detect a suitable watershed ID field.
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
    Detect a suitable watershed name field.
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
                            <h4 style="margin-bottom: 6px;">${watershedName}</h4>
                            <p>Loading weather forecast...</p>
                        </div>
                    `;

                    layer.bindPopup(loadingHtml, {
                        maxWidth: 520
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

                        data.forecast.forEach(function(item) {
                            forecastRows += `
                                <tr>
                                    <td style="padding: 4px 6px;">${item.date}</td>
                                    <td style="padding: 4px 6px; text-align: right;">${item.temperature_max_c}</td>
                                    <td style="padding: 4px 6px; text-align: right;">${item.temperature_min_c}</td>
                                    <td style="padding: 4px 6px; text-align: right;">${item.precipitation_mm}</td>
                                </tr>
                            `;
                        });

                        const popupHtml = `
                            <div style="width: 460px; font-family: Arial, sans-serif;">
                                <h4 style="margin: 0 0 6px 0;">
                                    Watershed ${data.watershed_id}
                                </h4>

                                <div style="font-size: 12px; color: #555; margin-bottom: 8px;">
                                    Lat: ${data.location.lat}, Lon: ${data.location.lon}
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
                                    style="width: 100%; border: 1px solid #ddd;"
                                />
                            </div>
                        `;

                        layer.setPopupContent(popupHtml);

                    } catch (error) {

                        const errorHtml = `
                            <div style="width: 360px; font-family: Arial, sans-serif;">
                                <h4>${watershedName}</h4>
                                <p style="color: red;">
                                    Failed to load weather forecast.
                                </p>
                                <p style="font-size: 12px;">
                                    ${error.message}
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


def main():
    """
    Generate an interactive WebGIS map.

    The map allows users to click a watershed polygon and retrieve
    mock weather forecast data from the local FastAPI backend.
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

    # Add clean API-facing fields to the GeoJSON properties.
    # The JavaScript click handler will use these fields.
    gdf["api_watershed_id"] = gdf[id_field].astype(str)

    if name_field:
        gdf["api_watershed_name"] = gdf[name_field].astype(str)
    else:
        gdf["api_watershed_name"] = gdf[id_field].astype(str)

    print("Creating map...")

    center = [
        gdf.geometry.centroid.y.mean(),
        gdf.geometry.centroid.x.mean(),
    ]

    m = folium.Map(
        location=center,
        zoom_start=9,
        tiles=None,
    )

    # Stable imagery basemap
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri World Imagery",
        name="Esri World Imagery",
        overlay=False,
        control=True,
    ).add_to(m)

    # Optional labels overlay
    folium.TileLayer(
        tiles=(
            "https://{s}.basemaps.cartocdn.com/light_only_labels/"
            "{z}/{x}/{y}{r}.png"
        ),
        attr="CartoDB / OpenStreetMap contributors",
        name="Labels",
        overlay=True,
        control=True,
    ).add_to(m)

    watershed_geojson = folium.GeoJson(
        gdf,
        name="Subwatersheds",
        style_function=lambda feature: {
            "fillColor": "#3388ff",
            "color": "#003366",
            "weight": 1,
            "fillOpacity": 0.25,
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

    # Add custom JavaScript click behavior
    click_handler = WeatherClickHandler(
        geojson_layer_name=watershed_geojson.get_name(),
        api_base_url=API_BASE_URL,
    )

    m.get_root().add_child(click_handler)

    folium.LayerControl(collapsed=False).add_to(m)

    os.makedirs("outputs", exist_ok=True)

    print(f"Saving map to {OUTPUT_HTML}...")
    m.save(OUTPUT_HTML)

    print("Done.")
    print(f"Open this file in browser: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()