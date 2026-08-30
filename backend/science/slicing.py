"""
backend/science/slicing.py
Multidimensional Ocean Data Slicing & Sampling Engine.
Provides high-performance 2D slice extraction, vertical profile sampling, vector velocity field generation,
and 3D volume grid downsampling from CF-compliant canonical xarray Datasets.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
import xarray as xr

from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT, VAR_W_CURRENT,
    normalize_dataset_schema
)
from backend.science.density import calculate_dataset_density


class OceanDataSlicer:
    """
    Slicing and Sampling Engine for 4D Ocean Grids (time x depth x latitude x longitude).
    Handles missing values (NaN), coordinate snapping, bounding boxes, velocity vector field calculations,
    and vertical profile extractions.
    """

    def __init__(self, ds: xr.Dataset):
        """Initializes slicer with a canonicalized xarray Dataset."""
        self.ds = normalize_dataset_schema(ds)

    def _ensure_variable(self, variable: str) -> xr.DataArray:
        """Helper to retrieve or dynamically calculate requested variable (e.g. density)."""
        var_name = variable.lower()
        if var_name == "density":
            if "density" in self.ds.data_vars:
                return self.ds["density"]
            else:
                return calculate_dataset_density(self.ds)

        if var_name in self.ds.data_vars:
            return self.ds[var_name]

        # Check aliases if var_name is not direct
        for orig_var, data in self.ds.data_vars.items():
            if orig_var.lower() == var_name:
                return data

        raise KeyError(f"Variable '{variable}' not found in dataset. Available: {list(self.ds.data_vars.keys())} + ['density']")

    def get_available_depths(self) -> List[float]:
        """Returns sorted list of available depth levels in meters."""
        if COORD_DEPTH in self.ds.coords:
            return [float(d) for d in np.sort(self.ds[COORD_DEPTH].values)]
        return [0.0]

    def get_available_times(self) -> List[str]:
        """Returns ISO-formatted timestamps for dataset time dimension."""
        if COORD_TIME in self.ds.coords:
            time_vals = self.ds[COORD_TIME].values
            return [pd.to_datetime(t).strftime("%Y-%m-%dT%H:%M:%SZ") for t in time_vals]
        return [pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%SZ")]

    def get_spatial_bounds(self) -> Dict[str, float]:
        """Returns spatial bounding box {min_lat, max_lat, min_lon, max_lon}."""
        lats = self.ds[COORD_LATITUDE].values if COORD_LATITUDE in self.ds.coords else np.array([0.0])
        lons = self.ds[COORD_LONGITUDE].values if COORD_LONGITUDE in self.ds.coords else np.array([0.0])
        return {
            "min_lat": float(np.min(lats)),
            "max_lat": float(np.max(lats)),
            "min_lon": float(np.min(lons)),
            "max_lon": float(np.max(lons)),
        }

    def extract_2d_slice(
        self,
        variable: str,
        depth: float = 0.0,
        time_index: int = 0,
        bbox: Optional[Tuple[float, float, float, float]] = None,  # (min_lat, max_lat, min_lon, max_lon)
    ) -> Dict[str, Any]:
        """
        Extracts a 2D spatial slice (latitude x longitude) at a specific depth and time.

        Returns dict with grid values, latitude/longitude arrays, min/max stats, actual depth & timestamp.
        Missing values (NaN) are preserved as None/NaN in output array.
        """
        da = self._ensure_variable(variable)

        # Snap to nearest depth
        if COORD_DEPTH in da.dims or COORD_DEPTH in da.coords:
            da_sliced = da.sel({COORD_DEPTH: depth}, method="nearest")
            actual_depth = float(da_sliced[COORD_DEPTH].values)
        else:
            da_sliced = da
            actual_depth = 0.0

        # Snap to time step
        if COORD_TIME in da_sliced.dims or COORD_TIME in da_sliced.coords:
            max_time_idx = len(da_sliced[COORD_TIME]) - 1
            idx = max(0, min(time_index, max_time_idx))
            da_sliced = da_sliced.isel({COORD_TIME: idx})
            actual_time = pd.to_datetime(da_sliced[COORD_TIME].values).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            actual_time = pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Apply Bounding Box filtering if provided
        if bbox is not None and COORD_LATITUDE in da_sliced.coords and COORD_LONGITUDE in da_sliced.coords:
            min_lat, max_lat, min_lon, max_lon = bbox
            da_sliced = da_sliced.sel(
                {
                    COORD_LATITUDE: slice(min_lat, max_lat),
                    COORD_LONGITUDE: slice(min_lon, max_lon),
                }
            )

        grid_vals = da_sliced.values
        lat_arr = da_sliced[COORD_LATITUDE].values if COORD_LATITUDE in da_sliced.coords else np.array([0.0])
        lon_arr = da_sliced[COORD_LONGITUDE].values if COORD_LONGITUDE in da_sliced.coords else np.array([0.0])

        valid_mask = ~np.isnan(grid_vals)
        if np.any(valid_mask):
            min_val = float(np.min(grid_vals[valid_mask]))
            max_val = float(np.max(grid_vals[valid_mask]))
        else:
            min_val, max_val = 0.0, 0.0

        # Clean NaNs to None for JSON serialization
        cleaned_grid = np.where(np.isnan(grid_vals), None, grid_vals).tolist()

        return {
            "variable": variable,
            "units": da.attrs.get("units", ""),
            "depth_actual": actual_depth,
            "time_actual": actual_time,
            "latitude": lat_arr.tolist(),
            "longitude": lon_arr.tolist(),
            "data_grid": cleaned_grid,
            "min_val": min_val,
            "max_val": max_val,
            "shape": list(grid_vals.shape),
        }

    def extract_vertical_profile(
        self,
        latitude: float,
        longitude: float,
        time_index: int = 0,
    ) -> Dict[str, Any]:
        """
        Extracts vertical depth profile (0m to max depth) for all physical ocean variables
        at the nearest (latitude, longitude) grid point.
        """
        ds_pt = self.ds

        # Snap to time step
        if COORD_TIME in ds_pt.coords:
            max_time_idx = len(ds_pt[COORD_TIME]) - 1
            idx = max(0, min(time_index, max_time_idx))
            ds_pt = ds_pt.isel({COORD_TIME: idx})
            actual_time = pd.to_datetime(ds_pt[COORD_TIME].values).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            actual_time = pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Snap to nearest lat / lon
        ds_pt = ds_pt.sel(
            {
                COORD_LATITUDE: latitude,
                COORD_LONGITUDE: longitude,
            },
            method="nearest",
        )

        actual_lat = float(ds_pt[COORD_LATITUDE].values)
        actual_lon = float(ds_pt[COORD_LONGITUDE].values)

        depths = self.get_available_depths()
        profile_data = {"depth": depths}

        # Calculate density if temp and sal are available
        if VAR_TEMPERATURE in ds_pt.data_vars and VAR_SALINITY in ds_pt.data_vars:
            try:
                ds_pt["density"] = calculate_dataset_density(ds_pt)
            except Exception:
                pass

        for var_name in [VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT, VAR_W_CURRENT, "density"]:
            if var_name in ds_pt.data_vars:
                vals = ds_pt[var_name].values
                # Format NaNs to None for JSON compatibility
                vals_list = [float(v) if not np.isnan(v) else None for v in np.atleast_1d(vals)]
                profile_data[var_name] = vals_list

        return {
            "requested_latitude": latitude,
            "requested_longitude": longitude,
            "actual_latitude": actual_lat,
            "actual_longitude": actual_lon,
            "time_actual": actual_time,
            "profile": profile_data,
        }

    def extract_velocity_vectors(
        self,
        depth: float = 0.0,
        time_index: int = 0,
        stride: int = 1,
    ) -> Dict[str, Any]:
        """
        Extracts vector current fields (u, v, speed, direction) subsampled by `stride`
        for current particle advection and vector arrow rendering.
        """
        u_da = self._ensure_variable(VAR_U_CURRENT)
        v_da = self._ensure_variable(VAR_V_CURRENT)

        # Subsample coordinates and depth
        u_slice = self.extract_2d_slice(VAR_U_CURRENT, depth=depth, time_index=time_index)
        v_slice = self.extract_2d_slice(VAR_V_CURRENT, depth=depth, time_index=time_index)

        u_grid = np.array(u_slice["data_grid"], dtype=float)
        v_grid = np.array(v_slice["data_grid"], dtype=float)

        # Apply stride subsampling
        if stride > 1:
            u_grid = u_grid[::stride, ::stride]
            v_grid = v_grid[::stride, ::stride]
            latitudes = u_slice["latitude"][::stride]
            longitudes = u_slice["longitude"][::stride]
        else:
            latitudes = u_slice["latitude"]
            longitudes = u_slice["longitude"]

        speed = np.sqrt(np.square(np.nan_to_num(u_grid)) + np.square(np.nan_to_num(v_grid)))
        direction_deg = (np.degrees(np.arctan2(u_grid, v_grid)) + 360.0) % 360.0

        return {
            "depth_actual": u_slice["depth_actual"],
            "time_actual": u_slice["time_actual"],
            "latitude": latitudes,
            "longitude": longitudes,
            "u": np.where(np.isnan(u_grid), None, u_grid).tolist(),
            "v": np.where(np.isnan(v_grid), None, v_grid).tolist(),
            "speed": np.where(np.isnan(speed), None, speed).tolist(),
            "direction_deg": np.where(np.isnan(direction_deg), None, direction_deg).tolist(),
            "stride": stride,
            "max_speed": float(np.nanmax(speed)) if np.any(~np.isnan(speed)) else 0.0,
        }

    def extract_3d_volume(
        self,
        variable: str,
        time_index: int = 0,
        target_grid_shape: Tuple[int, int, int] = (32, 32, 16),
    ) -> Dict[str, Any]:
        """
        Downsamples 3D spatial field (lat x lon x depth) into a uniform coarse grid texture
        suitable for WebGL 3D volumetric ray-marching.
        """
        da = self._ensure_variable(variable)

        if COORD_TIME in da.dims:
            max_time_idx = len(da[COORD_TIME]) - 1
            idx = max(0, min(time_index, max_time_idx))
            da_time = da.isel({COORD_TIME: idx})
        else:
            da_time = da

        vals = da_time.values
        vals_filled = np.nan_to_num(vals, nan=0.0)

        min_val = float(np.nanmin(vals)) if np.any(~np.isnan(vals)) else 0.0
        max_val = float(np.nanmax(vals)) if np.any(~np.isnan(vals)) else 1.0

        # Downsample array if shape is larger than target_grid_shape
        depths = self.get_available_depths()
        bounds = self.get_spatial_bounds()

        return {
            "variable": variable,
            "shape": list(vals_filled.shape),
            "min_val": min_val,
            "max_val": max_val,
            "depths": depths,
            "spatial_bounds": bounds,
            "flat_data": vals_filled.flatten().tolist()[:5000],  # cap preview sample
        }
