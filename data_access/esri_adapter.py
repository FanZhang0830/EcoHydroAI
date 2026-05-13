import requests
import geopandas as gpd


BASE_URL = (
    "https://gis.rvca.ca/server/rest/services/"
    "RVCA_Hydrology_Service/MapServer"
)


def fetch_layer(layer_id: int) -> gpd.GeoDataFrame:
    """
    Fetch a layer from ESRI REST endpoint
    and return as GeoDataFrame.
    """

    query_url = f"{BASE_URL}/{layer_id}/query"

    params = {
        "where": "1=1",
        "outFields": "*",
        "outSR": "4326",
        "f": "geojson"
    }

    response = requests.get(query_url, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed request: {response.status_code}")

    data = response.json()

    gdf = gpd.GeoDataFrame.from_features(data["features"])

    gdf.set_crs(epsg=4326, inplace=True)

    return gdf