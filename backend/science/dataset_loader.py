"""
backend/science/dataset_loader.py
Robust loader and data manager for OceanTwin synthetic/demo datasets.

Rules:
- Respect file extensions vs actual content. If a .csv file contains Excel binary content (PK\\x03\\x04),
  log the mismatch explicitly and read via pandas.read_excel().
- Cache loaded dataframes in memory for fast API responses.
- Provide canonical dataset access for ML bias training, dataset slicing, observations,
  climatology anomalies, current trajectories, and wave data.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("oceantwin.dataset_loader")
logging.basicConfig(level=logging.INFO)

# Root directory of the repository
REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = REPO_ROOT / "datasets"

_CACHE: Dict[str, pd.DataFrame] = {}

DATASET_FILE_MAP = {
    "01_matched_model_argo": ["01_matched_model_argo_training-2.csv", "01_matched_model_argo_training.csv"],
    "02_ocean_model_grid": ["02_ocean_model_grid_samples.csv"],
    "03_argo_observations": ["03_argo_observations-1.xlsx", "03_argo_observations.csv"],
    "04_climatology_baseline": ["04_climatology_baseline-1.csv", "04_climatology_baseline.csv"],
    "05_current_vectors": ["05_current_vectors_trajectory.csv"],
    "06_wave_samples": ["06_wave_samples.csv"]
}


def _resolve_file_path(candidates: list) -> Path:
    for candidate in candidates:
        p = DATASETS_DIR / candidate
        if p.exists():
            return p
    raise FileNotFoundError(f"None of dataset candidate files exist in {DATASETS_DIR}: {candidates}")


def load_dataset_file(key: str) -> pd.DataFrame:
    """Loads dataset by key with file extension vs content mismatch detection."""
    if key in _CACHE:
        return _CACHE[key]

    candidates = DATASET_FILE_MAP.get(key, [])
    path = _resolve_file_path(candidates)

    # Check header bytes for PK\x03\x04 (Excel/ZIP header)
    with open(path, 'rb') as f:
        header = f.read(4)

    is_excel_binary = header.startswith(b'PK\x03\x04')
    suffix = path.suffix.lower()

    if suffix == '.csv' and is_excel_binary:
        logger.warning(
            f"[DATASET LOADER MISMATCH DETECTED] File '{path.name}' has extension '.csv' "
            f"but contains binary XLSX format. Loading with pandas.read_excel()."
        )
        df = pd.read_excel(path)
    elif suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, encoding='utf-8', encoding_errors='replace')

    _CACHE[key] = df
    logger.info(f"Loaded dataset '{key}' from '{path.name}' with shape {df.shape}")
    return df


def get_matched_training_data() -> pd.DataFrame:
    """Dataset 01: Matched Model-Argo paired data for ML training and validation."""
    return load_dataset_file("01_matched_model_argo")


def get_ocean_grid_data() -> pd.DataFrame:
    """Dataset 02: 3D Ocean Model Grid Samples (Temp, Sal, Currents, SSH, Chlorophyll)."""
    return load_dataset_file("02_ocean_model_grid")


def get_argo_observations_data() -> pd.DataFrame:
    """Dataset 03: Argo Observations CTD profiles."""
    return load_dataset_file("03_argo_observations")


def get_climatology_baseline_data() -> pd.DataFrame:
    """Dataset 04: Climatology baseline means and std for Z-score anomaly calculation."""
    return load_dataset_file("04_climatology_baseline")


def get_current_vectors_data() -> pd.DataFrame:
    """Dataset 05: Current velocity vectors (u, v) for particle advection & trajectory."""
    return load_dataset_file("05_current_vectors")


def get_wave_samples_data() -> pd.DataFrame:
    """Dataset 06: Wave parameters (significant wave height, peak period, direction)."""
    return load_dataset_file("06_wave_samples")
