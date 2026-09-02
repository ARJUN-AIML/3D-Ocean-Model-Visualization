import {
  ArgoFloat,
  OceanVariable,
  DepthLevel,
  ValidationMetrics,
  BiasCorrectionData,
  ReliabilityData,
  OceanAnomaly,
  TrajectoryResult,
  RegionalInsight,
  ModelObsMatch,
  ErrorHeatmapPoint
} from '../../types/ocean';

import {
  DEMO_ARGO_FLOATS,
  DEMO_VALIDATION_METRICS,
  DEMO_BIAS_CORRECTION,
  DEMO_RELIABILITY_DATA,
  DEMO_ANOMALIES,
  DEMO_TRAJECTORY_SIMULATION,
  DEMO_REGIONAL_INSIGHT,
  DEMO_MODEL_OBS_MATCH,
  DEMO_ERROR_HEATMAP,
  DEMO_CURRENT_VECTORS,
  DEMO_DATA_NOTICE
} from '../../mocks/oceanDemoData';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function fetchFromApi<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
      ...options,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    return null;
  }
}

/**
 * Frontend Service / API Boundary Layer
 * 
 * Attempts to communicate with FastAPI REST endpoints at API_BASE_URL.
 * If backend is unavailable or fails, gracefully falls back to typed DEMO / MOCK datasets.
 */
export const oceanApiService = {
  getProvenanceStatus: async () => {
    const health = await fetchFromApi<{ status: string; provenance_mode?: string; dataMode?: string }>(`/api/health`);
    if (health && health.status === 'ok') {
      const modeStr = health.provenance_mode || health.dataMode || 'REAL DATA (FastAPI Connected)';
      return {
        mode: `FASTAPI BACKEND (${modeStr})` as const,
        notice: 'Connected to live FastAPI Scientific & ML Backend API boundary.',
        isRealDataConnected: true
      };
    }
    return {
      mode: 'DEMO / MOCK DATA' as const,
      notice: DEMO_DATA_NOTICE,
      isRealDataConnected: false
    };
  },

  getArgoFloats: async (): Promise<ArgoFloat[]> => {
    const data = await fetchFromApi<ArgoFloat[]>(`/api/observations?instrument_type=argo`);
    if (data && Array.isArray(data) && data.length > 0) return data;
    return DEMO_ARGO_FLOATS;
  },

  getArgoFloatById: async (id: string): Promise<ArgoFloat | undefined> => {
    const data = await fetchFromApi<ArgoFloat>(`/api/observations/${encodeURIComponent(id)}/profile`);
    if (data) return data;
    return DEMO_ARGO_FLOATS.find(f => f.id === id || f.wmoNumber === id);
  },

  getModelObsMatch: async (floatId: string, variable: OceanVariable): Promise<ModelObsMatch> => {
    const data = await fetchFromApi<ModelObsMatch>(`/api/model-obs-match?float_id=${encodeURIComponent(floatId)}&variable=${encodeURIComponent(variable)}`);
    if (data) return data;
    return {
      ...DEMO_MODEL_OBS_MATCH,
      floatId,
      variable
    };
  },

  getBiasCorrectionData: async (variable: OceanVariable, depth: DepthLevel): Promise<BiasCorrectionData> => {
    const reqBody = {
      targetVariable: variable,
      sensorType: 'argo',
      modelTemperature: 28.5,
      modelSalinity: 35.5,
      modelU: 0.1,
      modelV: 0.2,
      depth: typeof depth === 'number' ? depth : 0,
      latitude: 15.0,
      longitude: 70.0
    };
    const data = await fetchFromApi<BiasCorrectionData>(`/api/bias/predict`, {
      method: 'POST',
      body: JSON.stringify(reqBody)
    });
    if (data) return data;
    return {
      ...DEMO_BIAS_CORRECTION,
      variable,
      depth
    };
  },

  getValidationMetrics: async (variable: OceanVariable): Promise<ValidationMetrics> => {
    const data = await fetchFromApi<ValidationMetrics>(`/api/validation/metrics?variable=${encodeURIComponent(variable)}`);
    if (data) return data;
    return {
      ...DEMO_VALIDATION_METRICS,
      variable
    };
  },

  getReliabilityData: async (): Promise<ReliabilityData> => {
    const data = await fetchFromApi<ReliabilityData>(`/api/reliability`);
    if (data) return data;
    return DEMO_RELIABILITY_DATA;
  },

  getAnomalies: async (): Promise<OceanAnomaly[]> => {
    const data = await fetchFromApi<OceanAnomaly[]>(`/api/anomalies`);
    if (data && Array.isArray(data)) return data;
    return DEMO_ANOMALIES;
  },

  getErrorHeatmap: async (): Promise<ErrorHeatmapPoint[]> => {
    const data = await fetchFromApi<ErrorHeatmapPoint[]>(`/api/heatmap`);
    if (data && Array.isArray(data)) return data;
    return DEMO_ERROR_HEATMAP;
  },

  runTrajectorySimulation: async (
    startLat: number,
    startLon: number,
    durationHours: 6 | 12 | 24 | 48
  ): Promise<TrajectoryResult> => {
    const data = await fetchFromApi<TrajectoryResult>(`/api/trajectory?startLat=${startLat}&startLon=${startLon}&durationHours=${durationHours}`, {
      method: 'POST'
    });
    if (data) return data;
    return DEMO_TRAJECTORY_SIMULATION(startLat, startLon, durationHours);
  },

  getRegionalInsight: async (lat: number, lon: number): Promise<RegionalInsight> => {
    const data = await fetchFromApi<RegionalInsight>(`/api/insight?lat=${lat}&lon=${lon}`);
    if (data) return data;
    return {
      ...DEMO_REGIONAL_INSIGHT,
      regionName: `Location (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`
    };
  },

  getCurrentVectors: async (datasetId: string = 'default', depth: number = 0, timeIndex: number = 0, stride: number = 1) => {
    const data = await fetchFromApi<{
      datasetId: string;
      depth: number;
      time: string;
      vectorCount: number;
      vectors: { lat: number; lon: number; u: number; v: number; speed: number; directionDeg: number }[];
    }>(`/api/datasets/${datasetId}/vectors?depth=${depth}&time=${timeIndex}&stride=${stride}`);
    if (data && data.vectors && data.vectors.length > 0) {
      return data.vectors;
    }
    return DEMO_CURRENT_VECTORS;
  },

  getDatasets: async () => {
    const data = await fetchFromApi<any>(`/api/datasets`);
    if (data) {
      if (Array.isArray(data)) return data;
      if (Array.isArray(data.datasets)) return data.datasets;
    }
    return [{ id: 'indian_ocean_demo', name: 'Indian Ocean Regional Model (Default)', status: 'SYNTHETIC' }];
  },

  getDatasetSlice: async (datasetId: string = 'default', variable: OceanVariable = 'temp', depth: number = 0, timeIndex: number = 0) => {
    const data = await fetchFromApi<{
      datasetId: string;
      variable: string;
      depth: number;
      time: string;
      grid: { lats: number[]; lons: number[]; values: number[][] };
    }>(`/api/datasets/${datasetId}/slice?variable=${variable}&depth=${depth}&time=${timeIndex}`);
    return data;
  }
};
