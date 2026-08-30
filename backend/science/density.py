"""
backend/science/density.py
UNESCO 1983 / EOS-80 International Equation of State for Seawater Density.
Calculates seawater density rho(S, T, p) in kg/m³ from Salinity (PSU), Temperature (°C), and Depth (m).

NOTE ON SCIENTIFIC METHODOLOGY:
- This module implements the UNESCO 1983 (EOS-80) standard for seawater density.
- It is explicitly EOS-80 (NOT TEOS-10 / GSW).
- Hydrostatic pressure p (dbar) is derived from depth z (m) using Saunders & Fofonoff (1976) or standard approximation: p ≈ 1.00618 * z.
- Salinity is Practical Salinity S (PSU).
- Temperature is in-situ temperature T (°C).
"""

from typing import Union
import numpy as np
import xarray as xr


def depth_to_pressure(depth_m: Union[float, np.ndarray, xr.DataArray], latitude: float = 15.0) -> Union[float, np.ndarray, xr.DataArray]:
    """
    Converts depth in meters (z >= 0, positive down) to hydrostatic pressure in decibars (dbar).
    Uses the standard Saunders and Fofonoff (1976) formula approximation:
    p(z) ≈ 1.00618 * z + 2.18e-6 * z²
    """
    z = np.abs(depth_m)
    # Gravity variation with latitude
    sin_lat = np.sin(np.radians(latitude))
    g = 9.780318 * (1.0 + 5.2788e-3 * sin_lat**2 + 2.36e-5 * sin_lat**4)
    # Mean density factor ~ 1025 kg/m³, 1 dbar = 10^4 Pa
    p = (g * 1025.0 * z) / 10000.0
    return p


def calculate_eos80_density(
    temperature: Union[float, np.ndarray, xr.DataArray],
    salinity: Union[float, np.ndarray, xr.DataArray],
    depth_m: Union[float, np.ndarray, xr.DataArray] = 0.0,
    latitude: float = 15.0,
) -> Union[float, np.ndarray, xr.DataArray]:
    """
    Calculates in-situ seawater density rho(S, T, p) in kg/m³ using UNESCO 1983 (EOS-80).

    Parameters:
        temperature: In-situ ocean temperature in °C (ITS-90 or IPTS-68).
        salinity: Practical salinity S in PSU.
        depth_m: Depth in meters (z >= 0, positive down). Default is 0.0m (surface).
        latitude: Latitude in degrees for gravity correction in pressure derivation.

    Returns:
        Seawater density rho in kg/m³. Typical surface values range from 1020.0 to 1030.0 kg/m³.
    """
    T = temperature
    S = salinity
    p = depth_to_pressure(depth_m, latitude=latitude)

    # 1. Pure water density rho_w(T) at 1 atm (p = 0 dbar) - Millero & Poisson (1981)
    rho_w = (
        999.842594
        + 6.793952e-2 * T
        - 9.095290e-3 * T**2
        + 1.001685e-4 * T**3
        - 1.120083e-6 * T**4
        + 6.536332e-9 * T**5
    )

    # 2. Seawater density rho(S, T, 0) at atmospheric pressure (p = 0 dbar)
    A = (
        8.24493e-1
        - 4.0899e-3 * T
        + 7.6438e-5 * T**2
        - 8.2467e-7 * T**3
        + 5.3875e-9 * T**4
    )
    B = -5.72466e-3 + 1.0227e-4 * T - 1.6546e-6 * T**2
    C = 4.8314e-4

    rho_0 = rho_w + A * S + B * S**1.5 + C * S**2

    # If depth / pressure is 0, return atmospheric density
    if np.all(p == 0.0):
        return rho_0

    # 3. Secant bulk modulus K(S, T, p) for pressure dependence
    Kw = (
        19652.21
        + 148.4206 * T
        - 2.327105 * T**2
        + 1.360477e-2 * T**3
        - 5.155288e-5 * T**4
    )

    Ak = (
        54.6746
        - 0.603459 * T
        + 1.09987e-2 * T**2
        - 6.1670e-5 * T**3
    )
    Bk = 7.944e-2 + 1.6483e-2 * T - 5.3009e-4 * T**2

    K_0 = Kw + Ak * S + Bk * S**1.5

    # Pressure dependence terms for bulk modulus K(S, T, p)
    e = 3.239908 + 1.43713e-3 * T + 1.16092e-4 * T**2 - 5.77905e-7 * T**3
    f = 2.2838e-3 - 1.0981e-5 * T - 1.6078e-6 * T**2
    g_k = 1.91075e-4

    h = 8.50935e-5 - 6.12293e-6 * T + 5.2787e-8 * T**2
    i = -9.9348e-7 + 2.0816e-8 * T + 9.1697e-10 * T**2

    K_p = K_0 + (e + f * S + g_k * S**1.5) * p + (h + i * S) * p**2

    # In-situ density at pressure p
    rho_p = rho_0 / (1.0 - p / K_p)
    return rho_p


def calculate_dataset_density(ds: xr.Dataset, latitude: float = 15.0) -> xr.DataArray:
    """
    Computes EOS-80 density DataArray for an entire xarray Dataset containing
    'temperature' (°C) and 'salinity' (PSU).
    Preserves dimensions, coordinates, and metadata.
    """
    if "temperature" not in ds.data_vars or "salinity" not in ds.data_vars:
        raise ValueError("Dataset must contain both 'temperature' and 'salinity' variables to calculate density.")

    temp = ds["temperature"]
    sal = ds["salinity"]

    if "depth" in ds.coords:
        depth = ds["depth"]
    elif "depth" in ds.data_vars:
        depth = ds["depth"]
    else:
        depth = 0.0

    rho = calculate_eos80_density(temp, sal, depth_m=depth, latitude=latitude)

    # Wrap as xarray DataArray
    if isinstance(rho, (xr.DataArray, xr.Dataset)):
        rho_da = rho
    else:
        rho_da = xr.DataArray(rho, coords=temp.coords, dims=temp.dims)

    rho_da.attrs = {
        "standard_name": "sea_water_density",
        "long_name": "Sea Water In-Situ Density (UNESCO 1983 EOS-80)",
        "units": "kg m-3",
        "equation_of_state": "UNESCO 1983 (EOS-80)",
        "pressure_conversion": "Saunders & Fofonoff (1976)",
    }
    return rho_da
