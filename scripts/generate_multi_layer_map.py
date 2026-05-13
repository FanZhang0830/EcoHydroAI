# scripts/generate_multi_layer_map.py

import folium
import leafmap.foliumap as leafmap

from services.watershed_service import get_subwatersheds
from services.load_esri_imagery import add_esri_imagery
from services.load_nasa_gibs import add_nasa_gibs_layers  # NEW

# ==========================================
# Output file
# ==========================================

OUTPUT_HTML = "outputs/multi_layer_map.html"

# ==========================================
# Initialize map
# ==========================================

print("Initializing map...")

m = leafmap.Map(
    center=[45.42, -75.70],
    zoom=7,
    tiles="CartoDB positron"
)

# ==========================================
# Add ESRI World Imagery (optional satellite base)
# ==========================================

print("Adding ESRI World Imagery...")

add_esri_imagery(m, add_hillshade=True)

# ==========================================
# Add NASA GIBS (NEW REMOTE SENSING LAYER)
# ==========================================

print("Adding NASA GIBS layers...")

add_nasa_gibs_layers(m)

# ==========================================
# Load watershed polygons
# ==========================================

print("Loading watershed polygons...")

gdf = get_subwatersheds()

m.add_gdf(
    gdf,
    layer_name="Subwatersheds",
    info_mode="on_click",
    style={
        "color": "cyan",
        "weight": 2,
        "fillOpacity": 0.05
    }
)

# ==========================================
# Layer control
# ==========================================

folium.LayerControl(collapsed=False).add_to(m)

# ==========================================
# Export HTML
# ==========================================

print("Exporting HTML...")

m.to_html(OUTPUT_HTML)

print("Done! Map saved to:", OUTPUT_HTML)