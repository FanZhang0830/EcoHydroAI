# app/api/routes/watersheds.py

from fastapi import APIRouter, HTTPException

from services.watershed_service import (
    list_subwatersheds,
    get_subwatershed_summary,
)


router = APIRouter(
    prefix="/api/v1/watersheds",
    tags=["Watersheds"]
)


@router.get("")
def get_watersheds():
    """
    Return a list of subwatershed metadata.
    """

    return list_subwatersheds()


@router.get("/{watershed_id}")
def get_watershed(watershed_id: str):
    """
    Return metadata for a single subwatershed.
    """

    result = get_subwatershed_summary(watershed_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Watershed not found: {watershed_id}"
        )

    return result