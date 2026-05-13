# services/load_lidar.py

import folium

# ==========================================
# RVCA LiDAR Tile Service
# ==========================================

LIDAR_TILE_URL = (
    "https://gis.rvca.ca/server/rest/services/"
    "RVCA_DRAPE2019_Cache/MapServer/"
    "tile/{z}/{y}/{x}"
)


def add_lidar_layer(map_object):
    """
    Add RVCA LiDAR cached raster tiles
    to a Leafmap/Folium map.
    """

    folium.raster_layers.TileLayer(
        tiles=LIDAR_TILE_URL,
        attr="RVCA LiDAR",
        name="RVCA LiDAR",
        overlay=True,
        control=True,
        opacity=1.0,
        max_native_zoom=12,
        max_zoom=18
    ).add_to(map_object)

    return map_object