"""
backend/api/routers/baseline.py
FastAPI Router for Monthly Gridded Argo VAM Baseline Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies import get_vam_baseline_service
from backend.api.services.vam_baseline_service import VAMBaselineService
from backend.api.schemas.baseline import BaselineSummaryResponse, BaselinePointResponse, BaselineProfileResponse

router = APIRouter(prefix="/api/baseline", tags=["Monthly Baseline Data (VAM)"])


@router.get("", response_model=BaselineSummaryResponse)
def get_baseline_summary(
    vam_service: VAMBaselineService = Depends(get_vam_baseline_service),
):
    """Retrieve VAM Baseline dataset summary, depth levels, and coverage."""
    try:
        return vam_service.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect VAM Baseline dataset: {str(e)}")


@router.get("/point", response_model=BaselinePointResponse)
def get_baseline_point(
    variable: str = Query("temperature", description="Baseline variable (temperature or salinity)"),
    month: int = Query(..., ge=1, le=12, description="Target month of year (1-12)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    depth: float = Query(5.0, ge=0.0, le=2000.0, description="Depth in meters"),
    vam_service: VAMBaselineService = Depends(get_vam_baseline_service),
):
    """Query historical 5-year climatological baseline mean and std for a specific month, location, and depth."""
    try:
        return vam_service.get_baseline_point(
            variable=variable,
            month=month,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying VAM baseline point: {str(e)}")


@router.get("/profile", response_model=BaselineProfileResponse)
def get_baseline_profile(
    variable: str = Query("temperature", description="Baseline variable (temperature or salinity)"),
    month: int = Query(..., ge=1, le=12, description="Target month of year (1-12)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    vam_service: VAMBaselineService = Depends(get_vam_baseline_service),
):
    """Query vertical baseline mean and std profile across all 24 VAM depth levels (5m to 2000m)."""
    try:
        return vam_service.get_baseline_profile(
            variable=variable,
            month=month,
            latitude=latitude,
            longitude=longitude,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying VAM baseline profile: {str(e)}")
