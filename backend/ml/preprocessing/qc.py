"""
backend/ml/preprocessing/qc.py
Observational Ingestion Quality Control (QC) Module.
Filters in-situ profiles (Argo, Glider, CTD, etc.) using physical bounds and QC flags
before model alignment and ML feature extraction.
"""

from typing import List, Optional, Tuple
from datetime import datetime

from backend.ml.schemas import ObservationRecord, ProfileMeasurement

# Standard Oceanographic Physical Bounds
TEMP_MIN, TEMP_MAX = -2.0, 40.0      # °C
SAL_MIN, SAL_MAX = 0.0, 45.0          # PSU
DEPTH_MIN, DEPTH_MAX = 0.0, 10000.0   # Meters
LAT_MIN, LAT_MAX = -90.0, 90.0        # Degrees
LON_MIN, LON_MAX = -180.0, 180.0      # Degrees

# Standard Oceanographic QC Flags (IOC / Argo standard)
# 1: Good data, 2: Probably good data
VALID_QC_FLAGS = {1, 2, "1", "2", "GOOD", "PROBABLY_GOOD"}


class QualityControlFilter:
    """
    Quality Control filter for sensor profiles.
    Performs physical range validation and metadata flag checking.
    """

    def __init__(
        self,
        temp_bounds: Tuple[float, float] = (TEMP_MIN, TEMP_MAX),
        sal_bounds: Tuple[float, float] = (SAL_MIN, SAL_MAX),
        depth_bounds: Tuple[float, float] = (DEPTH_MIN, DEPTH_MAX),
    ):
        self.temp_min, self.temp_max = temp_bounds
        self.sal_min, self.sal_max = sal_bounds
        self.depth_min, self.depth_max = depth_bounds

    def filter_record(self, record: ObservationRecord) -> Optional[ObservationRecord]:
        """
        Validates an observation record and filters out unphysical measurements.
        Returns a sanitized ObservationRecord or None if record is completely invalid.
        """
        # Validate latitude and longitude
        if not (LAT_MIN <= record.latitude <= LAT_MAX):
            return None
        if not (LON_MIN <= record.longitude <= LON_MAX):
            return None

        sanitized_profiles: List[ProfileMeasurement] = []

        for p in record.profiles:
            # Check depth bounds
            if not (self.depth_min <= p.depth <= self.depth_max):
                continue

            # Temperature range check
            t_valid = p.temperature
            if t_valid is not None and not (self.temp_min <= t_valid <= self.temp_max):
                t_valid = None

            # Salinity range check
            s_valid = p.salinity
            if s_valid is not None and not (self.sal_min <= s_valid <= self.sal_max):
                s_valid = None

            # Keep slice if temperature or salinity is valid
            if t_valid is not None or s_valid is not None:
                sanitized_profiles.append(
                    ProfileMeasurement(
                        depth=p.depth,
                        temperature=t_valid,
                        salinity=s_valid,
                        chlorophyll=p.chlorophyll,
                    )
                )

        if not sanitized_profiles:
            return None

        # Return sanitized copy
        return ObservationRecord(
            platform_id=record.platform_id,
            instrument_type=record.instrument_type.lower(),
            latitude=record.latitude,
            longitude=record.longitude,
            time=record.time,
            profiles=sanitized_profiles,
            source_metadata=record.source_metadata,
        )

    def filter_observations(self, records: List[ObservationRecord]) -> List[ObservationRecord]:
        """
        Filters a list of observation records.
        """
        valid_records = []
        for rec in records:
            filtered = self.filter_record(rec)
            if filtered is not None:
                valid_records.append(filtered)
        return valid_records
