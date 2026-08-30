"""
Unit tests for UNESCO 1983 (EOS-80) Seawater Density Equation.
"""

import numpy as np
import pytest
import xarray as xr

from backend.science.density import (
    calculate_eos80_density,
    calculate_dataset_density,
    depth_to_pressure,
)


def test_eos80_surface_density_known_values():
    """
    Validates surface seawater density at S=35 PSU, T=15°C, p=0 dbar.
    Standard EOS-80 reference value is ~1025.97 kg/m³.
    """
    rho = calculate_eos80_density(temperature=15.0, salinity=35.0, depth_m=0.0)
    assert pytest.approx(rho, abs=0.1) == 1025.97


def test_eos80_freshwater_density():
    """Validates pure water density at T=4°C (maximum density ~999.97 kg/m³)."""
    rho = calculate_eos80_density(temperature=4.0, salinity=0.0, depth_m=0.0)
    assert pytest.approx(rho, abs=0.1) == 999.97


def test_depth_to_pressure_conversion():
    """Validates depth to hydrostatic pressure conversion (1000m depth ≈ 1010-1030 dbar)."""
    p_surface = depth_to_pressure(0.0)
    p_1000m = depth_to_pressure(1000.0)

    assert p_surface == 0.0
    assert 1000.0 < p_1000m < 1050.0


def test_density_increases_with_depth():
    """Validates seawater compressibility: density at 1000m depth > surface density."""
    rho_surf = calculate_eos80_density(temperature=15.0, salinity=35.0, depth_m=0.0)
    rho_deep = calculate_eos80_density(temperature=15.0, salinity=35.0, depth_m=1000.0)
    assert rho_deep > rho_surf


def test_calculate_dataset_density():
    """Validates calculation of density DataArray on xarray Dataset."""
    ds = xr.Dataset(
        data_vars={
            "temperature": (["depth", "latitude", "longitude"], np.full((3, 4, 4), 20.0)),
            "salinity": (["depth", "latitude", "longitude"], np.full((3, 4, 4), 35.0)),
        },
        coords={
            "depth": [0.0, 100.0, 500.0],
            "latitude": [10.0, 11.0, 12.0, 13.0],
            "longitude": [60.0, 61.0, 62.0, 63.0],
        },
    )

    rho_da = calculate_dataset_density(ds)
    assert isinstance(rho_da, xr.DataArray)
    assert rho_da.shape == (3, 4, 4)
    assert rho_da.attrs["equation_of_state"] == "UNESCO 1983 (EOS-80)"
    assert "TEOS-10" not in rho_da.attrs["equation_of_state"]
    assert np.all(rho_da.values > 1000.0)
