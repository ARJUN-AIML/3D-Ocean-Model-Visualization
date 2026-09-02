"""
backend/api/services/hycom_service.py
Service for reading, chunking, caching, and querying INCOIS RSMC HYCOM NetCDF data.
"""

import os
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
import xarray as xr
import numpy as np
from pandas import Timestamp

from backend.api.config import settings

logger = logging.getLogger(__name__)

# Map common requested variable names to raw NetCDF names in HYCOM
HYCOM_VAR_MAP = {
    "temperature": "TEMP",
    "temp": "TEMP",
    "TEMP": "TEMP",
    "salinity": "SALN",
    "saln": "SALN",
    "sal": "SALN",
    "SALN": "SALN",
    "u_velocity": "UVEL",
    "u": "UVEL",
    "uvel": "UVEL",
    "UVEL": "UVEL",
    "v_velocity": "VVEL",
    "v": "VVEL",
    "vvel": "VVEL",
    "VVEL": "VVEL",
    "ssh": "SSH",
    "sea_surface_height": "SSH",
    "SSH": "SSH",
    "mld": "MLD",
    "mixed_layer_depth": "MLD",
    "MLD": "MLD",
    "tchp": "TCHP",
    "tropical_cyclone_heat_potential": "TCHP",
    "TCHP": "TCHP",
}

UNITS_MAP = {
    "TEMP": "degC",
    "SALN": "PSU",
    "UVEL": "m/s",
    "VVEL": "m/s",
    "SSH": "m",
    "MLD": "m",
    "TCHP": "KJ/cm2",
}


class HycomService:
    def __init__(self, hycom_path: Optional[str] = None):
        self.hycom_path = hycom_path or settings.HYCOM_DATA_PATH
        self._dataset: Optional[xr.Dataset] = None

    def _open_dataset(self) -> xr.Dataset:
        """Lazy load HYCOM dataset without loading full 10GB file into RAM."""
        if self._dataset is None:
            if not os.path.exists(self.hycom_path):
                raise FileNotFoundError(f"HYCOM file not found at: {self.hycom_path}")
            # Lazy open with xarray
            self._dataset = xr.open_dataset(self.hycom_path)
        return self._dataset

    def close(self):
        """Close dataset handle if open."""
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def get_summary(self) -> Dict[str, Any]:
        """Return dataset summary and spatial-temporal metadata."""
        ds = self._open_dataset()
        file_size_mb = os.path.getsize(self.hycom_path) / (1024 * 1024)

        time_vals = ds["TIME"].values
        depth_vals = ds["DEPTH"].values if "DEPTH" in ds.coords else []
        lat_vals = ds["LAT"].values
        lon_vals = ds["LON"].values

        var_list = []
        for v in ["TEMP", "SALN", "UVEL", "VVEL", "SSH", "MLD", "TCHP"]:
            if v in ds.data_vars:
                var_obj = ds[v]
                var_list.append({
                    "name": v,
                    "long_name": str(var_obj.attrs.get("long_name", v)),
                    "units": UNITS_MAP.get(v, str(var_obj.attrs.get("units", "Not specified"))),
                    "dimensions": [str(d) for d in var_obj.dims],
                    "shape": list(var_obj.shape),
                })

        return {
            "dataset_id": os.path.basename(self.hycom_path),
            "source": "INCOIS RSMC HYCOM",
            "file_size_mb": round(file_size_mb, 2),
            "timesteps_count": len(time_vals),
            "time_start": Timestamp(time_vals[0]).isoformat() + "Z",
            "time_end": Timestamp(time_vals[-1]).isoformat() + "Z",
            "depth_levels": [float(d) for d in depth_vals],
            "lat_min": float(lat_vals.min()),
            "lat_max": float(lat_vals.max()),
            "lon_min": float(lon_vals.min()),
            "lon_max": float(lon_vals.max()),
            "variables": var_list,
        }

    def resolve_var_name(self, query_var: str) -> str:
        """Resolve requested variable string to raw HYCOM variable name."""
        mapped = HYCOM_VAR_MAP.get(query_var.strip())
        if not mapped:
            mapped = HYCOM_VAR_MAP.get(query_var.strip().lower())
        if not mapped:
            raise ValueError(f"Unknown HYCOM variable '{query_var}'. Valid options: {list(HYCOM_VAR_MAP.keys())}")
        return mapped

    def get_point(
        self,
        variable: str,
        time: str,
        latitude: float,
        longitude: float,
        depth: float = 0.0,
    ) -> Dict[str, Any]:
        """Extract point query value for a specific variable at nearest time, lat, lon, and depth."""
        ds = self._open_dataset()
        raw_var = self.resolve_var_name(variable)

        if raw_var not in ds.data_vars:
            raise KeyError(f"Variable '{raw_var}' not present in HYCOM file.")

        da = ds[raw_var]

        # Select nearest time
        try:
            target_time = np.datetime64(pd_timestamp(time).tz_convert(None))
        except Exception:
            target_time = np.datetime64(time)

        sel_dict = {
            "TIME": target_time,
            "LAT": latitude,
            "LON": longitude,
        }
        if "DEPTH" in da.dims:
            sel_dict["DEPTH"] = depth

        sliced = da.sel(**sel_dict, method="nearest")

        val = sliced.values.item()
        # Handle _FillValue / NaN
        fill_val = da.encoding.get("_FillValue", da.attrs.get("_FillValue", None))
        if val is None or np.isnan(val) or (fill_val is not None and math.isclose(val, fill_val, rel_tol=1e-5)) or abs(val) > 1e20:
            clean_val = None
        else:
            clean_val = float(val)

        act_time = Timestamp(sliced.TIME.values).isoformat() + "Z"
        act_lat = float(sliced.LAT.values)
        act_lon = float(sliced.LON.values)
        act_depth = float(sliced.DEPTH.values) if "DEPTH" in sliced.coords else 0.0

        return {
            "source": "INCOIS RSMC HYCOM",
            "variable": raw_var,
            "units": UNITS_MAP.get(raw_var, str(da.attrs.get("units", "Not specified"))),
            "requested_time": time,
            "actual_time": act_time,
            "requested_latitude": latitude,
            "actual_latitude": act_lat,
            "requested_longitude": longitude,
            "actual_longitude": act_lon,
            "requested_depth": depth,
            "actual_depth": act_depth,
            "value": clean_val,
        }

    def get_profile(
        self,
        variable: str,
        time: str,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """Extract vertical profile across depth levels at nearest time, lat, and lon."""
        ds = self._open_dataset()
        raw_var = self.resolve_var_name(variable)

        if raw_var not in ds.data_vars:
            raise KeyError(f"Variable '{raw_var}' not present in HYCOM file.")

        da = ds[raw_var]

        try:
            target_time = np.datetime64(pd_timestamp(time).tz_convert(None))
        except Exception:
            target_time = np.datetime64(time)

        if "DEPTH" not in da.dims:
            # 2D variable (e.g. SSH, MLD, TCHP) - return surface value at depth 0
            point_res = self.get_point(variable, time, latitude, longitude, depth=0.0)
            return {
                "source": "INCOIS RSMC HYCOM",
                "variable": raw_var,
                "units": point_res["units"],
                "requested_time": time,
                "actual_time": point_res["actual_time"],
                "requested_latitude": latitude,
                "actual_latitude": point_res["actual_latitude"],
                "requested_longitude": longitude,
                "actual_longitude": point_res["actual_longitude"],
                "depths": [0.0],
                "values": [point_res["value"]],
            }

        sliced = da.sel(TIME=target_time, LAT=latitude, LON=longitude, method="nearest")

        depth_array = sliced.DEPTH.values
        val_array = sliced.values

        fill_val = da.encoding.get("_FillValue", da.attrs.get("_FillValue", None))

        clean_depths = [float(d) for d in depth_array]
        clean_values = []
        for v in val_array:
            if v is None or np.isnan(v) or (fill_val is not None and math.isclose(v, fill_val, rel_tol=1e-5)) or abs(v) > 1e20:
                clean_values.append(None)
            else:
                clean_values.append(float(v))

        act_time = Timestamp(sliced.TIME.values).isoformat() + "Z"
        act_lat = float(sliced.LAT.values)
        act_lon = float(sliced.LON.values)

        return {
            "source": "INCOIS RSMC HYCOM",
            "variable": raw_var,
            "units": UNITS_MAP.get(raw_var, str(da.attrs.get("units", "Not specified"))),
            "requested_time": time,
            "actual_time": act_time,
            "requested_latitude": latitude,
            "actual_latitude": act_lat,
            "requested_longitude": longitude,
            "actual_longitude": act_lon,
            "depths": clean_depths,
            "values": clean_values,
        }


def pd_timestamp(time_str: str) -> Timestamp:
    from pandas import to_datetime
    return to_datetime(time_str, utc=True)
