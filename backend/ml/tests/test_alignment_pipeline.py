"""
Unit tests for Model-vs-Observation Alignment Pipeline, Tolerances, and Alignment Reports.
"""

from datetime import datetime
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.ml.preprocessing.alignment import ModelObservationAligner, haversine_distance_km
from backend.ml.schemas import ObservationRecord, ProfileMeasurement, SensorType
from backend.science.canonical import COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE, VAR_TEMPERATURE
from backend.science.alignment_report import generate_alignment_report


@pytest.fixture
def dummy_model_dataset():
    times = [pd.Timestamp("2026-08-25T00:00:00"), pd.Timestamp("2026-08-26T00:00:00")]
    depths = [0.0, 10.0, 50.0]
    lats = [10.0, 11.0, 12.0]
    lons = [60.0, 61.0, 62.0]

    temp = np.full((2, 3, 3, 3), 28.0)
    # Give depth variation
    temp[:, 1, :, :] = 25.0
    temp[:, 2, :, :] = 20.0

    ds = xr.Dataset(
        data_vars={
            VAR_TEMPERATURE: (["time", "depth", "latitude", "longitude"], temp),
        },
        coords={
            COORD_TIME: times,
            COORD_DEPTH: depths,
            COORD_LATITUDE: lats,
            COORD_LONGITUDE: lons,
        },
    )
    return ds


@pytest.fixture
def dummy_observations():
    obs1 = ObservationRecord(
        platform_id="ARGO_001",
        instrument_type=SensorType.ARGO.value,
        latitude=10.0,
        longitude=60.0,
        time=datetime(2026, 8, 25, 0, 0),
        profiles=[
            ProfileMeasurement(depth=0.0, temperature=29.0),
            ProfileMeasurement(depth=10.0, temperature=25.5),
        ],
        source_metadata={"quality_flag": "QC_PASSED"},
    )
    # Observation outside spatial tolerance (lat 25.0, lon 80.0)
    obs_far = ObservationRecord(
        platform_id="ARGO_FAR",
        instrument_type=SensorType.ARGO.value,
        latitude=25.0,
        longitude=80.0,
        time=datetime(2026, 8, 25, 0, 0),
        profiles=[ProfileMeasurement(depth=0.0, temperature=28.0)],
        source_metadata={"quality_flag": "QC_PASSED"},
    )
    return [obs1, obs_far]


def test_haversine_distance():
    # Distance between (10, 60) and (10, 60) is 0 km
    assert haversine_distance_km(10.0, 60.0, 10.0, 60.0) == 0.0
    # Distance between (10, 60) and (11, 60) is ~111 km
    assert pytest.approx(haversine_distance_km(10.0, 60.0, 11.0, 60.0), abs=2.0) == 111.19


def test_alignment_exact_match_and_bias_calculation(dummy_model_dataset, dummy_observations):
    aligner = ModelObservationAligner(method="nearest", max_spatial_distance_km=50.0)
    df_aligned = aligner.align_observations(dummy_model_dataset, dummy_observations, target_variable="temperature")

    assert len(df_aligned) == 2  # obs1 has 2 profile depths
    assert "bias" in df_aligned.columns
    # Obs 1 depth 0: obs=29.0, model=28.0 -> bias = 29.0 - 28.0 = 1.0
    row_surf = df_aligned[df_aligned["depth"] == 0.0].iloc[0]
    assert row_surf["obs_value"] == 29.0
    assert row_surf["model_value"] == 28.0
    assert row_surf["bias"] == 1.0
    assert row_surf["quality_flag"] == "QC_PASSED"


def test_alignment_spatial_tolerance_cutoff(dummy_model_dataset, dummy_observations):
    # Set strict spatial cutoff max_spatial_distance_km = 10.0
    aligner = ModelObservationAligner(method="nearest", max_spatial_distance_km=10.0)
    df_aligned = aligner.align_observations(dummy_model_dataset, dummy_observations, target_variable="temperature")

    # ARGO_FAR is > 1000km away, so it must be rejected/excluded
    assert "ARGO_FAR" not in df_aligned["obs_platform_id"].values


def test_alignment_missing_values_rejected(dummy_model_dataset):
    # Create obs with NaN temperature
    obs_nan = ObservationRecord(
        platform_id="ARGO_NAN",
        instrument_type=SensorType.ARGO.value,
        latitude=10.0,
        longitude=60.0,
        time=datetime(2026, 8, 25, 0, 0),
        profiles=[ProfileMeasurement(depth=0.0, temperature=None)],
        source_metadata={},
    )
    aligner = ModelObservationAligner(method="nearest")
    df_aligned = aligner.align_observations(dummy_model_dataset, [obs_nan], target_variable="temperature")

    # Must be empty because temperature is None
    assert df_aligned.empty


def test_alignment_report_generation(dummy_model_dataset, dummy_observations):
    aligner = ModelObservationAligner(method="nearest")
    df_aligned = aligner.align_observations(dummy_model_dataset, dummy_observations, target_variable="temperature")

    report = generate_alignment_report(df_aligned, total_observations_input=len(dummy_observations), dataset_id="test_ds")
    assert report["dataset_id"] == "test_ds"
    assert report["summary"]["total_observations_input"] == 2
    assert report["summary"]["matched_observations"] == len(df_aligned)
    assert "markdown_report" in report
