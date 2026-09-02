"""
backend/api/routers/hycom.py
FastAPI Router for HYCOM Model Data Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies import get_hycom_service
from backend.api.services.hycom_service import HycomService
from backend.api.schemas.hycom import HycomSummaryResponse, HycomPointResponse, HycomProfileResponse

router = APIRouter(prefix="/api/hycom", tags=["HYCOM Model Data"])


@router.get("", response_model=HycomSummaryResponse)
def get_hycom_summary(
    hycom_service: HycomService = Depends(get_hycom_service),
):
    """Retrieve HYCOM dataset metadata, dimension sizes, coordinate bounds, and variable list."""
    try:
        return hycom_service.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect HYCOM dataset: {str(e)}")


@router.get("/point", response_model=HycomPointResponse)
def get_hycom_point(
    variable: str = Query("temperature", description="HYCOM variable (temperature, salinity, u, v, ssh, mld, tchp)"),
    time: str = Query(..., description="Target time (ISO8601 string e.g. 2026-08-31T00:00:00Z)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    depth: float = Query(0.0, ge=0.0, le=12000.0, description="Depth level in meters"),
    hycom_service: HycomService = Depends(get_hycom_service),
):
    """Query HYCOM variable value at nearest spatial-temporal point."""
    try:
        return hycom_service.get_point(
            variable=variable,
            time=time,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting HYCOM point: {str(e)}")


@router.get("/profile", response_model=HycomProfileResponse)
def get_hycom_profile(
    variable: str = Query("temperature", description="HYCOM variable (temperature, salinity, u, v)"),
    time: str = Query(..., description="Target time (ISO8601 string)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    hycom_service: HycomService = Depends(get_hycom_service),
):
    """Query vertical depth profile across available HYCOM depth levels at lat/lon/time."""
    try:
        return hycom_service.get_profile(
            variable=variable,
            time=time,
            latitude=latitude,
            longitude=longitude,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting HYCOM profile: {str(e)}")
