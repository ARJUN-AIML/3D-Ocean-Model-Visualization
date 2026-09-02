"""
backend/api/dependencies.py
FastAPI Dependency Injection for API Services and Configuration.
"""

from functools import lru_cache
from fastapi import Depends
from backend.api.config import APISettings, settings
from backend.api.services.dataset_service import DatasetService
from backend.api.services.ocean_service import OceanService
from backend.api.services.hycom_service import HycomService
from backend.api.services.argo_service import ArgoService
from backend.api.services.vam_baseline_service import VAMBaselineService
from backend.api.services.comparison_service import ComparisonService
from backend.api.services.anomaly_service import AnomalyService


@lru_cache()
def get_settings() -> APISettings:
    """Returns application configuration settings."""
    return settings


@lru_cache()
def get_dataset_service() -> DatasetService:
    """Singleton instance of DatasetService for API dependency injection."""
    return DatasetService()


def get_ocean_service(
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> OceanService:
    """Instantiates OceanService with active DatasetService dependency."""
    return OceanService(dataset_service=dataset_service)


@lru_cache()
def get_hycom_service() -> HycomService:
    """Singleton instance of HycomService."""
    return HycomService()


@lru_cache()
def get_argo_service() -> ArgoService:
    """Singleton instance of ArgoService."""
    return ArgoService()


@lru_cache()
def get_vam_baseline_service() -> VAMBaselineService:
    """Singleton instance of VAMBaselineService."""
    return VAMBaselineService()


def get_comparison_service(
    hycom_service: HycomService = Depends(get_hycom_service),
    argo_service: ArgoService = Depends(get_argo_service),
) -> ComparisonService:
    """Instantiates ComparisonService with active HYCOM and Argo dependencies."""
    return ComparisonService(hycom_service=hycom_service, argo_service=argo_service)


def get_anomaly_service(
    vam_baseline_service: VAMBaselineService = Depends(get_vam_baseline_service),
) -> AnomalyService:
    """Instantiates AnomalyService with active VAM Baseline dependency."""
    return AnomalyService(vam_baseline_service=vam_baseline_service)
