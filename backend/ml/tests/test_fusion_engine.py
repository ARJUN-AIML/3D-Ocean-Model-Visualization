"""
backend/ml/tests/test_fusion_engine.py
Integration & Extensibility Test Suite for Model-Observation Fusion Engine (TASK ML-02).
Tests Argo, Glider, Multi-Sensor Fusion, Extensibility (CTD), QC filtering, and Metadata.
"""

import os
from datetime import datetime
import pytest

from backend.ml.service import OceanMLService
from backend.ml.schemas import ObservationRecord, ProfileMeasurement, BiasPredictionRequest
from backend.ml.preprocessing.qc import QualityControlFilter


@pytest.fixture
def tmp_fusion_registry_dir(tmp_path):
    return str(tmp_path / "fusion_registry")


def test_argo_temperature_bias_correction(synthetic_ocean_model_ds, synthetic_argo_observations, tmp_fusion_registry_dir):
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)
    metrics, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_argo_observations,
        target_variable="temperature",
        sensor_types=["argo"],
        version_tag="xgb_argo_temp_v1",
    )

    assert metrics.target_variable == "temperature"
    assert metrics.baseline_mae > 0.0
    assert metrics.corrected_mae < metrics.baseline_mae
    assert metrics.mae_reduction_pct > 0.0
    assert metadata.sensor_type == "argo"
    assert metadata.target_variable == "temperature"


def test_argo_salinity_bias_correction(synthetic_ocean_model_ds, synthetic_argo_observations, tmp_fusion_registry_dir):
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)
    metrics, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_argo_observations,
        target_variable="salinity",
        sensor_types=["argo"],
        version_tag="xgb_argo_sal_v1",
    )

    assert metrics.target_variable == "salinity"
    assert metrics.baseline_mae > 0.0
    assert metrics.corrected_mae < metrics.baseline_mae
    assert metrics.mae_reduction_pct > 0.0
    assert metadata.target_variable == "salinity"


def test_glider_temperature_bias_correction(synthetic_ocean_model_ds, synthetic_glider_observations, tmp_fusion_registry_dir):
    """Verifies Glider bias correction runs using the SAME fusion pipeline without code duplication."""
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)
    metrics, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_glider_observations,
        target_variable="temperature",
        sensor_types=["glider"],
        version_tag="xgb_glider_temp_v1",
    )

    assert metrics.target_variable == "temperature"
    assert metrics.corrected_mae < metrics.baseline_mae
    assert metrics.mae_reduction_pct > 0.0
    assert metadata.sensor_type == "glider"


def test_glider_salinity_bias_correction(synthetic_ocean_model_ds, synthetic_glider_observations, tmp_fusion_registry_dir):
    """Verifies Glider salinity bias correction runs using the SAME fusion pipeline."""
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)
    metrics, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_glider_observations,
        target_variable="salinity",
        sensor_types=["glider"],
        version_tag="xgb_glider_sal_v1",
    )

    assert metrics.target_variable == "salinity"
    assert metrics.corrected_mae < metrics.baseline_mae
    assert metadata.sensor_type == "glider"


def test_unified_multi_sensor_fusion(
    synthetic_ocean_model_ds, synthetic_argo_observations, synthetic_glider_observations, tmp_fusion_registry_dir
):
    """Verifies co-training on Argo + Glider observations in a single unified fusion model."""
    combined_obs = synthetic_argo_observations + synthetic_glider_observations
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)

    metrics, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=combined_obs,
        target_variable="temperature",
        sensor_types=["argo", "glider"],
        version_tag="xgb_argo_glider_temp_v1",
    )

    assert metrics.sample_count > len(synthetic_argo_observations)
    assert metrics.corrected_mae < metrics.baseline_mae
    assert "argo" in metadata.sensor_type and "glider" in metadata.sensor_type


def test_extensibility_ctd_future_sensor(synthetic_ocean_model_ds, synthetic_ctd_observations, tmp_fusion_registry_dir):
    """
    Extensibility Acceptance Test:
    Verifies that a new sensor type (CTD) is ingested and processed by the fusion pipeline
    with ZERO changes to the core ML correction engine logic.
    """
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)
    metrics, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_ctd_observations,
        target_variable="temperature",
        sensor_types=["ctd"],
        version_tag="xgb_ctd_temp_v1",
    )

    assert metrics.corrected_mae < metrics.baseline_mae
    assert metadata.sensor_type == "ctd"


def test_quality_control_filtering():
    qc = QualityControlFilter()
    unphysical_record = ObservationRecord(
        platform_id="BAD_OBS_99",
        instrument_type="argo",
        latitude=12.0,
        longitude=72.0,
        time=datetime(2024, 1, 1),
        profiles=[
            ProfileMeasurement(depth=-10.0, temperature=25.0, salinity=35.0),  # invalid negative depth
            ProfileMeasurement(depth=10.0, temperature=99.0, salinity=99.0),   # unphysical temp & salinity
            ProfileMeasurement(depth=20.0, temperature=25.0, salinity=35.0),   # valid slice
        ],
    )

    filtered = qc.filter_record(unphysical_record)

    assert filtered is not None
    # Only valid slice at depth=20m should remain
    assert len(filtered.profiles) == 1
    assert filtered.profiles[0].depth == 20.0
    assert filtered.profiles[0].temperature == 25.0


def test_fusion_metadata_verification(synthetic_ocean_model_ds, synthetic_argo_observations, tmp_fusion_registry_dir):
    service = OceanMLService(registry_dir=tmp_fusion_registry_dir)
    version_tag = "xgb_meta_test_v1"

    _, metadata = service.train_fusion_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_argo_observations,
        target_variable="temperature",
        version_tag=version_tag,
    )

    assert metadata.model_version == version_tag
    assert metadata.training_period.start_time != "N/A"
    assert metadata.validation_period.start_time != "N/A"
    assert metadata.test_period.start_time != "N/A"
    assert metadata.training_dataset_hash is not None
    assert "spatial_distance_km" in metadata.features_used
    assert "depth_delta_m" in metadata.features_used
    assert "sensor_code" in metadata.features_used
