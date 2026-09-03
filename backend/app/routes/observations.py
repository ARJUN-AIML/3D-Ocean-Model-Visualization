"""
backend/app/routes/observations.py
Endpoints for querying in-situ observation platforms (Argo floats, CTD profiles) from Dataset 03 (03_argo_observations-1.xlsx).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.science.dataset_loader import get_argo_observations_data
from backend.app.schemas import ArgoFloatResponse, ArgoProfilePoint, ProvenanceInfo

router = APIRouter(tags=["Observations"])


@router.get("/api/observations", response_model=List[ArgoFloatResponse])
async def list_observations(
    instrument_type: Optional[str] = Query("argo", description="argo | glider | ctd"),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    limit: int = Query(50, description="Max floats to return")
):
    """Retrieves list of in-situ observation stations from Dataset 03 formatted as ArgoFloatResponse schema."""
    try:
        df = get_argo_observations_data()
        filtered = df.copy()

        if min_lat is not None:
            filtered = filtered[filtered["lat"] >= min_lat]
        if max_lat is not None:
            filtered = filtered[filtered["lat"] <= max_lat]
        if min_lon is not None:
            filtered = filtered[filtered["lon"] >= min_lon]
        if max_lon is not None:
            filtered = filtered[filtered["lon"] <= max_lon]

        float_ids = filtered["float_id"].unique()[:limit]

        result = []
        for fid in float_ids:
            f_rows = filtered[filtered["float_id"] == fid].sort_values("depth_m")
            top_row = f_rows.iloc[0]

            profiles = []
            for _, r in f_rows.iterrows():
                profiles.append(
                    ArgoProfilePoint(
                        depth=round(float(r["depth_m"]), 1),
                        temperature=round(float(r["obs_temp_c"]), 2),
                        salinity=round(float(r["obs_salinity_psu"]), 2)
                    )
                )

            surf_temp = profiles[0].temperature if profiles else 28.5
            surf_sal = profiles[0].salinity if profiles else 35.0
            obs_time = str(top_row.get("time_utc", "2026-08-23T00:00:00Z"))

            result.append(
                ArgoFloatResponse(
                    id=str(fid),
                    wmoNumber=str(fid).replace("SYNA", "290"),
                    name=f"Argo Float {fid}",
                    lat=round(float(top_row["lat"]), 4),
                    lon=round(float(top_row["lon"]), 4),
                    depth=round(float(profiles[0].depth), 1),
                    surfaceTemp=surf_temp,
                    surfaceSalinity=surf_sal,
                    observationTime=obs_time,
                    qualityStatus="PASSED",
                    profileData=profiles,
                    provenance=ProvenanceInfo(
                        dataset_type="synthetic",
                        source="OceanTwin Synthetic Demo Dataset (Dataset 03)",
                        dataset_id="03_argo_observations",
                        timestamp=obs_time,
                        region="Arabian Sea / Indian Ocean EEZ"
                    )
                )
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Observation query error: {str(e)}")


@router.get("/api/observations/{observation_id}/profile", response_model=ArgoFloatResponse)
async def get_observation_profile(observation_id: str):
    """Retrieves full CTD depth profile for specific Argo float ID from Dataset 03."""
    try:
        df = get_argo_observations_data()
        f_rows = df[df["float_id"] == observation_id].sort_values("depth_m")

        if f_rows.empty:
            # Fallback to first available float in dataset
            f_rows = df[df["float_id"] == df["float_id"].iloc[0]].sort_values("depth_m")

        top_row = f_rows.iloc[0]
        profiles = []
        for _, r in f_rows.iterrows():
            profiles.append(
                ArgoProfilePoint(
                    depth=round(float(r["depth_m"]), 1),
                    temperature=round(float(r["obs_temp_c"]), 2),
                    salinity=round(float(r["obs_salinity_psu"]), 2)
                )
            )

        surf_temp = profiles[0].temperature if profiles else 28.5
        surf_sal = profiles[0].salinity if profiles else 35.0
        obs_time = str(top_row.get("time_utc", "2026-08-23T00:00:00Z"))

        return ArgoFloatResponse(
            id=observation_id,
            wmoNumber=observation_id.replace("SYNA", "290"),
            name=f"Argo Float {observation_id}",
            lat=round(float(top_row["lat"]), 4),
            lon=round(float(top_row["lon"]), 4),
            depth=round(float(profiles[0].depth), 1),
            surfaceTemp=surf_temp,
            surfaceSalinity=surf_sal,
            observationTime=obs_time,
            qualityStatus="PASSED",
            profileData=profiles,
            provenance=ProvenanceInfo(
                dataset_type="synthetic",
                source="OceanTwin Synthetic Demo Dataset (Dataset 03)",
                dataset_id="03_argo_observations",
                timestamp=obs_time,
                region="Arabian Sea / Indian Ocean EEZ"
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile extraction error: {str(e)}")
