"""
backend/app/dependencies.py
Shared singleton dependencies for FastAPI endpoints.
Loads DatasetManager, OceanMLService, and default dataset models.
"""

from typing import Tuple
import xarray as xr

from backend.science.dataset_manager import OceanDatasetManager
from backend.ml.service import OceanMLService

# Global Singleton state
_dataset_manager: OceanDatasetManager = None
_ml_service: OceanMLService = None


def get_dataset_manager() -> OceanDatasetManager:
    global _dataset_manager
    if _dataset_manager is None:
        _dataset_manager = OceanDatasetManager(data_root="data")
    return _dataset_manager


def get_ml_service() -> OceanMLService:
    global _ml_service
    if _ml_service is None:
        _ml_service = OceanMLService(registry_dir="artifacts/ml_registry")
    return _ml_service


def get_default_dataset() -> Tuple[xr.Dataset, str]:
    dm = get_dataset_manager()
    return dm.get_or_create_default_dataset()
