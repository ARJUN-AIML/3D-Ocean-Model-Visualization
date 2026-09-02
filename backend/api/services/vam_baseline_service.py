"""
backend/api/services/vam_baseline_service.py
Service for querying historical 5-year climatological baseline statistics (mean and variance)
from INCOIS Monthly Gridded Argo VAM NetCDF dataset.
"""

import os
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
import xarray as xr
import numpy as np

from backend.api.config import settings

logger = logging.getLogger(__name__)

VAM_VAR_MAP = {
    "temperature": "TEMP",
    "temp": "TEMP",
    "TEMP": "TEMP",
    "salinity": "SAL",
    "sal": "SAL",
    "SAL": "SAL",
}

UNITS_MAP = {
    "TEMP": "degC",
    "SAL": "PSU",
}


class VAMBaselineService:
    def __init__(self, vam_path: Optional[str] = None):
        self.vam_path = vam_path or settings.ARGO_VAM_DATA_PATH
        self._dataset: Optional[xr.Dataset] = None

    def _open_dataset(self) -> xr.Dataset:
        """Open VAM dataset with physical bounds mask applied."""
        if self._dataset is None:
            if not os.path.exists(self.vam_path):
                raise FileNotFoundError(f"VAM Baseline dataset not found at: {self.vam_path}")
            
            ds = xr.open_dataset(self.vam_path)

            # Apply physical masking for unmasked sentinels
            temp_clean = ds['TEMP'].where((ds['TEMP'] >= -2.5) & (ds['TEMP'] <= 40.0))
            sal_clean = ds['SAL'].where((ds['SAL'] >= 2.0) & (ds['SAL'] <= 41.0))

            ds_clean = ds.assign(TEMP=temp_clean, SAL=sal_clean)
            self._dataset = ds_clean
        return self._dataset

    def close(self):
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def get_summary(self) -> Dict[str, Any]:
        """Return dataset summary and baseline metadata."""
        ds = self._open_dataset()
        file_size_mb = os.path.getsize(self.vam_path) / (1024 * 1024)

        time_vals = ds['time'].values
        depth_vals = ds['ZAX'].values
        lat_vals = ds['latitude'].values
        lon_vals = ds['longitude'].values

        return {
            "dataset_id": os.path.basename(self.vam_path),
            "source": "INCOIS Monthly Gridded Argo VAM",
            "file_size_mb": round(file_size_mb, 2),
            "timesteps_count": len(time_vals),
            "time_start": str(np.datetime_as_string(time_vals[0], unit='s')) + "Z",
            "time_end": str(np.datetime_as_string(time_vals[-1], unit='s')) + "Z",
            "depth_levels": [float(d) for d in depth_vals],
            "lat_min": float(lat_vals.min()),
            "lat_max": float(lat_vals.max()),
            "lon_min": float(lon_vals.min()),
            "lon_max": float(lon_vals.max()),
            "grid_resolution_deg": 1.0,
        }

    def resolve_var_name(self, query_var: str) -> str:
        mapped = VAM_VAR_MAP.get(query_var.strip())
        if not mapped:
            mapped = VAM_VAR_MAP.get(query_var.strip().lower())
        if not mapped:
            raise ValueError(f"Unknown VAM variable '{query_var}'. Valid options: ['temperature', 'salinity', 'TEMP', 'SAL']")
        return mapped

    def get_baseline_point(
        self,
        variable: str,
        month: int,
        latitude: float,
        longitude: float,
        depth: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Query 5-year monthly climatological baseline mean and standard deviation
        for a specific month (1-12), latitude, longitude, and depth.
        """
        if month < 1 or month > 12:
            raise ValueError(f"Month must be between 1 and 12, got {month}.")

        ds = self._open_dataset()
        raw_var = self.resolve_var_name(variable)
        da = ds[raw_var]

        # Filter timesteps matching the requested month (1-12)
        month_mask = (ds['time'].dt.month == month)
        da_month = da.sel(time=month_mask)

        # Select nearest spatial grid cell and depth
        sliced = da_month.sel(latitude=latitude, longitude=longitude, ZAX=depth, method="nearest")

        vals = sliced.values
        valid_vals = vals[~np.isnan(vals)]

        if len(valid_vals) == 0:
            mean_val = None
            std_val = None
        else:
            mean_val = float(np.mean(valid_vals))
            std_val = float(np.std(valid_vals, ddof=1)) if len(valid_vals) > 1 else 0.0

        act_lat = float(sliced.latitude.values)
        act_lon = float(sliced.longitude.values)
        act_depth = float(sliced.ZAX.values)
        matched_time = str(np.datetime_as_string(sliced.time.values[0], unit='s')) + "Z"

        return {
            "source": "INCOIS Monthly Gridded Argo VAM",
            "variable": raw_var,
            "units": UNITS_MAP.get(raw_var, "Not specified"),
            "month": month,
            "matched_time": matched_time,
            "requested_latitude": latitude,
            "actual_latitude": act_lat,
            "requested_longitude": longitude,
            "actual_longitude": act_lon,
            "requested_depth": depth,
            "actual_depth": act_depth,
            "baseline_mean": mean_val,
            "baseline_std": std_val,
        }

    def get_baseline_profile(
        self,
        variable: str,
        month: int,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Extract vertical baseline mean and standard deviation profile across 24 depth levels (5m to 2000m).
        """
        if month < 1 or month > 12:
            raise ValueError(f"Month must be between 1 and 12, got {month}.")

        ds = self._open_dataset()
        raw_var = self.resolve_var_name(variable)
        da = ds[raw_var]

        month_mask = (ds['time'].dt.month == month)
        da_month = da.sel(time=month_mask)

        sliced = da_month.sel(latitude=latitude, longitude=longitude, method="nearest")

        depths_arr = sliced.ZAX.values
        means = []
        stds = []

        for d_idx in range(len(depths_arr)):
            vals = sliced.isel(ZAX=d_idx).values
            valid = vals[~np.isnan(vals)]
            if len(valid) == 0:
                means.append(None)
                stds.append(None)
            else:
                means.append(float(np.mean(valid)))
                stds.append(float(np.std(valid, ddof=1)) if len(valid) > 1 else 0.0)

        act_lat = float(sliced.latitude.values)
        act_lon = float(sliced.longitude.values)
        matched_time = str(np.datetime_as_string(sliced.time.values[0], unit='s')) + "Z"

        return {
            "source": "INCOIS Monthly Gridded Argo VAM",
            "variable": raw_var,
            "units": UNITS_MAP.get(raw_var, "Not specified"),
            "month": month,
            "matched_time": matched_time,
            "requested_latitude": latitude,
            "actual_latitude": act_lat,
            "requested_longitude": longitude,
            "actual_longitude": act_lon,
            "depths": [float(d) for d in depths_arr],
            "baseline_means": means,
            "baseline_stds": stds,
        }
