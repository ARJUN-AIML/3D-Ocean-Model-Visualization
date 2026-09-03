export type OceanVariable = 'temp' | 'salinity' | 'currents' | 'waves';

export type DepthLevel = 0 | 10 | 50 | 100 | 500 | 1000 | 2000;

export type ReliabilityStatus = 'HIGH' | 'MODERATE' | 'LOW' | 'INSUFFICIENT DATA';

export type AnomalySeverity = 'NORMAL' | 'WATCH' | 'WARNING' | 'CRITICAL';

export type DataProvenanceMode = 
  | 'DEMO / MOCK DATA' 
  | 'REAL DATA' 
  | 'OFFLINE PRE-DOWNLOADED' 
  | 'SYNTHETIC DATA' 
  | 'UNKNOWN / NOT CONNECTED'
  | string;

export type ActiveDrawerView = 
  | 'none'
  | 'argo'
  | 'validation'
  | 'bias'
  | 'anomaly'
  | 'trajectory'
  | 'explain'
  | 'report'
  | 'reliability';

export interface ArgoProfilePoint {
  depth: number; // meters
  temperature: number; // °C
  salinity: number; // PSU
}

export interface ArgoFloat {
  id: string;
  wmoNumber: string;
  name: string;
  lat: number;
  lon: number;
  depth: number;
  surfaceTemp: number;
  surfaceSalinity: number;
  observationTime: string;
  qualityStatus: 'PASSED' | 'FLAGGED' | 'UNCERTAIN';
  platformType?: 'ARGO_FLOAT' | 'MOORED_BUOY' | 'SYNTHETIC_BUOY';
  profileData: ArgoProfilePoint[];
}

export interface LocationPropertiesResponse {
  available: boolean;
  reason?: string | null;
  requestedLat: number;
  requestedLon: number;
  resolvedLat: number;
  resolvedLon: number;
  distanceKm: number;
  requestedDepth: number;
  resolvedDepth: number;
  requestedTime: string;
  resolvedTime: string;
  timeGapHours: number;
  interpolated: boolean;
  regionName: string;
  temperatureC?: number | null;
  salinityPsu?: number | null;
  uMs?: number | null;
  vMs?: number | null;
  currentSpeedMps?: number | null;
  significantWaveHeightM?: number | null;
  peakWavePeriodS?: number | null;
  meanWaveDirectionDeg?: number | null;
  waveDirectionConvention?: string | null;
  zScore?: number | null;
  anomalyStatus?: string | null;
  rawModelTemp?: number | null;
  predictedBiasTemp?: number | null;
  correctedModelTemp?: number | null;
  profileData?: ArgoProfilePoint[];
  nearestStationId?: string | null;
  nearestStationDistanceKm?: number | null;
  platformType?: 'ARGO_FLOAT' | 'MOORED_BUOY' | 'SYNTHETIC_BUOY' | null;
  reliability?: string;
  provenance?: any;
}

export interface ModelObsMatch {
  floatId: string;
  variable: OceanVariable;
  modelValue: number;
  observedValue: number;
  difference: number;
  spatialDistanceKm: number;
  timeDifferenceHours: number;
  depthDifferenceM: number;
  qualityStatus: 'EXCELLENT' | 'GOOD' | 'MARGINAL';
}

export interface BiasCorrectionData {
  region: string;
  variable: OceanVariable;
  depth: DepthLevel;
  rawValue: number;
  correctedValue: number;
  observationValue: number;
  rawError: number;
  correctedError: number;
  improvementPct: number;
  mlModelName: string; // e.g. "XGBoost v2.1 (Backend Pending)"
}

export interface ValidationMetrics {
  variable: OceanVariable;
  region: string;
  mae: number; // Mean Absolute Error
  rmse: number; // Root Mean Square Error
  bias: number; // Mean Bias
  r2: number; // R-squared
  pearson: number; // Pearson correlation
  matchedObservations: number;
  rejectedObservations: number;
  coveragePct: number;
  reliability: ReliabilityStatus;
  isBackendConnected: boolean;
}

export interface ReliabilityFactor {
  name: string;
  status: 'OPTIMAL' | 'FAIR' | 'POOR';
  description: string;
}

export interface ReliabilityData {
  overallStatus: ReliabilityStatus;
  score: number; // 0 - 100 placeholder
  factors: ReliabilityFactor[];
}

export interface ErrorHeatmapPoint {
  lat: number;
  lon: number;
  rawError: number;
  correctedError: number;
}

export interface OceanAnomaly {
  id: string;
  variable: OceanVariable;
  locationName: string;
  lat: number;
  lon: number;
  depth: DepthLevel;
  timestamp: string;
  currentValue: number;
  baselineValue: number;
  deviation: number;
  zScore: number;
  severity: AnomalySeverity;
}

export interface CurrentVector {
  lat: number;
  lon: number;
  u: number; // Eastward velocity component (m/s)
  v: number; // Northward velocity component (m/s)
  speed: number; // m/s
  directionDeg: number; // 0-360 degrees
}

export interface TrajectoryPoint {
  lat: number;
  lon: number;
  elapsedHours: number;
  speedKts: number;
  depthM: number;
}

export interface TrajectoryResult {
  startLat: number;
  startLon: number;
  startLocationName: string;
  durationHours: 6 | 12 | 24 | 48;
  path: TrajectoryPoint[];
  endLat: number;
  endLon: number;
  totalDistanceKm: number;
  averageSpeedMps: number;
  statusText: string;
}

export interface RegionalInsight {
  regionName: string;
  bounds: { minLat: number; maxLat: number; minLon: number; maxLon: number };
  meanTemperature: number;
  meanSalinity: number;
  meanCurrentSpeed: number;
  anomalyCount: number;
  reliability: ReliabilityStatus;
  summary: string;
  isLlmConnected: boolean;
}

export interface LayerVisibilityState {
  oceanDataGrid: boolean;
  argoFloats: boolean;
  currentParticles: boolean;
  errorHeatmap: boolean;
  anomalies: boolean;
  reliabilityOverlay: boolean;
  trajectoryPath: boolean;
}

export interface SelectedLocationState {
  lat: number;
  lon: number;
  regionName: string;
  seaDepthM: number;
}
