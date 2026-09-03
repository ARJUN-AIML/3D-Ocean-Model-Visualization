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

from backend.app.schemas import (
    DatasetSummary,
    SliceResponse,
    VectorsResponse,
    VectorPoint,
    LocationPropertiesResponse,
    ArgoProfilePoint,
    ProvenanceInfo
)
from backend.science.dataset_loader import (
    get_ocean_grid_data,
    get_current_vectors_data,
    get_wave_samples_data,
    get_argo_observations_data
)

router = APIRouter(tags=["Datasets & Location Inspection"])


@router.get("/api/datasets", response_model=List[DatasetSummary])
async def list_datasets():
    """Lists available registered datasets dynamically populated from active backend dataset metadata."""
    try:
        grid_df = get_ocean_grid_data()
        time_col = "timestamp_utc" if "timestamp_utc" in grid_df.columns else "time_utc"
        timestamps = sorted(grid_df[time_col].dropna().astype(str).unique().tolist())
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
        time_col = "timestamp_utc" if "timestamp_utc" in df_sub.columns else "time_utc"
        available_times = sorted(df_sub[time_col].dropna().astype(str).unique().tolist())
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

        df_slice = df_sub[df_sub[time_col] == selected_time]

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


@router.get("/api/location-properties", response_model=LocationPropertiesResponse)
async def get_location_properties(
    lat: float = Query(..., description="Target Latitude"),
    lon: float = Query(..., description="Target Longitude"),
    depth: float = Query(0.0, description="Target Depth in meters"),
    time: Optional[str] = Query(None, description="Optional timestamp string or step index")
):
    """
    Returns full ocean state, waves, currents, anomaly, profile data, nearest station, and provenance
    for any requested latitude/longitude coordinate.
    """
    try:
        grid_df = get_ocean_grid_data()
        
        # Spatial distance in km (approx 1 deg = 111 km)
        grid_lats = grid_df["lat"].to_numpy()
        grid_lons = grid_df["lon"].to_numpy()
        dists = np.sqrt((grid_lats - lat) ** 2 + (grid_lons - lon) ** 2) * 111.0
        min_idx = np.argmin(dists)
        min_dist_km = float(dists[min_idx])
        
        # Coverage check: Include all Indian seas & ocean basin locations
        if min_dist_km > 4000.0:
            return LocationPropertiesResponse(
                available=False,
                reason="Location outside available ocean model coverage grid (Arabian Sea / Central Indian Ocean EEZ)",
                requestedLat=round(lat, 4),
                requestedLon=round(lon, 4),
                resolvedLat=round(float(grid_lats[min_idx]), 4),
                resolvedLon=round(float(grid_lons[min_idx]), 4),
                distanceKm=round(min_dist_km, 1),
                requestedDepth=depth,
                resolvedDepth=depth,
                requestedTime=time or "latest",
                resolvedTime="N/A",
                timeGapHours=0.0,
                regionName=f"Out of Coverage ({lat:.2f}°N, {lon:.2f}°E)",
                reliability="UNAVAILABLE",
                provenance=ProvenanceInfo(
                    dataset_type="synthetic",
                    source="Dataset 02 Boundary Check",
                    dataset_id="02_ocean_model_grid",
                    region="Global Ocean"
                )
            )

        # Nearest grid row
        nearest_row = grid_df.iloc[min_idx]
        resolved_lat = float(nearest_row["lat"])
        resolved_lon = float(nearest_row["lon"])
        
        # Closest depth
        if "depth_m" in grid_df.columns:
            depths = np.sort(grid_df["depth_m"].unique())
            closest_depth = float(depths[np.argmin(np.abs(depths - depth))])
            matching_depth_df = grid_df[(grid_df["lat"] == resolved_lat) & (grid_df["lon"] == resolved_lon) & (grid_df["depth_m"] == closest_depth)]
            if not matching_depth_df.empty:
                nearest_row = matching_depth_df.iloc[0]
        else:
            closest_depth = 0.0

        time_col = "timestamp_utc" if "timestamp_utc" in grid_df.columns else "time_utc"
        resolved_time = str(nearest_row.get(time_col, "2026-08-23T00:00:00Z"))

        # Ocean state
        temp_c = float(nearest_row["model_temp_c"]) if "model_temp_c" in nearest_row else None
        sal_psu = float(nearest_row["model_salinity_psu"]) if "model_salinity_psu" in nearest_row else None
        u_val = float(nearest_row["u_ms"]) if "u_ms" in nearest_row else None
        v_val = float(nearest_row["v_ms"]) if "v_ms" in nearest_row else None
        speed_val = float(nearest_row["current_speed_ms"]) if "current_speed_ms" in nearest_row else (
            round(math.sqrt(u_val**2 + v_val**2), 3) if u_val is not None and v_val is not None else None
        )

        # Wave data from Dataset 06
        wave_h = None
        wave_p = None
        wave_dir = None
        try:
            wave_df = get_wave_samples_data()
            w_lats = wave_df["lat"].to_numpy()
            w_lons = wave_df["lon"].to_numpy()
            w_dists = np.sqrt((w_lats - lat) ** 2 + (w_lons - lon) ** 2) * 111.0
            w_idx = np.argmin(w_dists)
            if w_dists[w_idx] <= 400.0:
                w_row = wave_df.iloc[w_idx]
                wave_h = round(float(w_row["significant_wave_height_m"]), 2)
                p_col = "peak_wave_period_sec" if "peak_wave_period_sec" in w_row else "peak_wave_period_s"
                wave_p = round(float(w_row.get(p_col, 8.0)), 1)
                wave_dir = round(float(w_row["mean_wave_direction_deg"]), 1)
        except Exception:
            pass

        # Anomaly / Bias estimate
        z_score = round(float((temp_c - 28.0) / 0.5), 2) if temp_c else 0.4
        anomaly_status = "NORMAL" if abs(z_score) < 1.5 else ("WARNING" if abs(z_score) < 2.5 else "CRITICAL")
        raw_temp = temp_c
        pred_bias = -0.12 if temp_c else 0.0
        corr_temp = round(temp_c - pred_bias, 2) if temp_c else None

        # Nearest Station / Observation Profile from Dataset 03
        profiles = []
        station_id = None
        station_dist = None
        plat_type = None
        try:
            obs_df = get_argo_observations_data()
            o_lats = obs_df["lat"].to_numpy()
            o_lons = obs_df["lon"].to_numpy()
            o_dists = np.sqrt((o_lats - lat) ** 2 + (o_lons - lon) ** 2) * 111.0
            o_idx = np.argmin(o_dists)
            station_dist = round(float(o_dists[o_idx]), 1)
            station_id = str(obs_df.iloc[o_idx]["float_id"])
            
            if station_id.startswith("SYNA100") or station_id.startswith("SYNA101"):
                plat_type = "ARGO_FLOAT"
            elif station_id.startswith("SYNA102") or station_id.startswith("SYNA103"):
                plat_type = "MOORED_BUOY"
            else:
                plat_type = "SYNTHETIC_BUOY"

            station_rows = obs_df[obs_df["float_id"] == station_id].sort_values("depth_m")
            for _, r in station_rows.iterrows():
                profiles.append(
                    ArgoProfilePoint(
                        depth=round(float(r["depth_m"]), 1),
                        temperature=round(float(r["obs_temp_c"]), 2),
                        salinity=round(float(r["obs_salinity_psu"]), 2)
                    )
                )
        except Exception:
            pass

        region_str = str(nearest_row.get("region", f"Arabian Sea ({resolved_lat:.2f}°N, {resolved_lon:.2f}°E)"))

        provenance = ProvenanceInfo(
            dataset_type="synthetic",
            source="Dataset 02 Ocean Model Grid & Dataset 06 Waves (Synthetic Demo)",
            dataset_id="02_ocean_model_grid",
            timestamp=resolved_time,
            depth_m=closest_depth,
            region=region_str
        )

        return LocationPropertiesResponse(
            available=True,
            reason=None,
            requestedLat=round(lat, 4),
            requestedLon=round(lon, 4),
            resolvedLat=round(resolved_lat, 4),
            resolvedLon=round(resolved_lon, 4),
            distanceKm=round(min_dist_km, 1),
            requestedDepth=depth,
            resolvedDepth=closest_depth,
            requestedTime=time or "latest",
            resolvedTime=resolved_time,
            timeGapHours=0.0,
            interpolated=False,
            regionName=region_str,
            temperatureC=round(temp_c, 2) if temp_c is not None else None,
            salinityPsu=round(sal_psu, 2) if sal_psu is not None else None,
            uMs=round(u_val, 3) if u_val is not None else None,
            vMs=round(v_val, 3) if v_val is not None else None,
            currentSpeedMps=round(speed_val, 3) if speed_val is not None else None,
            significantWaveHeightM=wave_h,
            peakWavePeriodS=wave_p,
            meanWaveDirectionDeg=wave_dir,
            waveDirectionConvention="FROM_DIRECTION (0=North, 90=East, 180=South, 270=West)",
            zScore=z_score,
            anomalyStatus=anomaly_status,
            rawModelTemp=raw_temp,
            predictedBiasTemp=pred_bias,
            correctedModelTemp=corr_temp,
            profileData=profiles,
            nearestStationId=station_id,
            nearestStationDistanceKm=station_dist,
            platformType=plat_type,
            reliability="HIGH",
            provenance=provenance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Location properties query error: {str(e)}")
