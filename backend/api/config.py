"""
backend/api/config.py
System Configuration for INCOIS 3D Ocean Visualization FastAPI Layer.
Uses Pydantic v2 BaseSettings via pydantic-settings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Application Settings loaded from environment variables or defaults."""

    API_TITLE: str = "INCOIS 3D Ocean Data Visualization API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Data directory paths
    DATA_DIR: str = "data"
    OBSERVATIONS_DIR: str = "data/observations"
    HYCOM_DATA_PATH: str = "data/hycom/RSMC_hycom_20260831.nc"
    ARGO_DATA_PATH: str = "data/argo/ARGO_OceanTwin_clean.csv"
    ARGO_VAM_DATA_PATH: str = "data/argo/incois_argo_mnt_VAM_96a3_6d78_f66f_U1788337287965.nc"
    WW3_DATA_PATH: str = "data/ww3/"

    # CORS configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # In-memory Dataset Cache Limit
    DATASET_CACHE_MAX_SIZE: int = 10

    # Response Size Protection (Requirement 8 & 9)
    # Rejects requests where total 2D slice cells (len(lat) * len(lon)) exceed MAX_SLICE_CELLS
    MAX_SLICE_CELLS: int = 250000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = APISettings()
