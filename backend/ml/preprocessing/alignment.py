"""
backend/ml/preprocessing/alignment.py
Model-vs-Observation Spatiotemporal Alignment Pipeline.
Matches in-situ observation profiles (Argo, Glider, CTD, Mooring, etc.) with multidimensional numerical model fields.
Preserves spatial distance (km), temporal offset (hours), and depth offset (m).
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime

from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT,
    normalize_dataset_schema
)
from backend.ml.schemas import ObservationRecord, AlignedPoint


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in kilometers between two lat/lon pairs."""
    R = 6371.0  # Earth radius km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(R * c)


class ModelObservationAligner:
    """
    Aligns observation profiles with numerical model outputs.
    Supports 'nearest' grid lookup and 'interp' (trilinear) interpolation.
    Sensor-agnostic across Argo, Glider, CTD, Moorings, ADCP, BGC.
    """

    def __init__(self, method: str = "nearest"):
        """
        Args:
            method: 'nearest' or 'interp'
        """
        if method not in ("nearest", "interp"):
            raise ValueError("Method must be 'nearest' or 'interp'")
        self.method = method

    def align_observations(
        self,
        model_ds: xr.Dataset,
        observations: List[ObservationRecord],
        target_variable: str = "temperature",
        sensor_types: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Pairs observation records with model grid predictions.

        Args:
            model_ds: xarray Dataset containing numerical model output.
            observations: List of ObservationRecord instances.
            target_variable: 'temperature' or 'salinity'.
            sensor_types: Optional filter list for sensor types (e.g. ['argo'], ['glider']).

        Returns:
            pd.DataFrame with aligned rows containing obs and model attributes + offsets.
        """
        model_ds = normalize_dataset_schema(model_ds)
        aligned_rows = []

        target_obs_col = f"obs_{target_variable}"
        target_mod_col = f"model_{target_variable}"

        for obs in observations:
            # Filter by sensor type if specified
            if sensor_types and obs.instrument_type.lower() not in [s.lower() for s in sensor_types]:
                continue

            obs_time = np.datetime64(obs.time)

            for p in obs.profiles:
                # Target availability check
                val_to_check = p.temperature if target_variable == "temperature" else p.salinity
                if val_to_check is None:
                    continue  # Do not silently interpolate or extrapolate missing observation values

                if self.method == "nearest":
                    # Nearest index matching
                    nearest_ds = model_ds.sel(
                        {
                            COORD_TIME: obs_time,
                            COORD_LATITUDE: obs.latitude,
                            COORD_LONGITUDE: obs.longitude,
                            COORD_DEPTH: p.depth,
                        },
                        method="nearest"
                    )

                    matched_time = pd.to_datetime(nearest_ds[COORD_TIME].values)
                    matched_lat = float(nearest_ds[COORD_LATITUDE].values)
                    matched_lon = float(nearest_ds[COORD_LONGITUDE].values)
                    matched_depth = float(nearest_ds[COORD_DEPTH].values)

                    model_temp = float(nearest_ds[VAR_TEMPERATURE].values) if VAR_TEMPERATURE in nearest_ds else np.nan
                    model_sal = float(nearest_ds[VAR_SALINITY].values) if VAR_SALINITY in nearest_ds else np.nan
                    model_u = float(nearest_ds[VAR_U_CURRENT].values) if VAR_U_CURRENT in nearest_ds else np.nan
                    model_v = float(nearest_ds[VAR_V_CURRENT].values) if VAR_V_CURRENT in nearest_ds else np.nan

                else:  # 'interp'
                    interp_ds = model_ds.interp(
                        {
                            COORD_TIME: obs_time,
                            COORD_LATITUDE: obs.latitude,
                            COORD_LONGITUDE: obs.longitude,
                            COORD_DEPTH: p.depth,
                        },
                        method="linear"
                    )

                    matched_time = obs.time
                    matched_lat = obs.latitude
                    matched_lon = obs.longitude
                    matched_depth = p.depth

                    model_temp = float(interp_ds[VAR_TEMPERATURE].values) if VAR_TEMPERATURE in interp_ds else np.nan
                    model_sal = float(interp_ds[VAR_SALINITY].values) if VAR_SALINITY in interp_ds else np.nan
                    model_u = float(interp_ds[VAR_U_CURRENT].values) if VAR_U_CURRENT in interp_ds else np.nan
                    model_v = float(interp_ds[VAR_V_CURRENT].values) if VAR_V_CURRENT in interp_ds else np.nan

                # Compute offsets
                spatial_dist = haversine_distance_km(obs.latitude, obs.longitude, matched_lat, matched_lon)
                time_delta_h = abs((pd.to_datetime(obs.time) - pd.to_datetime(matched_time)).total_seconds() / 3600.0)
                depth_delta_m = abs(p.depth - matched_depth)

                aligned_rows.append({
                    "obs_platform_id": obs.platform_id,
                    "instrument_type": obs.instrument_type.lower(),
                    "obs_time": obs.time,
                    "obs_lat": obs.latitude,
                    "obs_lon": obs.longitude,
                    "depth": p.depth,
                    "obs_temperature": p.temperature,
                    "obs_salinity": p.salinity,
                    "model_temperature": model_temp,
                    "model_salinity": model_sal,
                    "model_u": model_u,
                    "model_v": model_v,
                    "spatial_distance_km": spatial_dist,
                    "time_delta_hours": time_delta_h,
                    "depth_delta_m": depth_delta_m,
                    "interpolation_method": self.method,
                })

        df = pd.DataFrame(aligned_rows)
        # Drop rows where required observation or model target variable is NaN
        if not df.empty and target_obs_col in df.columns and target_mod_col in df.columns:
            df.dropna(subset=[target_obs_col, target_mod_col], inplace=True)
            df.reset_index(drop=True, inplace=True)

        return df
