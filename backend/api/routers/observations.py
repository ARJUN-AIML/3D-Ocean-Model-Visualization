"""
backend/api/routers/observations.py
In-Situ Argo Observation Discovery and Profile Query Router.
Serves cleaned INCOIS Indian Argo observation profiles.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies import get_argo_service
from backend.api.services.argo_service import ArgoService
from backend.api.schemas.observations import ObservationDiscoveryResponse

router = APIRouter(prefix="/api", tags=["Argo Observations"])


@router.get("/argo")
def get_argo_observations(
    platform_number: Optional[str] = Query(None, description="Filter by float platform WMO ID"),
    cycle_number: Optional[int] = Query(None, description="Filter by cycle index"),
    lat_min: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Minimum latitude"),
    lat_max: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Maximum latitude"),
    lon_min: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Minimum longitude"),
    lon_max: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Maximum longitude"),
    depth_min: Optional[float] = Query(None, ge=0.0, le=12000.0, description="Minimum depth in meters"),
    depth_max: Optional[float] = Query(None, ge=0.0, le=12000.0, description="Maximum depth in meters"),
    time_start: Optional[str] = Query(None, description="Start ISO8601 time"),
    time_end: Optional[str] = Query(None, description="End ISO8601 time"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Record pagination offset"),
    argo_service: ArgoService = Depends(get_argo_service),
):
    """Query cleaned INCOIS Indian Argo float observations with spatial/temporal/platform filtering."""
    try:
        return argo_service.get_observations(
            platform_number=platform_number,
            cycle_number=cycle_number,
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max,
            depth_min=depth_min,
            depth_max=depth_max,
            time_start=time_start,
            time_end=time_end,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Argo observations: {str(e)}")


@router.get("/argo/profile")
def get_argo_profile(
    platform_number: str = Query(..., description="Argo Float Platform WMO ID (e.g. 2901307)"),
    cycle_number: int = Query(..., description="Float profile cycle index (e.g. 322)"),
    argo_service: ArgoService = Depends(get_argo_service),
):
    """Retrieve full vertical depth profile (temperature, salinity, pressure, depth) for a single float cycle."""
    try:
        return argo_service.get_profile(
            platform_number=platform_number,
            cycle_number=cycle_number,
        )
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Argo profile: {str(e)}")


# Backward-compatibility endpoint for /api/observations
@router.get("/observations", response_model=ObservationDiscoveryResponse)
def discover_observations(
    sensor_type: Optional[str] = Query(None, description="Optional sensor filter: argo | glider"),
    start_time: Optional[str] = Query(None, description="Optional start time filter"),
    end_time: Optional[str] = Query(None, description="Optional end time filter"),
    argo_service: ArgoService = Depends(get_argo_service),
) -> ObservationDiscoveryResponse:
    """Backward compatibility discovery endpoint."""
    summary = argo_service.get_summary()
    return ObservationDiscoveryResponse(total_count=summary["total_observations"], observations=[])
