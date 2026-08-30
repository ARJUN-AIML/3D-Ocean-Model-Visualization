"""
backend/science/sample_observations.py
Synthetic Argo, Glider, and CTD Observation Profile Generator.
Generates in-situ observation profile records in the Indian Ocean basin for ML pipeline alignment testing.

CRITICAL MANDATORY NOTICE:
- Generated observation profiles are strictly for development, testing, and offline demonstration.
- All observation records carry the explicit metadata attribute:
  data_status: "SYNTHETIC / DEMO DATA — NOT REAL OBSERVATIONS"
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from backend.ml.schemas import ObservationRecord, ProfileMeasurement, SensorType
from backend.science.sample_generator import DEMO_DATA_STATUS


def generate_synthetic_observations(
    num_argo: int = 15,
    num_glider: int = 10,
    num_ctd: int = 5,
    start_date: str = "2026-08-23",
    output_json_path: str = "data/demo/observations_demo.json",
) -> List[ObservationRecord]:
    """
    Generates a collection of synthetic Argo floats, Gliders, and CTD profiles in the Indian Ocean.
    Saves metadata to output_json_path with explicit SYNTHETIC / DEMO DATA provenance attributes.
    """
    np.random.seed(42)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    observations: List[ObservationRecord] = []

    depth_levels = [0.0, 10.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0]

    # 1. Argo Floats (Deep profiles down to 2000m)
    for i in range(num_argo):
        lat = float(np.random.uniform(5.0, 25.0))
        lon = float(np.random.uniform(55.0, 90.0))
        time_offset = float(np.random.uniform(0.0, 6.0))  # within 6 days
        dt = start_dt + timedelta(days=time_offset)

        profiles = []
        for z in depth_levels:
            # Temperature with subtle random in-situ observation noise (+- 0.3°C)
            temp = 28.5 - 24.5 * (1.0 - np.exp(-z / 250.0)) - 0.08 * lat + float(np.random.normal(0.0, 0.25))
            # Salinity with subtle random noise (+- 0.15 PSU)
            sal = (36.0 if lon < 75.0 else 33.0) + float(np.random.normal(0.0, 0.15))
            profiles.append(ProfileMeasurement(depth=z, temperature=float(np.clip(temp, 2.0, 32.0)), salinity=float(np.clip(sal, 30.0, 37.5))))

        obs = ObservationRecord(
            platform_id=f"ARGO_{2900000 + i}",
            instrument_type=SensorType.ARGO.value,
            latitude=round(lat, 4),
            longitude=round(lon, 4),
            time=dt,
            profiles=profiles,
            source_metadata={
                "data_status": DEMO_DATA_STATUS,
                "is_synthetic": True,
                "institution": "INCOIS Digital Twin (Demo)",
                "quality_flag": "QC_PASSED",
            },
        )
        observations.append(obs)

    # 2. Gliders (High spatial density, upper 500m)
    for i in range(num_glider):
        lat = float(np.random.uniform(8.0, 18.0))
        lon = float(np.random.uniform(65.0, 85.0))
        time_offset = float(np.random.uniform(0.0, 6.0))
        dt = start_dt + timedelta(days=time_offset)

        profiles = []
        for z in [d for d in depth_levels if d <= 500.0]:
            temp = 28.5 - 24.5 * (1.0 - np.exp(-z / 250.0)) - 0.08 * lat + float(np.random.normal(0.0, 0.2))
            sal = (35.8 if lon < 75.0 else 33.2) + float(np.random.normal(0.0, 0.1))
            profiles.append(ProfileMeasurement(depth=z, temperature=float(np.clip(temp, 4.0, 32.0)), salinity=float(np.clip(sal, 30.0, 37.5))))

        obs = ObservationRecord(
            platform_id=f"GLIDER_IN_{500 + i}",
            instrument_type=SensorType.GLIDER.value,
            latitude=round(lat, 4),
            longitude=round(lon, 4),
            time=dt,
            profiles=profiles,
            source_metadata={
                "data_status": DEMO_DATA_STATUS,
                "is_synthetic": True,
                "institution": "INCOIS Digital Twin (Demo)",
                "quality_flag": "QC_PASSED",
            },
        )
        observations.append(obs)

    # 3. CTD Stations (Full depth casts)
    for i in range(num_ctd):
        lat = float(np.random.uniform(10.0, 20.0))
        lon = float(np.random.uniform(70.0, 88.0))
        time_offset = float(np.random.uniform(0.0, 6.0))
        dt = start_dt + timedelta(days=time_offset)

        profiles = []
        for z in depth_levels:
            temp = 28.5 - 24.5 * (1.0 - np.exp(-z / 250.0)) - 0.08 * lat + float(np.random.normal(0.0, 0.15))
            sal = (35.5 if lon < 75.0 else 33.5) + float(np.random.normal(0.0, 0.08))
            profiles.append(ProfileMeasurement(depth=z, temperature=float(np.clip(temp, 2.0, 32.0)), salinity=float(np.clip(sal, 30.0, 37.5))))

        obs = ObservationRecord(
            platform_id=f"CTD_STN_{100 + i}",
            instrument_type=SensorType.CTD.value,
            latitude=round(lat, 4),
            longitude=round(lon, 4),
            time=dt,
            profiles=profiles,
            source_metadata={
                "data_status": DEMO_DATA_STATUS,
                "is_synthetic": True,
                "institution": "INCOIS Digital Twin (Demo)",
                "quality_flag": "QC_PASSED",
            },
        )
        observations.append(obs)

    # Save to JSON file if requested
    if output_json_path:
        serializable_data = [obs.dict() for obs in observations]
        # Convert datetime objects to string
        for item in serializable_data:
            item["time"] = item["time"].isoformat()

        with open(output_json_path, "w") as f:
            json.dump(serializable_data, f, indent=2)

    return observations
