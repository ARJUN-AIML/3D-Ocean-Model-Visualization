"""
backend/api/routers/ocean.py
FastAPI Router for Ocean Data Slicing, Variable Discovery, and Fused Digital Twin Queries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies import (
    get_ocean_service,
    get_hycom_service,
    get_argo_service,
    get_vam_baseline_service,
)
from backend.api.services.ocean_service import OceanService
from backend.api.services.hycom_service import HycomService
from backend.api.services.argo_service import ArgoService
from backend.api.services.vam_baseline_service import VAMBaselineService
from backend.api.schemas.ocean import VariableSummary, OceanSliceResponse

router = APIRouter(prefix="/api/ocean", tags=["Ocean Digital Twin Services"])


@router.get("/variables", response_model=List[VariableSummary])
def list_dataset_variables(
    dataset_id: str = Query(..., description="Target dataset filename in data/ directory"),
    ocean_service: OceanService = Depends(get_ocean_service),
) -> List[VariableSummary]:
    """Lists all variables available in a dataset with canonical names, physical units, and ranges."""
    return ocean_service.get_available_variables(dataset_id)


@router.get("/slice", response_model=OceanSliceResponse)
def get_ocean_slice(
    dataset_id: str = Query(..., description="Target dataset filename in data/ directory"),
    variable: str = Query(..., description="Variable name to slice"),
    time: str = Query(..., description="ISO8601 target timestamp"),
    depth: float = Query(0.0, description="Target depth level in meters"),
    lat_min: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Minimum bounding latitude"),
    lat_max: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Maximum bounding latitude"),
    lon_min: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Minimum bounding longitude"),
    lon_max: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Maximum bounding longitude"),
    downsample: Optional[int] = Query(1, ge=1, le=20, description="Grid downsampling stride step"),
    ocean_service: OceanService = Depends(get_ocean_service),
) -> OceanSliceResponse:
    """Extracts a 2D depth/time slice grid payload for 3D visualization."""
    return ocean_service.get_ocean_slice(
        dataset_id=dataset_id,
        variable=variable,
        time=time,
        depth=depth,
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        downsample=downsample,
    )


@router.get("/point")
def get_fused_ocean_point(
    variable: str = Query("temperature", description="Variable (temperature, salinity, u, v)"),
    time: str = Query(..., description="Timestamp (ISO8601 string)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    depth: float = Query(0.0, ge=0.0, le=12000.0, description="Depth level in meters"),
    hycom_service: HycomService = Depends(get_hycom_service),
    vam_service: VAMBaselineService = Depends(get_vam_baseline_service),
):
    """
    Unified Fused Digital Twin Point Endpoint.
    Combines HYCOM model prediction, VAM historical baseline, and calculated anomaly for a point.
    """
    try:
        hycom_res = hycom_service.get_point(variable, time, latitude, longitude, depth)
        
        # Get baseline if temperature or salinity
        if variable.lower() in ["temperature", "temp", "salinity", "saln", "sal"]:
            from pandas import to_datetime
            month = to_datetime(time, utc=True).month
            baseline_res = vam_service.get_baseline_point(variable, month, latitude, longitude, depth)
            b_mean = baseline_res["baseline_mean"]
            b_std = baseline_res["baseline_std"]
        else:
            b_mean = None
            b_std = None

        m_val = hycom_res["value"]
        anomaly = (m_val - b_mean) if (m_val is not None and b_mean is not None) else None

        return {
            "source": "OceanTwin Fused Engine",
            "variable": hycom_res["variable"],
            "units": hycom_res["units"],
            "time": time,
            "latitude": latitude,
            "longitude": longitude,
            "depth": depth,
            "hycom_model_value": m_val,
            "baseline_mean_value": b_mean,
            "baseline_std_value": b_std,
            "model_anomaly": round(anomaly, 4) if anomaly is not None else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting fused ocean point: {str(e)}")


@router.get("/profile")
def get_fused_ocean_profile(
    variable: str = Query("temperature", description="Variable (temperature, salinity, u, v)"),
    time: str = Query(..., description="Timestamp (ISO8601 string)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    hycom_service: HycomService = Depends(get_hycom_service),
    vam_service: VAMBaselineService = Depends(get_vam_baseline_service),
):
    """
    Unified Fused Digital Twin Vertical Profile Endpoint.
    Combines HYCOM model profile and VAM historical baseline profile across depth levels.
    """
    try:
        hycom_prof = hycom_service.get_profile(variable, time, latitude, longitude)
        
        if variable.lower() in ["temperature", "temp", "salinity", "saln", "sal"]:
            from pandas import to_datetime
            month = to_datetime(time, utc=True).month
            vam_prof = vam_service.get_baseline_profile(variable, month, latitude, longitude)
            b_depths = vam_prof["depths"]
            b_means = vam_prof["baseline_means"]
        else:
            b_depths = []
            b_means = []

        return {
            "source": "OceanTwin Fused Engine",
            "variable": hycom_prof["variable"],
            "units": hycom_prof["units"],
            "time": time,
            "latitude": latitude,
            "longitude": longitude,
            "hycom_profile": {
                "depths": hycom_prof["depths"],
                "values": hycom_prof["values"],
            },
            "baseline_profile": {
                "depths": b_depths,
                "means": b_means,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting fused ocean profile: {str(e)}")
