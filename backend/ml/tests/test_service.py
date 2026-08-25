"""
backend/ml/tests/test_service.py
End-to-End Integration Test for OceanMLService Pipeline.
Verifies complete flow from NetCDF dataset + Argo observations to training, validation,
held-out evaluation, metadata artifact serialization, and inference.
"""

import os
import pytest

from backend.ml.service import OceanMLService
from backend.ml.schemas import BiasPredictionRequest


@pytest.fixture
def tmp_registry_dir(tmp_path):
    return str(tmp_path / "ml_registry")


def test_end_to_end_ml_service_pipeline(
    synthetic_ocean_model_ds,
    synthetic_argo_observations,
    tmp_registry_dir
):
    service = OceanMLService(registry_dir=tmp_registry_dir)

    # Run end-to-end pipeline
    version_tag = "test_bias_v1"
    metrics, metadata = service.train_xgb_bias_pipeline(
        model_ds=synthetic_ocean_model_ds,
        observations=synthetic_argo_observations,
        version_tag=version_tag,
        alignment_method="nearest",
    )

    # Assertions on metrics improvement
    assert metrics.baseline_mae > 0.0
    assert metrics.corrected_mae < metrics.baseline_mae
    assert metrics.mae_reduction_pct > 0.0
    assert metrics.rmse_reduction_pct > 0.0
    assert metrics.sample_count > 0

    # Assertions on metadata artifact
    assert metadata.model_version == version_tag
    assert metadata.model_name == "xgb_fusion_bias_correction"
    assert len(metadata.features_used) > 0
    assert metadata.evaluation_metrics.corrected_mae == metrics.corrected_mae

    # Verify files created in registry dir
    version_dir = os.path.join(tmp_registry_dir, version_tag)
    assert os.path.exists(os.path.join(version_dir, "metadata.json"))
    assert os.path.exists(os.path.join(version_dir, "model.json"))

    # Test loading model from registry
    new_service = OceanMLService(registry_dir=tmp_registry_dir)
    loaded_meta = new_service.load_bias_model(version_tag)
    assert loaded_meta.model_version == version_tag

    # Test single prediction inference
    req = BiasPredictionRequest(
        target_variable="temperature",
        sensor_type="argo",
        model_temperature=26.0,
        model_salinity=35.0,
        model_u=0.1,
        model_v=-0.1,
        depth=10.0,
        latitude=12.5,
        longitude=72.5,
        timestamp=synthetic_argo_observations[0].time,
    )
    result = new_service.predict_bias_correction(req)

    assert result.model_value == 26.0
    assert result.model_version == version_tag
    assert result.corrected_value == result.model_value + result.predicted_correction
    assert result.uncertainty_estimate is not None


def test_statistical_anomaly_pipeline(synthetic_ocean_model_ds):
    service = OceanMLService()
    service.fit_anomaly_baseline(synthetic_ocean_model_ds, variable="temperature")

    raw_anom, std_anom = service.compute_dataset_anomalies(synthetic_ocean_model_ds, variable="temperature")

    assert raw_anom is not None
    assert std_anom is not None
    assert raw_anom.shape == synthetic_ocean_model_ds["temperature"].shape
