# services/load_sentinel.py

import ee

# ==========================================
# Initialize Google Earth Engine
# ==========================================

ee.Initialize("ecohydroai")

# ==========================================
# Study Area Definition
# ==========================================
#
# This bounding box defines the current study area.
# Update the coordinates below if the study site changes.
#
# Coordinate order:
# [min_lon, min_lat, max_lon, max_lat]
#
# Current region:
# Ottawa / RVCA region
#
# ==========================================

STUDY_AREA = ee.Geometry.Rectangle([
    -76.94072265625002,  # min longitude (west)
    44.55410804029227,  # min latitude (south)
    -75.25432128906252, # max longitude (east)
    45.56678842692987  # max latitude (north)
])

# ==========================================
# Sentinel-2 Image Collection Settings
# ==========================================

CLOUD_THRESHOLD = 30

START_DATE = "2025-01-01"
END_DATE = "2026-12-31"

# ==========================================
# Visualization Parameters
# ==========================================
#
# RGB visualization:
# B4 = Red
# B3 = Green
# B2 = Blue
#
# ==========================================

VIS_PARAMS = {
    "bands": ["B4", "B3", "B2"],
    "min": 0,
    "max": 3000
}


def get_recent_sentinel_layer():
    """
    Retrieve the most recent Sentinel-2 image
    with cloud coverage below the defined threshold.

    Returns:
        ee.Image: Sentinel-2 image
        dict: Visualization parameters
    """

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(STUDY_AREA)
        .filterDate(START_DATE, END_DATE)
        .filter(ee.Filter.lt(
            "CLOUDY_PIXEL_PERCENTAGE",
            CLOUD_THRESHOLD
        ))
        .sort("system:time_start", False)
    )

    image = collection.first().clip(STUDY_AREA)

    return image, VIS_PARAMS