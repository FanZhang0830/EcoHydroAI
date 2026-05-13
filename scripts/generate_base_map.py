import leafmap

from services.watershed_service import get_subwatersheds


OUTPUT_HTML = "outputs/base_map.html"


print("Loading subwatersheds...")

gdf = get_subwatersheds()

print("Creating map...")

m = leafmap.Map(center=[45.42, -75.70], zoom=9)

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

print("Exporting HTML...")

m.to_html(OUTPUT_HTML)

print("Done!")