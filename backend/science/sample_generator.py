"""
backend/science/sample_generator.py
Indian Ocean Physical Oceanography Demo Dataset Generator.
Generates scientifically plausible 4D gridded fields (time x depth x latitude x longitude)
for Temperature, Salinity, u-velocity, v-velocity, w-velocity, Density, and Chlorophyll.

CRITICAL MANDATORY NOTICE:
- Generated datasets are strictly for development, testing, and offline demonstration.
- All generated files carry the explicit metadata tag:
  data_status: "SYNTHETIC / DEMO DATA — NOT REAL OBSERVATIONS"
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import xarray as xr

from backend.science.density import calculate_eos80_density
from backend.science.canonical import (
    COORD_TIME, COORD_DEPTH, COORD_LATITUDE, COORD_LONGITUDE,
    VAR_TEMPERATURE, VAR_SALINITY, VAR_U_CURRENT, VAR_V_CURRENT, VAR_W_CURRENT, VAR_CHLOROPHYLL
)

DEMO_DATA_STATUS = "SYNTHETIC / DEMO DATA — NOT REAL OBSERVATIONS"


def generate_indian_ocean_demo_dataset(
    output_path: str = "data/demo/indian_ocean_demo.nc",
    num_days: int = 7,
    lat_range: tuple = (0.0, 30.0, 0.5),      # 0 to 30°N at 0.5° grid
    lon_range: tuple = (45.0, 100.0, 0.5),    # 45 to 100°E at 0.5° grid
    depth_levels: list = [0.0, 10.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0],
    start_date: str = "2026-08-23",
) -> xr.Dataset:
    """
    Generates a scientifically plausible 4D NetCDF dataset for the Indian Ocean basin.
    Saves the dataset to output_path with explicit SYNTHETIC / DEMO DATA provenance attributes.
    """
    lats = np.arange(lat_range[0], lat_range[1] + lat_range[2], lat_range[2])
    lons = np.arange(lon_range[0], lon_range[1] + lon_range[2], lon_range[2])
    depths = np.array(depth_levels, dtype=float)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    times = [start_dt + timedelta(days=i) for i in range(num_days)]

    n_time = len(times)
    n_depth = len(depths)
    n_lat = len(lats)
    n_lon = len(lons)

    # Meshgrid setup for vectorized field generation
    LON, LAT = np.meshgrid(lons, lats)

    # Pre-allocate 4D arrays: (time, depth, lat, lon)
    temp_4d = np.zeros((n_time, n_depth, n_lat, n_lon), dtype=np.float32)
    sal_4d = np.zeros((n_time, n_depth, n_lat, n_lon), dtype=np.float32)
    u_4d = np.zeros((n_time, n_depth, n_lat, n_lon), dtype=np.float32)
    v_4d = np.zeros((n_time, n_depth, n_lat, n_lon), dtype=np.float32)
    w_4d = np.zeros((n_time, n_depth, n_lat, n_lon), dtype=np.float32)
    chl_4d = np.zeros((n_time, n_depth, n_lat, n_lon), dtype=np.float32)

    for t_idx in range(n_time):
        t_factor = np.sin(2.0 * np.pi * t_idx / 30.0)

        for d_idx, z in enumerate(depths):
            # 1. Temperature Profile: Surface ~29°C, thermocline drop at 100-200m, deep ocean ~3-4°C
            # Latitudinal cooling toward north/south, Arabian Sea warmer surface
            base_temp = 28.5 - 24.5 * (1.0 - np.exp(-z / 250.0)) - 0.08 * LAT
            # Synoptic eddy perturbation
            eddy_t = 1.2 * np.sin(np.radians(LAT * 3.0)) * np.cos(np.radians((LON - 65.0) * 2.0))
            t_field = base_temp + eddy_t * np.exp(-z / 300.0) + 0.2 * t_factor
            temp_4d[t_idx, d_idx, :, :] = np.clip(t_field, 2.0, 32.0)

            # 2. Salinity Profile: Arabian Sea (west, >60°E) high salinity (~36.5 PSU), Bay of Bengal (east, >80°E) fresh (~32.5 PSU)
            sal_west = 36.5 - 1.5 * (1.0 - np.exp(-z / 400.0))
            sal_east = 32.5 + 2.0 * (1.0 - np.exp(-z / 300.0))
            lon_weight = np.clip((LON - 50.0) / 45.0, 0.0, 1.0)
            s_field = (1.0 - lon_weight) * sal_west + lon_weight * sal_east
            sal_4d[t_idx, d_idx, :, :] = np.clip(s_field, 30.0, 37.5)

            # 3. Ocean Currents: u (eastward) and v (northward) in m/s
            # Equatorial Jet & Somali Boundary Current dynamics
            depth_decay = np.exp(-z / 200.0)
            u_surf = 0.4 * np.sin(np.radians(LAT * 6.0)) + 0.2 * np.cos(np.radians(LON * 4.0))
            v_surf = 0.5 * np.exp(-((LON - 52.0) ** 2) / 25.0) * np.sin(np.radians(LAT * 4.0))  # Somali boundary current
            u_4d[t_idx, d_idx, :, :] = u_surf * depth_decay
            v_4d[t_idx, d_idx, :, :] = v_surf * depth_decay
            w_4d[t_idx, d_idx, :, :] = (1.5e-5 * np.sin(np.radians(LAT * 4.0))) * depth_decay

            # 4. Chlorophyll (mg/m³): Maximum near surface / coastal upwelling, exponentially zero in deep ocean
            chl_surf = 0.8 + 1.2 * np.exp(-((LON - 55.0) ** 2) / 50.0) + 0.3 * (LAT / 30.0)
            chl_4d[t_idx, d_idx, :, :] = chl_surf * np.exp(-((z - 30.0) ** 2) / 1000.0)

    # Create Xarray Dataset
    ds = xr.Dataset(
        data_vars={
            VAR_TEMPERATURE: (["time", "depth", "latitude", "longitude"], temp_4d),
            VAR_SALINITY: (["time", "depth", "latitude", "longitude"], sal_4d),
            VAR_U_CURRENT: (["time", "depth", "latitude", "longitude"], u_4d),
            VAR_V_CURRENT: (["time", "depth", "latitude", "longitude"], v_4d),
            VAR_W_CURRENT: (["time", "depth", "latitude", "longitude"], w_4d),
            VAR_CHLOROPHYLL: (["time", "depth", "latitude", "longitude"], chl_4d),
        },
        coords={
            COORD_TIME: pd.to_datetime(times),
            COORD_DEPTH: depths,
            COORD_LATITUDE: lats,
            COORD_LONGITUDE: lons,
        },
        attrs={
            "title": "Indian Ocean Physical Oceanography Demo Dataset",
            "institution": "BluePulse / OceanTwin Digital Twin Platform (Demo Mode)",
            "source": "Synthetic Physics-Informed Numerical Model",
            "data_status": DEMO_DATA_STATUS,
            "is_synthetic": "true",
            "comment": "WARNING: This dataset is synthetic for offline demonstration and testing. NOT real observations.",
            "spatial_resolution": "0.5 degree",
            "geospatial_lat_min": float(lats[0]),
            "geospatial_lat_max": float(lats[-1]),
            "geospatial_lon_min": float(lons[0]),
            "geospatial_lon_max": float(lons[-1]),
        },
    )

    # Assign CF attributes to data variables
    ds[VAR_TEMPERATURE].attrs = {"units": "degC", "standard_name": "sea_water_temperature", "long_name": "Sea Water Temperature"}
    ds[VAR_SALINITY].attrs = {"units": "PSU", "standard_name": "sea_water_salinity", "long_name": "Sea Water Salinity"}
    ds[VAR_U_CURRENT].attrs = {"units": "m s-1", "standard_name": "eastward_sea_water_velocity", "long_name": "Eastward Velocity Component"}
    ds[VAR_V_CURRENT].attrs = {"units": "m s-1", "standard_name": "northward_sea_water_velocity", "long_name": "Northward Velocity Component"}
    ds[VAR_W_CURRENT].attrs = {"units": "m s-1", "standard_name": "upward_sea_water_velocity", "long_name": "Upward Velocity Component"}
    ds[VAR_CHLOROPHYLL].attrs = {"units": "mg m-3", "standard_name": "mass_concentration_of_chlorophyll_a_in_sea_water", "long_name": "Chlorophyll-a Concentration"}

    # Calculate UNESCO 1983 EOS-80 density field
    ds["density"] = calculate_eos80_density(ds[VAR_TEMPERATURE], ds[VAR_SALINITY], ds[COORD_DEPTH])

    # Save NetCDF file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ds.to_netcdf(output_path)
    return ds
