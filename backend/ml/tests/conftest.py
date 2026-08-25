"""
backend/ml/tests/conftest.py
Pytest Fixtures for ML Unit, Integration, and Fusion Engine Tests.
Generates synthetic CF-compliant xarray Ocean Model Datasets and realistic Argo, Glider, and CTD profile observations.
"""

from datetime import datetime, timedelta
from typing import List
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT
)
from backend.ml.schemas import ObservationRecord, ProfileMeasurement


@pytest.fixture
def synthetic_ocean_model_ds() -> xr.Dataset:
    """
    Creates a synthetic 4D (time x depth x lat x lon) NetCDF-style ocean model dataset.
    Covers Indian Ocean EEZ region: lat 10°N..15°N, lon 70°E..75°E over 30 daily timesteps.
    """
    times = pd.date_range("2024-01-01", periods=30, freq="D")
    depths = np.array([0.0, 10.0, 20.0, 50.0, 100.0, 200.0])
    lats = np.linspace(10.0, 15.0, 6)
    lons = np.linspace(70.0, 75.0, 6)

    shape = (len(times), len(depths), len(lats), len(lons))
    np.random.seed(42)

    depth_profile_temp = 28.0 - 16.0 * (1.0 - np.exp(-depths / 50.0))
    depth_profile_sal = 34.5 + 1.2 * (1.0 - np.exp(-depths / 80.0))

    temp_4d = np.zeros(shape)
    sal_4d = np.zeros(shape)

    for t_idx in range(shape[0]):
        for d_idx in range(len(depths)):
            lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
            spatial_var = 0.5 * (lat_grid - 12.5) + 0.2 * (lon_grid - 72.5)
            time_var = 1.0 * np.sin(2 * np.pi * t_idx / 30.0)

            temp_4d[t_idx, d_idx, :, :] = depth_profile_temp[d_idx] + spatial_var + time_var
            sal_4d[t_idx, d_idx, :, :] = depth_profile_sal[d_idx] + 0.1 * spatial_var + 0.05 * time_var

    ds = xr.Dataset(
        data_vars={
            VAR_TEMPERATURE: ((COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE), temp_4d),
            VAR_SALINITY: ((COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE), sal_4d),
            VAR_U_CURRENT: ((COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE), np.full(shape, 0.15)),
            VAR_V_CURRENT: ((COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE), np.full(shape, -0.05)),
        },
        coords={
            COORD_TIME: times,
            COORD_DEPTH: depths,
            COORD_LATITUDE: lats,
            COORD_LONGITUDE: lons,
        },
        attrs={"title": "Synthetic ROMS Ocean Model Data", "institution": "INCOIS"},
    )
    return ds


@pytest.fixture
def synthetic_argo_observations(synthetic_ocean_model_ds: xr.Dataset) -> List[ObservationRecord]:
    """Generates synthetic Argo float observation profiles with systematic model bias."""
    obs_list: List[ObservationRecord] = []
    np.random.seed(123)

    times = pd.to_datetime(synthetic_ocean_model_ds[COORD_TIME].values)
    depths = synthetic_ocean_model_ds[COORD_DEPTH].values
    lats = synthetic_ocean_model_ds[COORD_LATITUDE].values
    lons = synthetic_ocean_model_ds[COORD_LONGITUDE].values

    for i in range(40):
        time_val = times[i % len(times)]
        lat_val = float(np.random.uniform(lats.min(), lats.max()))
        lon_val = float(np.random.uniform(lons.min(), lons.max()))

        model_sub = synthetic_ocean_model_ds.sel(
            {COORD_TIME: time_val, COORD_LATITUDE: lat_val, COORD_LONGITUDE: lon_val},
            method="nearest"
        )

        profiles = []
        for d in depths:
            mod_t = float(model_sub[VAR_TEMPERATURE].sel({COORD_DEPTH: d}, method="nearest").values)
            mod_s = float(model_sub[VAR_SALINITY].sel({COORD_DEPTH: d}, method="nearest").values)

            # Temperature bias: model underpredicts surface temp
            t_bias = 1.2 * np.exp(-d / 100.0) + float(np.random.normal(0, 0.05))
            # Salinity bias: model overpredicts salinity by +0.3 PSU
            s_bias = -0.3 + float(np.random.normal(0, 0.02))

            profiles.append(
                ProfileMeasurement(
                    depth=float(d),
                    temperature=mod_t + t_bias,
                    salinity=mod_s + s_bias,
                )
            )

        obs_record = ObservationRecord(
            platform_id=f"ARGO_{2900000 + i}",
            instrument_type="argo",
            latitude=lat_val,
            longitude=lon_val,
            time=time_val.to_pydatetime(),
            profiles=profiles,
        )
        obs_list.append(obs_record)

    return obs_list


@pytest.fixture
def synthetic_glider_observations(synthetic_ocean_model_ds: xr.Dataset) -> List[ObservationRecord]:
    """Generates synthetic Glider observation profiles along a spatial sawtooth transect."""
    obs_list: List[ObservationRecord] = []
    np.random.seed(456)

    times = pd.to_datetime(synthetic_ocean_model_ds[COORD_TIME].values)
    depths = synthetic_ocean_model_ds[COORD_DEPTH].values

    # Glider transect along lat 12.5°N
    for i in range(30):
        time_val = times[i % len(times)]
        lat_val = 12.5 + 0.1 * np.sin(i / 5.0)
        lon_val = 71.0 + 0.1 * i

        model_sub = synthetic_ocean_model_ds.sel(
            {COORD_TIME: time_val, COORD_LATITUDE: lat_val, COORD_LONGITUDE: lon_val},
            method="nearest"
        )

        profiles = []
        for d in depths:
            mod_t = float(model_sub[VAR_TEMPERATURE].sel({COORD_DEPTH: d}, method="nearest").values)
            mod_s = float(model_sub[VAR_SALINITY].sel({COORD_DEPTH: d}, method="nearest").values)

            # Glider temp bias: +0.7°C
            t_bias = 0.7 + float(np.random.normal(0, 0.04))
            # Glider salinity bias: -0.25 PSU
            s_bias = -0.25 + float(np.random.normal(0, 0.015))

            profiles.append(
                ProfileMeasurement(
                    depth=float(d),
                    temperature=mod_t + t_bias,
                    salinity=mod_s + s_bias,
                )
            )

        obs_record = ObservationRecord(
            platform_id=f"GLIDER_SEA042_{i}",
            instrument_type="glider",
            latitude=lat_val,
            longitude=lon_val,
            time=time_val.to_pydatetime(),
            profiles=profiles,
        )
        obs_list.append(obs_record)

    return obs_list


@pytest.fixture
def synthetic_ctd_observations(synthetic_ocean_model_ds: xr.Dataset) -> List[ObservationRecord]:
    """Generates synthetic CTD research vessel station profiles."""
    obs_list: List[ObservationRecord] = []
    np.random.seed(789)

    times = pd.to_datetime(synthetic_ocean_model_ds[COORD_TIME].values)
    depths = synthetic_ocean_model_ds[COORD_DEPTH].values

    for i in range(15):
        time_val = times[i * 2 % len(times)]
        lat_val = 11.5 + 0.2 * i
        lon_val = 72.0 + 0.15 * i

        model_sub = synthetic_ocean_model_ds.sel(
            {COORD_TIME: time_val, COORD_LATITUDE: lat_val, COORD_LONGITUDE: lon_val},
            method="nearest"
        )

        profiles = []
        for d in depths:
            mod_t = float(model_sub[VAR_TEMPERATURE].sel({COORD_DEPTH: d}, method="nearest").values)
            mod_s = float(model_sub[VAR_SALINITY].sel({COORD_DEPTH: d}, method="nearest").values)

            t_bias = 0.5 + float(np.random.normal(0, 0.03))
            s_bias = -0.15 + float(np.random.normal(0, 0.01))

            profiles.append(
                ProfileMeasurement(
                    depth=float(d),
                    temperature=mod_t + t_bias,
                    salinity=mod_s + s_bias,
                )
            )

        obs_record = ObservationRecord(
            platform_id=f"CTD_STATION_{i+1}",
            instrument_type="ctd",
            latitude=lat_val,
            longitude=lon_val,
            time=time_val.to_pydatetime(),
            profiles=profiles,
        )
        obs_list.append(obs_record)

    return obs_list
