"""
backend/api/routers/health.py
Health Check Router.
"""

from fastapi import APIRouter, Depends
from backend.api.config import APISettings
from backend.api.dependencies import get_settings
from backend.api.schemas.datasets import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(settings: APISettings = Depends(get_settings)) -> HealthResponse:
    """Returns service operational health status, title, and version."""
    return HealthResponse(
        status="ok",
        service_name=settings.API_TITLE,
        version=settings.API_VERSION,
    )
