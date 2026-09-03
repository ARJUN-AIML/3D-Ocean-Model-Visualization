import {
  ArgoFloat,
  OceanAnomaly,
  ValidationMetrics,
  BiasCorrectionData,
  ReliabilityData,
  CurrentVector,
  TrajectoryResult,
  RegionalInsight,
  ModelObsMatch,
  ErrorHeatmapPoint
} from '../types/ocean';

// Clearly labeled DEMO / MOCK DATA warning constant
export const DEMO_DATA_NOTICE = "DEMO / MOCK DATA — Backend API & Scientific Engine Not Connected";

export const DEMO_ARGO_FLOATS: ArgoFloat[] = [
  {
    id: "ARGO-5906234",
    wmoNumber: "5906234",
    name: "Arabian Sea Central Station",
    lat: 15.42,
    lon: 68.12,
    depth: 2000,
    surfaceTemp: 28.4,
    surfaceSalinity: 36.2,
    observationTime: "2026-09-02T06:00:00Z",
    qualityStatus: "PASSED",
    profileData: [
      { depth: 0, temperature: 28.4, salinity: 36.2 },
      { depth: 50, temperature: 27.8, salinity: 36.1 },
      { depth: 100, temperature: 24.2, salinity: 35.8 },
      { depth: 200, temperature: 18.5, salinity: 35.4 },
      { depth: 500, temperature: 11.2, salinity: 35.1 },
      { depth: 1000, temperature: 6.8, salinity: 34.9 },
      { depth: 1500, temperature: 4.2, salinity: 34.8 },
      { depth: 2000, temperature: 2.7, salinity: 34.7 }
    ]
  },
  {
    id: "ARGO-2903481",
    wmoNumber: "2903481",
    name: "Bay of Bengal Deep Profiler",
    lat: 12.85,
    lon: 85.40,
    depth: 2000,
    surfaceTemp: 29.1,
    surfaceSalinity: 33.8,
    observationTime: "2026-09-02T05:30:00Z",
    qualityStatus: "PASSED",
    profileData: [
      { depth: 0, temperature: 29.1, salinity: 33.8 },
      { depth: 50, temperature: 28.5, salinity: 34.0 },
      { depth: 100, temperature: 25.1, salinity: 34.9 },
      { depth: 200, temperature: 19.8, salinity: 35.1 },
      { depth: 500, temperature: 12.0, salinity: 35.0 },
      { depth: 1000, temperature: 7.1, salinity: 34.9 },
      { depth: 2000, temperature: 2.9, salinity: 34.7 }
    ]
  },
  {
    id: "ARGO-7901122",
    wmoNumber: "7901122",
    name: "Equatorial Indian Ocean Transect",
    lat: 0.12,
    lon: 78.50,
    depth: 2000,
    surfaceTemp: 29.6,
    surfaceSalinity: 35.1,
    observationTime: "2026-09-01T22:15:00Z",
    qualityStatus: "PASSED",
    profileData: [
      { depth: 0, temperature: 29.6, salinity: 35.1 },
      { depth: 50, temperature: 28.9, salinity: 35.2 },
      { depth: 100, temperature: 23.4, salinity: 35.3 },
      { depth: 200, temperature: 17.1, salinity: 35.2 },
      { depth: 500, temperature: 10.8, salinity: 35.0 },
      { depth: 1000, temperature: 6.4, salinity: 34.8 },
      { depth: 2000, temperature: 2.5, salinity: 34.7 }
    ]
  },
  {
    id: "ARGO-3908841",
    wmoNumber: "3908841",
    name: "Southern Indian Ocean Gyre",
    lat: -22.30,
    lon: 75.10,
    depth: 2000,
    surfaceTemp: 21.5,
    surfaceSalinity: 35.6,
    observationTime: "2026-09-02T02:45:00Z",
    qualityStatus: "PASSED",
    profileData: [
      { depth: 0, temperature: 21.5, salinity: 35.6 },
      { depth: 50, temperature: 21.2, salinity: 35.6 },
      { depth: 100, temperature: 19.5, salinity: 35.7 },
      { depth: 200, temperature: 15.3, salinity: 35.4 },
      { depth: 500, temperature: 9.8, salinity: 34.8 },
      { depth: 1000, temperature: 5.2, salinity: 34.6 },
      { depth: 2000, temperature: 2.2, salinity: 34.7 }
    ]
  },
  {
    id: "ARGO-4902109",
    wmoNumber: "4902109",
    name: "North Atlantic Subpolar Float",
    lat: 56.40,
    lon: -42.10,
    depth: 2000,
    surfaceTemp: 11.4,
    surfaceSalinity: 34.9,
    observationTime: "2026-09-01T18:00:00Z",
    qualityStatus: "PASSED",
    profileData: [
      { depth: 0, temperature: 11.4, salinity: 34.9 },
      { depth: 50, temperature: 11.1, salinity: 34.9 },
      { depth: 100, temperature: 9.8, salinity: 35.0 },
      { depth: 200, temperature: 7.5, salinity: 35.0 },
      { depth: 500, temperature: 4.8, salinity: 34.9 },
      { depth: 1000, temperature: 3.4, salinity: 34.9 },
      { depth: 2000, temperature: 2.1, salinity: 34.8 }
    ]
  }
];

export const DEMO_MODEL_OBS_MATCH: ModelObsMatch = {
  floatId: "ARGO-5906234",
  variable: "temp",
  modelValue: 29.1,
  observedValue: 28.4,
  difference: 0.7,
  spatialDistanceKm: 4.2,
  timeDifferenceHours: 1.5,
  depthDifferenceM: 0.0,
  qualityStatus: "EXCELLENT"
};

export const DEMO_BIAS_CORRECTION: BiasCorrectionData = {
  region: "Arabian Sea",
  variable: "temp",
  depth: 0,
  rawValue: 29.35,
  correctedValue: 28.48,
  observationValue: 28.40,
  rawError: 0.95,
  correctedError: 0.08,
  improvementPct: 91.5,
  mlModelName: "XGBoost Spatial Bias Corrector (Pending API)"
};

export const DEMO_VALIDATION_METRICS: ValidationMetrics = {
  variable: "temp",
  region: "Indian Ocean Basin",
  mae: 0.24,
  rmse: 0.38,
  bias: -0.05,
  r2: 0.94,
  pearson: 0.97,
  matchedObservations: 1420,
  rejectedObservations: 38,
  coveragePct: 97.4,
  reliability: "HIGH",
  isBackendConnected: false
};

export const DEMO_RELIABILITY_DATA: ReliabilityData = {
  overallStatus: "HIGH",
  score: 92,
  factors: [
    { name: "Observation Availability", status: "OPTIMAL", description: "Dense Argo float coverage in active domain." },
    { name: "Observation Quality", status: "OPTIMAL", description: "97% of observations passed quality control." },
    { name: "Spatial Matching Tolerance", status: "OPTIMAL", description: "Matching within 10 km grid resolution." },
    { name: "Temporal Matching", status: "FAIR", description: "Observations within 3 hours window." },
    { name: "Model Error Residuals", status: "OPTIMAL", description: "Low residual variance post ML correction." }
  ]
};

export const DEMO_ANOMALIES: OceanAnomaly[] = [
  {
    id: "ANO-001",
    variable: "temp",
    locationName: "Arabian Sea Marine Heatwave",
    lat: 18.20,
    lon: 64.50,
    depth: 0,
    timestamp: "2026-09-02T00:00:00Z",
    currentValue: 31.2,
    baselineValue: 28.5,
    deviation: 2.7,
    zScore: 3.1,
    severity: "CRITICAL"
  },
  {
    id: "ANO-002",
    variable: "salinity",
    locationName: "Bay of Bengal Freshwater Plume",
    lat: 16.10,
    lon: 89.30,
    depth: 10,
    timestamp: "2026-09-01T12:00:00Z",
    currentValue: 31.0,
    baselineValue: 34.2,
    deviation: -3.2,
    zScore: -2.4,
    severity: "WARNING"
  },
  {
    id: "ANO-003",
    variable: "temp",
    locationName: "Equatorial Upwelling Zone",
    lat: -2.50,
    lon: 60.10,
    depth: 50,
    timestamp: "2026-09-02T03:00:00Z",
    currentValue: 22.1,
    baselineValue: 24.8,
    deviation: -2.7,
    zScore: -1.9,
    severity: "WATCH"
  }
];

export const DEMO_CURRENT_VECTORS: CurrentVector[] = [
  { lat: 10, lon: 65, u: 0.45, v: 0.22, speed: 0.50, directionDeg: 64 },
  { lat: 12, lon: 70, u: 0.60, v: 0.15, speed: 0.62, directionDeg: 76 },
  { lat: 15, lon: 72, u: 0.80, v: -0.30, speed: 0.85, directionDeg: 110 },
  { lat: 8, lon: 80, u: -0.20, v: 0.50, speed: 0.54, directionDeg: 338 },
  { lat: 5, lon: 85, u: -0.70, v: 0.10, speed: 0.71, directionDeg: 278 }
];

export const DEMO_TRAJECTORY_SIMULATION = (startLat: number, startLon: number, duration: 6 | 12 | 24 | 48): TrajectoryResult => {
  const steps = duration === 6 ? 6 : duration === 12 ? 12 : duration === 24 ? 24 : 48;
  const path = [];
  let curLat = startLat;
  let curLon = startLon;
  
  for (let i = 0; i <= steps; i++) {
    const timeOffset = (i / steps) * duration;
    // Drift northeastwards with subtle turbulence
    curLat += 0.04 + Math.sin(i * 0.5) * 0.01;
    curLon += 0.08 + Math.cos(i * 0.5) * 0.02;
    path.push({
      lat: Number(curLat.toFixed(4)),
      lon: Number(curLon.toFixed(4)),
      elapsedHours: timeOffset,
      speedKts: Number((1.2 + Math.sin(i) * 0.3).toFixed(2)),
      depthM: 0
    });
  }

  return {
    startLat,
    startLon,
    startLocationName: `Point (${startLat.toFixed(2)}°, ${startLon.toFixed(2)}°)`,
    durationHours: duration,
    path,
    endLat: path[path.length - 1].lat,
    endLon: path[path.length - 1].lon,
    totalDistanceKm: Number((duration * 2.4).toFixed(1)),
    averageSpeedMps: 0.65,
    statusText: "Current-Based Estimated Trajectory (Demo Simulation)"
  };
};

export const DEMO_REGIONAL_INSIGHT: RegionalInsight = {
  regionName: "Arabian Sea & Western Indian Ocean",
  bounds: { minLat: 0, maxLat: 25, minLon: 50, maxLon: 78 },
  meanTemperature: 28.2,
  meanSalinity: 36.0,
  meanCurrentSpeed: 0.58,
  anomalyCount: 1,
  reliability: "HIGH",
  summary: "The Arabian Sea exhibits seasonally high sea surface temperatures with intense evaporation driving high salinity levels (>36 PSU). Strong southwest monsoon winds generate prominent eastward surface currents.",
  isLlmConnected: false
};

export const DEMO_ERROR_HEATMAP: ErrorHeatmapPoint[] = [
  { lat: 15.0, lon: 65.0, depthM: 0, timestamp: '2026-09-02T00:00:00Z', error: 1.4, absoluteError: 1.4, modelValue: 27.0, observedValue: 28.4, variable: 'temperature', mode: 'raw', rawError: 1.4, correctedError: 0.12 },
  { lat: 16.0, lon: 67.0, depthM: 0, timestamp: '2026-09-02T00:00:00Z', error: 1.8, absoluteError: 1.8, modelValue: 26.8, observedValue: 28.6, variable: 'temperature', mode: 'raw', rawError: 1.8, correctedError: 0.15 },
  { lat: 14.0, lon: 70.0, depthM: 0, timestamp: '2026-09-02T00:00:00Z', error: 0.9, absoluteError: 0.9, modelValue: 27.5, observedValue: 28.4, variable: 'temperature', mode: 'raw', rawError: 0.9, correctedError: 0.08 },
  { lat: 10.0, lon: 75.0, depthM: 0, timestamp: '2026-09-02T00:00:00Z', error: 1.1, absoluteError: 1.1, modelValue: 27.3, observedValue: 28.4, variable: 'temperature', mode: 'raw', rawError: 1.1, correctedError: 0.10 },
  { lat: 12.0, lon: 82.0, depthM: 0, timestamp: '2026-09-02T00:00:00Z', error: 1.6, absoluteError: 1.6, modelValue: 27.2, observedValue: 28.8, variable: 'temperature', mode: 'raw', rawError: 1.6, correctedError: 0.18 }
];
