"""
backend/api/services/dataset_service.py
Service for Dataset Discovery, Metadata Extraction, and In-Process Dataset Caching.
Reuses backend.science.profiler and backend.science.canonical.
"""

import os
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import xarray as xr
from fastapi import HTTPException

from backend.api.config import settings
from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    normalize_dataset_schema
)
from backend.science.profiler import DatasetProfiler
from backend.api.schemas.datasets import (
    DatasetSummary,
    DatasetDetail,
    CoordinateInfo,
    VariableInfo,
    BoundingBox,
    TimeRange,
    DepthRange,
)


class DatasetCache:
    """
    Thread-safe in-process LRU cache for open xarray Datasets.
    Properly closes xarray datasets when evicted or during application shutdown.
    (Requirements 4 & 5).
    """

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._cache: OrderedDict[str, xr.Dataset] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, dataset_id: str) -> Optional[xr.Dataset]:
        with self._lock:
            if dataset_id in self._cache:
                self._cache.move_to_end(dataset_id)
                return self._cache[dataset_id]
            return None

    def put(self, dataset_id: str, ds: xr.Dataset) -> None:
        with self._lock:
            if dataset_id in self._cache:
                self._cache.move_to_end(dataset_id)
                self._cache[dataset_id] = ds
                return

            self._cache[dataset_id] = ds
            if len(self._cache) > self.max_size:
                evicted_id, evicted_ds = self._cache.popitem(last=False)
                try:
                    evicted_ds.close()
                except Exception:
                    pass

    def close_all(self) -> None:
        """Closes all cached datasets during application shutdown (Requirement 5)."""
        with self._lock:
            for ds_id, ds in list(self._cache.items()):
                try:
                    ds.close()
                except Exception:
                    pass
            self._cache.clear()


class DatasetService:
    """Service handling dataset discovery, metadata, and safe file loading."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = os.path.abspath(data_dir or settings.DATA_DIR)
        self.cache = DatasetCache(max_size=settings.DATASET_CACHE_MAX_SIZE)
        self.profiler = DatasetProfiler()

    def get_safe_file_path(self, dataset_id: str) -> str:
        """
        Validates dataset_id to prevent path traversal attacks.
        Ensures target file is located strictly within configured data_dir.
        """
        # Resolve target path
        target_path = os.path.abspath(os.path.join(self.data_dir, dataset_id))

        # Check path containment
        if not target_path.startswith(self.data_dir + os.sep) and target_path != self.data_dir:
            raise HTTPException(status_code=400, detail="Invalid dataset_id: path traversal detected.")

        if not os.path.isfile(target_path):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

        return target_path

    def discover_datasets(self) -> List[DatasetSummary]:
        """
        Scans data_dir for valid NetCDF model or observation datasets.
        Returns empty list if directory contains no real datasets (Requirements 2 & 3).
        """
        summaries: List[DatasetSummary] = []
        if not os.path.exists(self.data_dir):
            return summaries

        supported_exts = (".nc", ".nc4", ".netcdf", ".h5")

        for root, _, files in os.walk(self.data_dir):
            for f in sorted(files):
                if f.lower().endswith(supported_exts):
                    full_path = os.path.join(root, f)
                    rel_id = os.path.relpath(full_path, self.data_dir).replace("\\", "/")
                    try:
                        summary = self._extract_dataset_summary(rel_id, full_path)
                        summaries.append(summary)
                    except Exception:
                        continue

        return summaries

    def _extract_dataset_summary(self, dataset_id: str, full_path: str) -> DatasetSummary:
        """Extracts summary metadata for discovery endpoint."""
        ds = xr.open_dataset(full_path, engine="netcdf4" if full_path.endswith((".nc", ".nc4")) else "h5netcdf")
        norm_ds = normalize_dataset_schema(ds)

        available_vars = list(norm_ds.data_vars)
        title = str(ds.attrs.get("title", dataset_id))

        time_range = None
        if COORD_TIME in norm_ds.coords:
            t_vals = norm_ds[COORD_TIME].values
            if len(t_vals) > 0:
                time_range = [
                    pd.to_datetime(t_vals[0]).isoformat(),
                    pd.to_datetime(t_vals[-1]).isoformat(),
                ]

        depth_range = None
        if COORD_DEPTH in norm_ds.coords:
            d_vals = norm_ds[COORD_DEPTH].values
            if len(d_vals) > 0:
                depth_range = [float(np.nanmin(d_vals)), float(np.nanmax(d_vals))]

        lat_range = None
        if COORD_LATITUDE in norm_ds.coords:
            lat_vals = norm_ds[COORD_LATITUDE].values
            if len(lat_vals) > 0:
                lat_range = [float(np.nanmin(lat_vals)), float(np.nanmax(lat_vals))]

        lon_range = None
        if COORD_LONGITUDE in norm_ds.coords:
            lon_vals = norm_ds[COORD_LONGITUDE].values
            if len(lon_vals) > 0:
                lon_range = [float(np.nanmin(lon_vals)), float(np.nanmax(lon_vals))]

        ds.close()

        return DatasetSummary(
            dataset_id=dataset_id,
            display_name=title,
            source_type="model",
            format="NetCDF-4/HDF5",
            available_variables=available_vars,
            time_range=time_range,
            depth_range=depth_range,
            latitude_range=lat_range,
            longitude_range=lon_range,
        )

    def get_dataset_detail(self, dataset_id: str) -> DatasetDetail:
        """
        Uses DatasetProfiler infrastructure to return detailed scientific metadata.
        (Requirement 10).
        """
        full_path = self.get_safe_file_path(dataset_id)
        raw_profile = self.profiler.profile_netcdf_file(full_path)

        # Map profiler output to Pydantic DatasetDetail
        coords = {}
        for cname, cinfo in raw_profile.get("coordinates", {}).items():
            coords[cname] = CoordinateInfo(
                dtype=cinfo.get("dtype", "unknown"),
                range=cinfo.get("range", []),
                units=cinfo.get("units", "unknown"),
                size=cinfo.get("size", 0),
            )

        variables = {}
        for vname, vinfo in raw_profile.get("variables", {}).items():
            variables[vname] = VariableInfo(
                dtype=vinfo.get("dtype", "unknown"),
                range=vinfo.get("range", []),
                units=vinfo.get("units", "unknown"),
                missing_pct=vinfo.get("missing_pct", 0.0),
                chunking=vinfo.get("chunking", "unchunked"),
                compression=vinfo.get("compression", "False"),
            )

        # Extract spatial, temporal, depth coverage
        lat_range = coords.get(COORD_LATITUDE, CoordinateInfo(dtype="", range=[-90, 90], units="", size=0)).range
        lon_range = coords.get(COORD_LONGITUDE, CoordinateInfo(dtype="", range=[-180, 180], units="", size=0)).range
        bbox = BoundingBox(
            latitude_range=[float(lat_range[0]), float(lat_range[1])] if len(lat_range) == 2 and lat_range[0] != "N/A" else [-90.0, 90.0],
            longitude_range=[float(lon_range[0]), float(lon_range[1])] if len(lon_range) == 2 and lon_range[0] != "N/A" else [-180.0, 180.0],
        )

        time_cov = None
        if COORD_TIME in coords and coords[COORD_TIME].size > 0:
            trange = coords[COORD_TIME].range
            if len(trange) == 2 and trange[0] != "N/A":
                time_cov = TimeRange(
                    start_time=str(trange[0]),
                    end_time=str(trange[1]),
                    timesteps_count=coords[COORD_TIME].size,
                )

        depth_cov = None
        if COORD_DEPTH in coords and coords[COORD_DEPTH].size > 0:
            drange = coords[COORD_DEPTH].range
            if len(drange) == 2 and drange[0] != "N/A":
                depth_cov = DepthRange(
                    min_depth=float(drange[0]),
                    max_depth=float(drange[1]),
                    levels_count=coords[COORD_DEPTH].size,
                )

        available_vars = list(variables.keys())

        return DatasetDetail(
            dataset_id=dataset_id,
            display_name=raw_profile.get("cf_attributes", {}).get("title", dataset_id),
            source_type="model",
            format=raw_profile.get("format", "NetCDF-4/HDF5"),
            available_variables=available_vars,
            time_range=[time_cov.start_time, time_cov.end_time] if time_cov else None,
            depth_range=[depth_cov.min_depth, depth_cov.max_depth] if depth_cov else None,
            latitude_range=bbox.latitude_range,
            longitude_range=bbox.longitude_range,
            file_size_mb=raw_profile.get("file_size_mb", 0.0),
            dimensions=raw_profile.get("dimensions", {}),
            coordinates=coords,
            variables=variables,
            spatial_coverage=bbox,
            temporal_coverage=time_cov,
            depth_coverage=depth_cov,
            visualization_capabilities=raw_profile.get("visualization_capabilities", {}),
            scientific_issues=raw_profile.get("scientific_issues", []),
        )

    def get_open_dataset(self, dataset_id: str) -> xr.Dataset:
        """
        Retrieves open xarray Dataset from in-process cache, or opens & caches it.
        Schema is normalized on load using normalize_dataset_schema (Requirement 7 & 10).
        """
        cached_ds = self.cache.get(dataset_id)
        if cached_ds is not None:
            return cached_ds

        full_path = self.get_safe_file_path(dataset_id)
        raw_ds = xr.open_dataset(full_path, engine="netcdf4" if full_path.endswith((".nc", ".nc4")) else "h5netcdf")
        norm_ds = normalize_dataset_schema(raw_ds)

        self.cache.put(dataset_id, norm_ds)
        return norm_ds

    def close_all_cached(self) -> None:
        """Closes all cached xarray datasets."""
        self.cache.close_all()
