"""
backend/api/services/ocean_service.py
Service for 2D Ocean Slice Extraction and Variable Metadata Discovery.
Implements explicit requested vs actual time/depth selection, JSON-safe missing value handling,
geographic subsetting for ascending/descending coordinates, downsampling, and MAX_SLICE_CELLS protection.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import xarray as xr
from fastapi import HTTPException

from backend.api.config import settings
from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VARIABLE_ALIASES
)
from backend.api.services.dataset_service import DatasetService
from backend.api.schemas.ocean import VariableSummary, OceanSliceResponse


class OceanService:
    """Service handling 2D ocean slice extractions and variable queries."""

    def __init__(self, dataset_service: DatasetService):
        self.dataset_service = dataset_service

    def get_available_variables(self, dataset_id: str) -> List[VariableSummary]:
        """
        Lists available variables in dataset with canonical names, units, and ranges.
        """
        ds = self.dataset_service.get_open_dataset(dataset_id)
        vars_summary: List[VariableSummary] = []

        # Invert alias map to find original names if applicable
        reverse_aliases: Dict[str, str] = {}
        for orig, canon in VARIABLE_ALIASES.items():
            if canon not in reverse_aliases:
                reverse_aliases[canon] = orig

        for vname in ds.data_vars:
            var_arr = ds[vname]
            units = str(var_arr.attrs.get("units", "unknown"))
            dims = [str(d) for d in var_arr.dims]

            vals = var_arr.values
            valid_mask = ~np.isnan(vals) if np.issubdtype(vals.dtype, np.number) else ~pd.isna(vals)

            min_val = float(np.min(vals[valid_mask])) if np.any(valid_mask) and np.issubdtype(vals.dtype, np.number) else None
            max_val = float(np.max(vals[valid_mask])) if np.any(valid_mask) and np.issubdtype(vals.dtype, np.number) else None

            orig_name = reverse_aliases.get(str(vname), str(vname))

            vars_summary.append(
                VariableSummary(
                    canonical_name=str(vname),
                    original_name=orig_name,
                    units=units,
                    min_value=min_val,
                    max_value=max_val,
                    dimensions=dims,
                )
            )

        return vars_summary

    def get_ocean_slice(
        self,
        dataset_id: str,
        variable: str,
        time: str,
        depth: float,
        lat_min: Optional[float] = None,
        lat_max: Optional[float] = None,
        lon_min: Optional[float] = None,
        lon_max: Optional[float] = None,
        downsample: Optional[int] = 1,
    ) -> OceanSliceResponse:
        """
        Extracts a 2D depth/time slice payload for visualization.
        """
        ds = self.dataset_service.get_open_dataset(dataset_id)

        # 1. Validate variable existence
        if variable not in ds.data_vars:
            raise HTTPException(status_code=404, detail=f"Variable '{variable}' not found in dataset '{dataset_id}'.")

        var_da = ds[variable]
        units = str(var_da.attrs.get("units", "unknown"))

        # 2. Time Selection (Explicit Nearest Match)
        if COORD_TIME not in ds.coords:
            raise HTTPException(status_code=400, detail=f"Dataset '{dataset_id}' has no time coordinate.")

        try:
            target_time = pd.to_datetime(time)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid ISO8601 time string: '{time}'.")

        time_coords = ds[COORD_TIME].values
        time_series = pd.to_datetime(time_coords)

        # Calculate nearest time index
        time_diffs = np.abs(time_series - target_time)
        nearest_t_idx = int(np.argmin(time_diffs))
        actual_time_val = pd.to_datetime(time_coords[nearest_t_idx]).isoformat()

        # 3. Depth Selection (Explicit Nearest Match)
        if COORD_DEPTH not in ds.coords:
            raise HTTPException(status_code=400, detail=f"Dataset '{dataset_id}' has no depth coordinate.")

        depth_coords = ds[COORD_DEPTH].values
        if len(depth_coords) == 0:
            raise HTTPException(status_code=400, detail="Dataset depth coordinate is empty.")

        depth_diffs = np.abs(depth_coords - depth)
        nearest_d_idx = int(np.argmin(depth_diffs))
        actual_depth_val = float(depth_coords[nearest_d_idx])

        # 4. Extract 2D Slice
        slice_2d = var_da.isel({COORD_TIME: nearest_t_idx, COORD_DEPTH: nearest_d_idx})

        # 5. Geographic Bounding Box Subsetting (Supports Ascending & Descending Latitudes - Requirement 6)
        if COORD_LATITUDE not in slice_2d.coords or COORD_LONGITUDE not in slice_2d.coords:
            raise HTTPException(status_code=400, detail="Dataset missing latitude or longitude coordinates.")

        lats = slice_2d[COORD_LATITUDE].values
        lons = slice_2d[COORD_LONGITUDE].values

        if lat_min is not None and lat_max is not None:
            if lat_min > lat_max:
                raise HTTPException(status_code=400, detail="lat_min must be <= lat_max.")
            lat_mask = (lats >= lat_min) & (lats <= lat_max)
        else:
            lat_mask = np.ones(len(lats), dtype=bool)

        if lon_min is not None and lon_max is not None:
            if lon_min > lon_max:
                raise HTTPException(status_code=400, detail="lon_min must be <= lon_max.")
            lon_mask = (lons >= lon_min) & (lons <= lon_max)
        else:
            lon_mask = np.ones(len(lons), dtype=bool)

        lat_indices = np.where(lat_mask)[0]
        lon_indices = np.where(lon_mask)[0]

        if len(lat_indices) == 0 or len(lon_indices) == 0:
            raise HTTPException(status_code=400, detail="Geographic bounding box subset contains 0 grid points.")

        # 6. Downsampling
        step = downsample if downsample and downsample > 0 else 1
        lat_indices = lat_indices[::step]
        lon_indices = lon_indices[::step]

        # 7. Response Size Protection (Requirements 8 & 9)
        total_cells = len(lat_indices) * len(lon_indices)
        if total_cells > settings.MAX_SLICE_CELLS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Requested slice size ({total_cells} cells: {len(lat_indices)} lat x {len(lon_indices)} lon) "
                    f"exceeds maximum allowed limit of {settings.MAX_SLICE_CELLS} cells. "
                    f"Please specify a smaller bounding box or increase downsample step."
                ),
            )

        selected_slice = slice_2d.isel({COORD_LATITUDE: lat_indices, COORD_LONGITUDE: lon_indices})

        lat_res = [float(val) for val in selected_slice[COORD_LATITUDE].values]
        lon_res = [float(val) for val in selected_slice[COORD_LONGITUDE].values]

        raw_values = selected_slice.values

        # 8. JSON-Safe Missing Value Serialization (NaN / Inf / _FillValue -> None)
        values_2d: List[List[Optional[float]]] = []
        valid_vals: List[float] = []
        missing_count = 0

        fill_val = selected_slice.attrs.get("_FillValue", None)

        for row in raw_values:
            row_list: List[Optional[float]] = []
            for item in row:
                if (
                    item is None
                    or np.isnan(item)
                    or np.isinf(item)
                    or (fill_val is not None and math.isclose(item, fill_val, abs_tol=1e-5))
                ):
                    row_list.append(None)
                    missing_count += 1
                else:
                    val_float = float(item)
                    row_list.append(val_float)
                    valid_vals.append(val_float)
            values_2d.append(row_list)

        valid_min = float(np.min(valid_vals)) if valid_vals else None
        valid_max = float(np.max(valid_vals)) if valid_vals else None

        source_meta = {
            "title": str(ds.attrs.get("title", "")),
            "institution": str(ds.attrs.get("institution", "")),
            "grid_type": str(ds.attrs.get("grid_type", "regular")),
        }

        return OceanSliceResponse(
            dataset_id=dataset_id,
            variable=variable,
            units=units,
            requested_time=time,
            actual_time=actual_time_val,
            requested_depth=float(depth),
            actual_depth=actual_depth_val,
            latitude=lat_res,
            longitude=lon_res,
            values=values_2d,
            valid_min=valid_min,
            valid_max=valid_max,
            missing_value_count=missing_count,
            source_metadata=source_meta,
        )
