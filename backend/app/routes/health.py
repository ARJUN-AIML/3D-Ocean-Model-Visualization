"""
backend/app/routes/health.py
Health check and system liveness endpoint.
"""

from fastapi import APIRouter
from backend.app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
async def get_health():
    """Returns liveness, version, and backend data connection mode."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        is_real_data_connected=True,
        provenance_mode="REAL DATA (FastAPI Connected)",
        message="INCOIS OceanTwin 3D FastAPI Backend Operational"
    )
