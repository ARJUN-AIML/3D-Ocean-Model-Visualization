"""
backend/science/dataset_manager.py
Configurable Ocean Dataset Manager & Scientific Provenance Tracker.
Supports dynamic loading of NetCDF and Zarr datasets from data/raw, data/processed, and data/demo.
Preserves scientific metadata, quality flags, and enforces clear separation between REAL and SYNTHETIC data.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import xarray as xr
import pandas as pd

from backend.science.canonical import normalize_dataset_schema
from backend.science.slicing import OceanDataSlicer
from backend.science.sample_generator import generate_indian_ocean_demo_dataset, DEMO_DATA_STATUS


class OceanDatasetManager:
    """
    Central Manager for Ocean Model & Observation Datasets.
    Configurable paths:
      - data/raw/       (Raw real ocean NetCDF/Argo datasets)
      - data/processed/ (Validated, processed real datasets)
      - data/demo/      (Separated demo/synthetic datasets for offline dev)
    """

    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.raw_dir = self.data_root / "raw"
        self.processed_dir = self.data_root / "processed"
        self.demo_dir = self.data_root / "demo"

        # Ensure directory structures exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.demo_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, xr.Dataset] = {}
        self._slicers: Dict[str, OceanDataSlicer] = {}
        self.active_dataset_id: Optional[str] = None

    def list_datasets(self) -> List[Dict[str, Any]]:
        """Scans data/raw, data/processed, data/demo and returns list of available dataset manifests."""
        datasets = []
        search_dirs = [
            (self.raw_dir, "REAL"),
            (self.processed_dir, "REAL"),
            (self.demo_dir, DEMO_DATA_STATUS),
        ]

        for folder, default_status in search_dirs:
            if not folder.exists():
                continue
            for file_path in folder.glob("*.*"):
                if file_path.suffix.lower() in [".nc", ".nc4", ".zarr", ".cdf"]:
                    ds_id = file_path.stem
                    is_synthetic = "demo" in folder.name.lower() or "synthetic" in ds_id.lower()
                    data_status = DEMO_DATA_STATUS if is_synthetic else default_status

                    datasets.append({
                        "dataset_id": ds_id,
                        "file_path": str(file_path),
                        "folder": folder.name,
                        "data_status": data_status,
                        "is_synthetic": is_synthetic,
                        "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                    })
        return datasets

    def get_or_create_default_dataset(self) -> Tuple[xr.Dataset, str]:
        """
        Loads the active dataset. If no dataset exists in data/, automatically
        generates the Indian Ocean demo dataset in data/demo/indian_ocean_demo.nc.
        """
        manifest = self.list_datasets()
        if not manifest:
            demo_path = str(self.demo_dir / "indian_ocean_demo.nc")
            generate_indian_ocean_demo_dataset(output_path=demo_path)
            ds_id = "indian_ocean_demo"
        else:
            ds_id = manifest[0]["dataset_id"]

        ds = self.load_dataset(ds_id)
        return ds, ds_id

    def load_dataset(self, dataset_id: str) -> xr.Dataset:
        """
        Loads dataset by dataset_id, normalizes schema, and caches slicer.
        """
        if dataset_id in self._cache:
            self.active_dataset_id = dataset_id
            return self._cache[dataset_id]

        # Locate file
        file_path = None
        for folder in [self.raw_dir, self.processed_dir, self.demo_dir]:
            for ext in [".nc", ".nc4", ".zarr", ".cdf"]:
                candidate = folder / f"{dataset_id}{ext}"
                if candidate.exists():
                    file_path = candidate
                    break
            if file_path:
                break

        if file_path is None:
            # Fallback to demo dataset if dataset_id matches demo
            if "demo" in dataset_id.lower():
                demo_path = str(self.demo_dir / "indian_ocean_demo.nc")
                ds = generate_indian_ocean_demo_dataset(output_path=demo_path)
                file_path = Path(demo_path)
            else:
                raise FileNotFoundError(f"Dataset '{dataset_id}' not found in raw, processed, or demo directories.")

        # Load Xarray dataset
        if file_path.suffix.lower() == ".zarr":
            ds = xr.open_zarr(str(file_path))
        else:
            ds = xr.open_dataset(str(file_path))

        ds_norm = normalize_dataset_schema(ds)
        self._cache[dataset_id] = ds_norm
        self._slicers[dataset_id] = OceanDataSlicer(ds_norm)
        self.active_dataset_id = dataset_id
        return ds_norm

    def get_slicer(self, dataset_id: Optional[str] = None) -> OceanDataSlicer:
        """Gets OceanDataSlicer instance for active or specified dataset."""
        target_id = dataset_id or self.active_dataset_id
        if not target_id or target_id not in self._slicers:
            ds, target_id = self.get_or_create_default_dataset()
        return self._slicers[target_id]

    def get_provenance_metadata(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts full scientific provenance metadata for a dataset per section 8 of architecture spec.
        Includes dataset_id, source, data_status, variables, time/depth/spatial bounds, and quality flags.
        """
        target_id = dataset_id or self.active_dataset_id
        if not target_id or target_id not in self._cache:
            self.load_dataset(target_id or "indian_ocean_demo")
            target_id = self.active_dataset_id

        ds = self._cache[target_id]
        slicer = self._slicers[target_id]

        attrs = ds.attrs
        is_synthetic = attrs.get("is_synthetic", "false").lower() == "true" or "demo" in target_id.lower()
        data_status = attrs.get("data_status", DEMO_DATA_STATUS if is_synthetic else "REAL")

        variables_info = {}
        for var_name, da in ds.data_vars.items():
            variables_info[var_name] = {
                "units": da.attrs.get("units", "unknown"),
                "standard_name": da.attrs.get("standard_name", var_name),
                "long_name": da.attrs.get("long_name", var_name),
            }

        times = slicer.get_available_times()
        depths = slicer.get_available_depths()
        spatial = slicer.get_spatial_bounds()

        return {
            "dataset_id": target_id,
            "title": attrs.get("title", f"Ocean Dataset - {target_id}"),
            "institution": attrs.get("institution", "INCOIS / BluePulse Ocean Digital Twin"),
            "source": attrs.get("source", "Numerical Ocean Model"),
            "data_status": data_status,
            "is_synthetic": is_synthetic,
            "quality_flag": attrs.get("quality_flag", "QC_PASSED"),
            "processing_version": attrs.get("processing_version", "v2.0"),
            "model_version": attrs.get("model_version", "ROMS/HYCOM-INCOIS-v1"),
            "variables": variables_info,
            "time_range": {
                "start": times[0] if times else None,
                "end": times[-1] if times else None,
                "count": len(times),
            },
            "depth_range": {
                "min_depth": depths[0] if depths else 0.0,
                "max_depth": depths[-1] if depths else 0.0,
                "levels": len(depths),
            },
            "spatial_extent": spatial,
        }
