"""
backend/api/routers/datasets.py
Dataset Discovery and Metadata Profile Router.
"""

from typing import List
from fastapi import APIRouter, Depends
from backend.api.dependencies import get_dataset_service
from backend.api.services.dataset_service import DatasetService
from backend.api.schemas.datasets import DatasetSummary, DatasetDetail

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.get("", response_model=List[DatasetSummary])
def list_datasets(
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> List[DatasetSummary]:
    """
    Discovers available scientific ocean datasets in configured data directory.
    Returns an empty list if no real datasets are present (Requirements 2 & 3).
    """
    return dataset_service.discover_datasets()


@router.get("/{dataset_id:path}", response_model=DatasetDetail)
def get_dataset_metadata(
    dataset_id: str,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> DatasetDetail:
    """
    Returns complete scientific metadata profile for a specified dataset ID.
    Uses existing DatasetProfiler infrastructure (Requirement 10).
    """
    return dataset_service.get_dataset_detail(dataset_id)
