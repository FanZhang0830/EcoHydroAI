import requests
import geopandas as gpd
import leafmap

# ==========================================
# Configuration
# ==========================================

# ESRI MapServer layer URL
LAYER_URL = (
    "https://gis.rvca.ca/server/rest/services/"
    "RVCA_Hydrology_Service/MapServer/4/query"
)

# Query parameters
params = {
    "where": "1=1",
    "outFields": "*",
    "outSR": "4326",     # Use WGS84 projection
    "f": "geojson"       # Request GeoJSON format
}

# Output HTML file
OUTPUT_HTML = "outputs/base_map.html"

# ==========================================
# Fetch data from ESRI REST endpoint
# ==========================================

print("Fetching watershed data...")

response = requests.get(LAYER_URL, params=params)

if response.status_code != 200:
    raise Exception(f"Failed to fetch data: {response.status_code}")

data = response.json()

# ==========================================
# Convert GeoJSON to GeoDataFrame
# ==========================================

print("Converting to GeoDataFrame...")

gdf = gpd.GeoDataFrame.from_features(data["features"])

# Ensure CRS is WGS84
gdf.set_crs(epsg=4326, inplace=True)

print(f"Loaded {len(gdf)} watershed polygons")

# ==========================================
# Create interactive map
# ==========================================

print("Creating interactive map...")

# Center around Ottawa region
m = leafmap.Map(center=[45.42, -75.70], zoom=9)

# Add watershed layer
m.add_gdf(
    gdf,
    layer_name="Subwatersheds",
    info_mode="on_hover",
    style={
        "color": "blue",
        "weight": 1,
        "fillOpacity": 0.2
    }
)

# ==========================================
# Export to HTML
# ==========================================

print(f"Saving map to HTML: {OUTPUT_HTML}")

m.to_html(OUTPUT_HTML)

print("Done!")