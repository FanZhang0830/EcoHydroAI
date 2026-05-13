# services/watershed_service.py

from functools import lru_cache

import geopandas as gpd

from data_access.esri_adapter import fetch_layer


SUBWATERSHED_LAYER_ID = 4


@lru_cache(maxsize=1)
def get_subwatersheds() -> gpd.GeoDataFrame:
    """
    Load subwatershed polygons from the ESRI REST endpoint.

    The result is cached to avoid requesting the ESRI service
    every time the API endpoint is called.
    """

    gdf = fetch_layer(SUBWATERSHED_LAYER_ID)

    # Ensure CRS is WGS84 for web mapping and API responses
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    return gdf


def _detect_id_field(gdf: gpd.GeoDataFrame) -> str:
    """
    Detect a reasonable ID field from the ESRI layer.
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


def _detect_name_field(gdf: gpd.GeoDataFrame) -> str | None:
    """
    Detect a reasonable name field from the ESRI layer.
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


def _calculate_area_km2(gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    """
    Calculate polygon area in square kilometers.

    The data is projected to EPSG:3857 for approximate area calculation.
    For production use, a local equal-area projection would be better.
    """

    projected = gdf.to_crs(epsg=3857)
    return projected.geometry.area / 1_000_000


def _calculate_centroids(gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    """
    Calculate centroid points and return them in WGS84.
    """

    projected = gdf.to_crs(epsg=3857)
    centroids = projected.geometry.centroid
    centroids_gdf = gpd.GeoDataFrame(geometry=centroids, crs="EPSG:3857")
    centroids_gdf = centroids_gdf.to_crs(epsg=4326)

    return centroids_gdf.geometry


def list_subwatersheds() -> list[dict]:
    """
    Return a lightweight list of subwatershed metadata.
    """

    gdf = get_subwatersheds()

    id_field = _detect_id_field(gdf)
    name_field = _detect_name_field(gdf)

    areas_km2 = _calculate_area_km2(gdf)
    centroids = _calculate_centroids(gdf)

    results = []

    for idx, row in gdf.iterrows():
        centroid = centroids.loc[idx]

        item = {
            "id": str(row[id_field]),
            "name": str(row[name_field]) if name_field else str(row[id_field]),
            "area_km2": round(float(areas_km2.loc[idx]), 3),
            "centroid": {
                "lat": round(float(centroid.y), 6),
                "lon": round(float(centroid.x), 6),
            },
        }

        results.append(item)

    return results


def get_subwatershed_summary(watershed_id: str) -> dict | None:
    """
    Return metadata for one subwatershed by ID.
    """

    gdf = get_subwatersheds()

    id_field = _detect_id_field(gdf)
    name_field = _detect_name_field(gdf)

    matched = gdf[gdf[id_field].astype(str) == str(watershed_id)]

    if matched.empty:
        return None

    row = matched.iloc[0]

    area_km2 = _calculate_area_km2(matched).iloc[0]
    centroid = _calculate_centroids(matched).iloc[0]

    return {
        "id": str(row[id_field]),
        "name": str(row[name_field]) if name_field else str(row[id_field]),
        "area_km2": round(float(area_km2), 3),
        "centroid": {
            "lat": round(float(centroid.y), 6),
            "lon": round(float(centroid.x), 6),
        },
    }