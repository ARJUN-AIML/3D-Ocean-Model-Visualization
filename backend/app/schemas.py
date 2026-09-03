"""
backend/app/schemas.py
Pydantic API schemas matching frontend domain types (frontend/types/ocean.ts).
Enforces camelCase output to match TypeScript contracts while providing clean adapter integration.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    is_real_data_connected: bool = True
    provenance_mode: str = "SYNTHETIC DEMO DATASET (FastAPI Connected)"
    message: str = "OceanTwin 3D FastAPI Backend Operational"


class ProvenanceInfo(BaseModel):
    dataset_type: str = "synthetic"
    source: str = "OceanTwin Synthetic Demo Dataset"
    dataset_id: str = "02_ocean_model_grid"
    timestamp: Optional[str] = None
    depth_m: Optional[float] = None
    region: Optional[str] = None


class DatasetSummary(BaseModel):
    id: str
    name: str
    description: str
    grid_type: str = "regular"
    spatial_bounds: Dict[str, float]
    depth_levels: List[float]
    time_steps: List[str]
    variables: List[str]
    provenance: Optional[ProvenanceInfo] = None


class SliceResponse(BaseModel):
    datasetId: str
    variable: str
    depth: float
    time: str
    minVal: float
    maxVal: float
    units: str
    latitudes: List[float]
    longitudes: List[float]
    values: List[List[Optional[float]]]
    provenance: Optional[ProvenanceInfo] = None


class VectorPoint(BaseModel):
    lat: float
    lon: float
    u: float
    v: float
    speed: float
    directionDeg: float


class VectorsResponse(BaseModel):
    datasetId: str
    depth: float
    time: str
    vectorCount: int
    vectors: List[VectorPoint]
    provenance: Optional[ProvenanceInfo] = None


class WaveSamplePoint(BaseModel):
    lat: float
    lon: float
    timestamp: str
    significantWaveHeightM: float
    peakWavePeriodS: float
    meanWaveDirectionDeg: float


class WaveResponse(BaseModel):
    datasetId: str = "06_wave_samples"
    count: int
    waves: List[WaveSamplePoint]
    provenance: Optional[ProvenanceInfo] = None


class ArgoProfilePoint(BaseModel):
    depth: float
    temperature: float
    salinity: float


class ArgoFloatResponse(BaseModel):
    id: str
    wmoNumber: str
    name: str
    lat: float
    lon: float
    depth: float
    surfaceTemp: float
    surfaceSalinity: float
    observationTime: str
    qualityStatus: str  # 'PASSED' | 'FLAGGED' | 'UNCERTAIN'
    platformType: str = "ARGO_FLOAT"  # 'ARGO_FLOAT' | 'MOORED_BUOY' | 'SYNTHETIC_BUOY'
    profileData: List[ArgoProfilePoint]
    provenance: Optional[ProvenanceInfo] = None


class LocationPropertiesResponse(BaseModel):
    available: bool = True
    reason: Optional[str] = None
    requestedLat: float
    requestedLon: float
    resolvedLat: float
    resolvedLon: float
    distanceKm: float
    requestedDepth: float
    resolvedDepth: float
    requestedTime: str
    resolvedTime: str
    timeGapHours: float
    interpolated: bool = False
    regionName: str
    
    # Ocean State
    temperatureC: Optional[float] = None
    salinityPsu: Optional[float] = None
    
    # Currents
    uMs: Optional[float] = None
    vMs: Optional[float] = None
    currentSpeedMps: Optional[float] = None
    
    # Waves
    significantWaveHeightM: Optional[float] = None
    peakWavePeriodS: Optional[float] = None
    meanWaveDirectionDeg: Optional[float] = None
    waveDirectionConvention: Optional[str] = "FROM_DIRECTION (0=North, 90=East, 180=South, 270=West)"
    
    # Anomaly & Bias
    zScore: Optional[float] = None
    anomalyStatus: Optional[str] = None
    rawModelTemp: Optional[float] = None
    predictedBiasTemp: Optional[float] = None
    correctedModelTemp: Optional[float] = None
    
    # Profile Data
    profileData: List[ArgoProfilePoint] = []
    
    # Station Info
    nearestStationId: Optional[str] = None
    nearestStationDistanceKm: Optional[float] = None
    platformType: Optional[str] = None  # 'ARGO_FLOAT' | 'MOORED_BUOY' | 'SYNTHETIC_BUOY'
    
    reliability: str = "HIGH"
    provenance: Optional[ProvenanceInfo] = None


class ModelObsMatchResponse(BaseModel):
    floatId: str
    variable: str  # 'temp' | 'salinity' | 'currents' | 'waves'
    modelValue: float
    observedValue: float
    difference: float
    spatialDistanceKm: float
    timeDifferenceHours: float
    depthDifferenceM: float
    qualityStatus: str  # 'EXCELLENT' | 'GOOD' | 'MARGINAL'
    provenance: Optional[ProvenanceInfo] = None


class BiasPredictionApiRequest(BaseModel):
    targetVariable: str = Field("temp", description="temp | salinity")
    sensorType: str = Field("argo", description="argo | glider | ctd")
    modelTemperature: float = 28.5
    modelSalinity: Optional[float] = 35.0
    modelU: Optional[float] = 0.15
    modelV: Optional[float] = -0.05
    depth: float = 10.0
    latitude: float = 15.42
    longitude: float = 68.12
    timestamp: Optional[str] = None


class BiasCorrectionResponse(BaseModel):
    region: str
    variable: str
    depth: float
    rawValue: float
    correctedValue: float
    observationValue: float
    rawError: float
    correctedError: float
    improvementPct: float
    mlModelName: str
    provenance: Optional[ProvenanceInfo] = None


class RawAndCorrectedMetrics(BaseModel):
    mae: float
    rmse: float
    bias: float
    r2: float
    pearson: float
    matchCount: int


class ValidationMetricsResponse(BaseModel):
    variable: str
    region: str
    mae: float
    rmse: float
    bias: float
    r2: float
    pearson: float
    matchedObservations: int
    rejectedObservations: int
    coveragePct: float
    reliability: str
    isBackendConnected: bool = True
    rawModel: Optional[RawAndCorrectedMetrics] = None
    correctedModel: Optional[RawAndCorrectedMetrics] = None
    evaluationSplit: str = "held-out test split"
    provenance: Optional[ProvenanceInfo] = None


class ReliabilityFactor(BaseModel):
    name: str
    status: str
    description: str


class ReliabilityDataResponse(BaseModel):
    overallStatus: str
    score: float
    factors: List[ReliabilityFactor]
    provenance: Optional[ProvenanceInfo] = None


class OceanAnomalyResponse(BaseModel):
    id: str
    variable: str
    locationName: str
    lat: float
    lon: float
    depth: float
    timestamp: str
    currentValue: float
    baselineValue: float
    deviation: float
    zScore: float
    severity: str
    provenance: Optional[ProvenanceInfo] = None


class ErrorHeatmapPointResponse(BaseModel):
    lat: float
    lon: float
    depthM: float
    timestamp: str
    modelValue: float
    observedValue: float
    rawError: float
    correctedModelValue: Optional[float] = None
    correctedError: Optional[float] = None
    error: float
    absoluteError: float
    variable: str
    mode: str


class ErrorHeatmapStatistics(BaseModel):
    matchCount: int
    mae: float
    rmse: float
    bias: float


class ErrorHeatmapResponse(BaseModel):
    variable: str
    mode: str
    errorConvention: str = "observation_minus_model"
    requestedDepthM: float
    resolvedDepthM: float
    points: List[ErrorHeatmapPointResponse]
    statistics: ErrorHeatmapStatistics
    provenance: Optional[ProvenanceInfo] = None


class TrajectorySimRequest(BaseModel):
    startLat: float
    startLon: float
    durationHours: int = Field(24, description="6 | 12 | 24 | 48")


class TrajectoryPoint(BaseModel):
    lat: float
    lon: float
    elapsedHours: float
    speedKts: float
    depthM: float


class TrajectoryResultResponse(BaseModel):
    startLat: float
    startLon: float
    startLocationName: str
    durationHours: int
    path: List[TrajectoryPoint]
    endLat: float
    endLon: float
    totalDistanceKm: float
    averageSpeedMps: float
    statusText: str
    provenance: Optional[ProvenanceInfo] = None


class RegionalInsightResponse(BaseModel):
    regionName: str
    bounds: Dict[str, float]
    meanTemperature: float
    meanSalinity: float
    meanCurrentSpeed: float
    anomalyCount: int
    reliability: str
    summary: str
    isLlmConnected: bool = False
    provenance: Optional[ProvenanceInfo] = None

