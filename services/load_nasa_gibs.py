# services/load_nasa_gibs.py

import folium


def add_nasa_gibs_layers(m):
    """
    Add stable NASA GIBS layers to a Folium/Leafmap map.

    Notes:
    - GIBS layers are time-dependent.
    - Some MODIS/NDVI layers may not have tiles for every date.
    - VIIRS True Color is usually a safer first test layer.
    """

    # Use a known historical date first for debugging.
    date = "2024-07-01"

    viirs_true_color = (
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
        f"VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{date}/"
        "GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg"
    )

    folium.TileLayer(
        tiles=viirs_true_color,
        name="NASA GIBS - VIIRS True Color",
        attr="NASA GIBS",
        overlay=True,
        control=True,
        show=False,
        max_zoom=9,
        opacity=0.85,
    ).add_to(m)