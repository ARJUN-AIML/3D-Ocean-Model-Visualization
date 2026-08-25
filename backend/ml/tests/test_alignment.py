"""
backend/ml/tests/test_alignment.py
Unit tests for Model-vs-Observation Alignment Module.
"""

import pandas as pd
import pytest

from backend.ml.preprocessing.alignment import ModelObservationAligner, haversine_distance_km


def test_haversine_distance():
    # Distance between Mumbai (18.92, 72.83) and Goa (15.49, 73.82) is ~390 km
    dist = haversine_distance_km(18.92, 72.83, 15.49, 73.82)
    assert 370.0 < dist < 410.0


def test_align_observations_nearest(synthetic_ocean_model_ds, synthetic_argo_observations):
    aligner = ModelObservationAligner(method="nearest")
    df_aligned = aligner.align_observations(synthetic_ocean_model_ds, synthetic_argo_observations)

    assert not df_aligned.empty
    assert "obs_temperature" in df_aligned.columns
    assert "model_temperature" in df_aligned.columns
    assert "spatial_distance_km" in df_aligned.columns
    assert "time_delta_hours" in df_aligned.columns
    assert "depth_delta_m" in df_aligned.columns

    # Offsets should be reasonable within domain bounds
    assert df_aligned["spatial_distance_km"].max() < 100.0
    assert df_aligned["time_delta_hours"].max() < 48.0
    assert df_aligned["depth_delta_m"].max() < 1.0


def test_align_observations_interp(synthetic_ocean_model_ds, synthetic_argo_observations):
    aligner = ModelObservationAligner(method="interp")
    df_aligned = aligner.align_observations(synthetic_ocean_model_ds, synthetic_argo_observations)

    assert not df_aligned.empty
    assert "obs_temperature" in df_aligned.columns
    assert "model_temperature" in df_aligned.columns
    assert df_aligned["interpolation_method"].iloc[0] == "interp"
