# services/load_esri_imagery.py

import folium


ESRI_WORLD_IMAGERY_URL = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

ESRI_WORLD_HILL_SHADE_URL = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}"
)


def add_esri_imagery(m, add_hillshade=True):
    """
    Add ESRI World Imagery base layer to folium/leafmap map.

    Parameters
    ----------
    m : folium.Map or leafmap.Map
    add_hillshade : bool
        If True, also add terrain shading layer.
    """

    # =========================
    # Base imagery layer
    # =========================
    imagery = folium.TileLayer(
        tiles=ESRI_WORLD_IMAGERY_URL,
        name="ESRI World Imagery",
        attr="Tiles © Esri",
        overlay=False,
        control=True,
        show=True
    )
    imagery.add_to(m)

    # =========================
    # Optional hillshade layer
    # =========================
    if add_hillshade:
        hillshade = folium.TileLayer(
            tiles=ESRI_WORLD_HILL_SHADE_URL,
            name="ESRI Hillshade",
            attr="Tiles © Esri",
            overlay=True,
            control=True,
            opacity=0.35,
            show=False
        )
        hillshade.add_to(m)