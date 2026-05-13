# app/api/routes/health.py

from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
    tags=["Health"]
)


@router.get("/health")
def health_check():
    """
    Health check endpoint.

    This endpoint is used to verify that the FastAPI backend
    is running correctly.
    """

    return {
        "status": "ok",
        "message": "EcoHydroAI API is running"
    }