"""
backend/app/routes/datasets.py
Endpoints for dataset listing, 2D slice extraction, and velocity vectors.
Connects directly to Dataset 02 (02_ocean_model_grid_samples.csv) and Dataset 05 (05_current_vectors_trajectory.csv).
"""

import math
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import numpy as np
import pandas as pd

from backend.app.schemas import DatasetSummary, SliceResponse, VectorsResponse, VectorPoint, ProvenanceInfo
from backend.science.dataset_loader import get_ocean_grid_data, get_current_vectors_data

router = APIRouter(tags=["Datasets"])


@router.get("/api/datasets", response_model=List[DatasetSummary])
async def list_datasets():
    """Lists available registered datasets dynamically populated from active backend dataset metadata."""
    try:
        grid_df = get_ocean_grid_data()
        timestamps = sorted(grid_df["time_utc"].dropna().astype(str).unique().tolist())
        depths = sorted(grid_df["depth_m"].dropna().unique().tolist())
        min_lat, max_lat = float(grid_df["lat"].min()), float(grid_df["lat"].max())
        min_lon, max_lon = float(grid_df["lon"].min()), float(grid_df["lon"].max())

        provenance = ProvenanceInfo(
            dataset_type="synthetic",
            source="OceanTwin Synthetic Demo Dataset (Dataset 02)",
            dataset_id="02_ocean_model_grid",
            region="Arabian Sea / Indian Ocean EEZ"
        )

        return [
            DatasetSummary(
                id="02_ocean_model_grid",
                name="Indian Ocean ROMS Synthetic Model Grid (Dataset 02)",
                description="Synthetic ocean model grid supporting Temp, Salinity, Currents (u/v), SSH, Chlorophyll.",
                grid_type="regular",
                spatial_bounds={"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon},
                depth_levels=[float(d) for d in depths],
                time_steps=timestamps,
                variables=["temp", "salinity", "currents", "waves", "ssh", "chlorophyll"],
                provenance=provenance
            )
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


@router.get("/api/datasets/{dataset_id}/slice", response_model=SliceResponse)
@router.get("/api/slice", response_model=SliceResponse)
async def get_slice(
    dataset_id: str = "default",
    variable: str = Query("temp", description="temp | salinity | currents | ssh | chlorophyll"),
    depth: float = Query(0.0, description="Depth level in meters"),
    time: Optional[str] = Query(None, description="ISO timestamp string or index")
):
    """Extracts a 2D spatial grid slice of requested variable at target depth and time step from Dataset 02."""
    if variable.lower() == "waves":
        raise HTTPException(
            status_code=400,
            detail="Wave variables belong to Dataset 06 (/api/waves). Do not query Dataset 02 for wave slices."
        )

    try:
        grid_df = get_ocean_grid_data()

        # Map variable to column name
        col_map = {
            "temp": "model_temp_c",
            "temperature": "model_temp_c",
            "salinity": "model_salinity_psu",
            "currents": "current_speed_ms",
            "u_ms": "u_ms",
            "v_ms": "v_ms",
            "ssh": "ssh_m",
            "chlorophyll": "chlorophyll_mg_m3"
        }
        col_name = col_map.get(variable.lower(), "model_temp_c")

        # Select closest depth
        available_depths = np.array(sorted(grid_df["depth_m"].unique()))
        closest_depth = float(available_depths[np.argmin(np.abs(available_depths - depth))])

        # Filter depth
        df_sub = grid_df[grid_df["depth_m"] == closest_depth].copy()

        # Select time
        available_times = sorted(df_sub["time_utc"].unique().tolist())
        if time:
            if time.isdigit():
                idx = min(int(time), len(available_times) - 1)
                selected_time = available_times[idx]
            elif time in available_times:
                selected_time = time
            else:
                selected_time = available_times[0]
        else:
            selected_time = available_times[0]

        df_slice = df_sub[df_sub["time_utc"] == selected_time]

        # Pivot to lat-lon 2D matrix
        lats = sorted(df_slice["lat"].unique().tolist())
        lons = sorted(df_slice["lon"].unique().tolist())

        pivot_df = df_slice.pivot(index="lat", columns="lon", values=col_name)

        values_grid = []
        for lat in lats:
            row_vals = []
            for lon in lons:
                if lat in pivot_df.index and lon in pivot_df.columns:
                    v = pivot_df.loc[lat, lon]
                    row_vals.append(round(float(v), 3) if pd.notnull(v) else None)
                else:
                    row_vals.append(None)
            values_grid.append(row_vals)

        valid_vals = df_slice[col_name].dropna().to_numpy()
        min_v = float(np.min(valid_vals)) if len(valid_vals) > 0 else 0.0
        max_v = float(np.max(valid_vals)) if len(valid_vals) > 0 else 1.0

        units_map = {
            "temp": "°C",
            "salinity": "PSU",
            "currents": "m/s",
            "ssh": "m",
            "chlorophyll": "mg/m³"
        }

        provenance = ProvenanceInfo(
            dataset_type="synthetic",
            source="OceanTwin Synthetic Demo Dataset (Dataset 02)",
            dataset_id="02_ocean_model_grid",
            timestamp=selected_time,
            depth_m=closest_depth,
            region="Arabian Sea / Indian Ocean EEZ"
        )

        return SliceResponse(
            datasetId=dataset_id,
            variable=variable,
            depth=closest_depth,
            time=selected_time,
            minVal=round(min_v, 2),
            maxVal=round(max_v, 2),
            units=units_map.get(variable.lower(), ""),
            latitudes=[round(float(l), 4) for l in lats],
            longitudes=[round(float(l), 4) for l in lons],
            values=values_grid,
            provenance=provenance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Slice extraction error: {str(e)}")


@router.get("/api/datasets/{dataset_id}/vectors", response_model=VectorsResponse)
@router.get("/api/vectors", response_model=VectorsResponse)
async def get_vectors(
    dataset_id: str = "default",
    depth: float = Query(0.0, description="Depth level in meters"),
    time: Optional[str] = Query(None, description="ISO timestamp string or index"),
    stride: int = Query(1, description="Subsampling stride")
):
    """Subsamples horizontal current velocity vectors (u, v) from Dataset 05 or Dataset 02."""
    try:
        try:
            vec_df = get_current_vectors_data()
        except Exception:
            vec_df = get_ocean_grid_data()

        # Select closest depth if depth_m column exists
        if "depth_m" in vec_df.columns:
            available_depths = np.array(sorted(vec_df["depth_m"].unique()))
            closest_depth = float(available_depths[np.argmin(np.abs(available_depths - depth))])
            df_sub = vec_df[vec_df["depth_m"] == closest_depth]
        else:
            closest_depth = 0.0
            df_sub = vec_df

        # Subsample with stride
        sub_df = df_sub.iloc[::stride].copy()

        vectors = []
        for _, row in sub_df.iterrows():
            u_val = float(row["u_ms"])
            v_val = float(row["v_ms"])
            speed = float(row.get("current_speed_ms", math.sqrt(u_val**2 + v_val**2)))
            direction = (math.degrees(math.atan2(u_val, v_val)) + 360) % 360

            vectors.append(
                VectorPoint(
                    lat=round(float(row["lat"]), 4),
                    lon=round(float(row["lon"]), 4),
                    u=round(u_val, 3),
                    v=round(v_val, 3),
                    speed=round(speed, 3),
                    directionDeg=round(direction, 1)
                )
            )

        provenance = ProvenanceInfo(
            dataset_type="synthetic",
            source="OceanTwin Synthetic Demo Dataset (Dataset 05 / 02)",
            dataset_id="05_current_vectors",
            depth_m=closest_depth,
            region="Arabian Sea / Indian Ocean EEZ"
        )

        selected_time = str(df_sub["time_utc"].iloc[0]) if "time_utc" in df_sub.columns else "2026-08-23T00:00:00Z"

        return VectorsResponse(
            datasetId=dataset_id,
            depth=closest_depth,
            time=selected_time,
            vectorCount=len(vectors),
            vectors=vectors,
            provenance=provenance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Vectors extraction error: {str(e)}")
