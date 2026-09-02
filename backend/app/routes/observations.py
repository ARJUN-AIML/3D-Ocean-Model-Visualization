"""
backend/app/routes/observations.py
Endpoints for querying in-situ observation platforms (Argo floats, Gliders, CTD profiles).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.dependencies import get_default_dataset
from backend.app.schemas import ArgoFloatResponse, ArgoProfilePoint
from backend.app.adapters import adapt_observation_to_argo
from backend.science.sample_observations import generate_synthetic_observations

router = APIRouter(tags=["Observations"])


@router.get("/api/observations", response_model=List[ArgoFloatResponse])
async def list_observations(
    instrument_type: Optional[str] = Query("argo", description="argo | glider | ctd"),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None)
):
    """Retrieves list of in-situ observation stations formatted as frontend ArgoFloatResponse schema."""
    raw_obs_list = generate_synthetic_observations(num_argo=15, num_glider=10, num_ctd=5)

    if instrument_type:
        filtered = [o for o in raw_obs_list if o.instrument_type.lower() == instrument_type.lower()]
    else:
        filtered = raw_obs_list

    if not filtered:
        filtered = raw_obs_list

    result = [adapt_observation_to_argo(o) for o in filtered]
    return result


@router.get("/api/observations/{observation_id}/profile", response_model=ArgoFloatResponse)
async def get_observation_profile(observation_id: str):
    """Retrieves full CTD depth profile for specific Argo or observation platform ID."""
    raw_obs_list = generate_synthetic_observations(num_argo=15, num_glider=10, num_ctd=5)

    match = next((o for o in raw_obs_list if o.platform_id == observation_id or observation_id in o.platform_id), None)
    if match:
        return adapt_observation_to_argo(match)

    # Fallback default if specific ID is queried from frontend demo selection
    fallback_obs = raw_obs_list[0]
    res = adapt_observation_to_argo(fallback_obs)
    res.id = observation_id
    res.wmoNumber = observation_id.replace("ARGO_", "")
    res.name = f"Station Profile ({observation_id})"
    return res
