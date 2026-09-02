"""
backend/api/routers/compare.py
FastAPI Router for Model-Observation Comparison and Anomaly Calculation Services.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies import get_comparison_service, get_anomaly_service
from backend.api.services.comparison_service import ComparisonService
from backend.api.services.anomaly_service import AnomalyService
from backend.api.schemas.comparison import ComparisonPointResponse, AnomalyResponse

router = APIRouter(prefix="/api", tags=["Model-Observation Comparison & Anomalies"])


@router.get("/compare", response_model=ComparisonPointResponse)
def compare_model_and_observation(
    platform_number: Optional[str] = Query(None, description="Argo Float Platform WMO ID"),
    cycle_number: Optional[int] = Query(None, description="Float profile cycle index"),
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude coordinate"),
    depth: Optional[float] = Query(None, ge=0.0, le=12000.0, description="Depth level in meters"),
    time: Optional[str] = Query(None, description="Timestamp (ISO8601 string)"),
    observed_temperature: Optional[float] = Query(None, description="Observed temperature in °C"),
    observed_salinity: Optional[float] = Query(None, description="Observed salinity in PSU"),
    comparison_service: ComparisonService = Depends(get_comparison_service),
):
    """
    Compare HYCOM model predictions against an Argo float profile observation or explicit measurement point.
    Returns matched model value, observed value, error (model - observed), current vectors, and spatial-temporal metrics.
    """
    try:
        return comparison_service.compare_point(
            platform_number=platform_number,
            cycle_number=cycle_number,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            time=time,
            observed_temperature=observed_temperature,
            observed_salinity=observed_salinity,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing comparison service: {str(e)}")


@router.get("/anomaly", response_model=AnomalyResponse)
def calculate_ocean_anomaly(
    variable: str = Query("temperature", description="Variable (temperature or salinity)"),
    value: float = Query(..., description="Current observed or model value"),
    time: str = Query(..., description="Observation timestamp (ISO8601 string)"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    depth: float = Query(5.0, ge=0.0, le=2000.0, description="Depth level in meters"),
    anomaly_service: AnomalyService = Depends(get_anomaly_service),
):
    """
    Calculate ocean temperature or salinity anomaly (Δ = value - baseline_mean) and Z-score
    against historical 5-year INCOIS VAM monthly climatology baseline.
    """
    try:
        return anomaly_service.calculate_anomaly(
            variable=variable,
            value=value,
            time=time,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing anomaly service: {str(e)}")
