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
  ErrorHeatmapPoint,
  ErrorHeatmapResponse,
  LocationPropertiesResponse
} from '../../types/ocean';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function fetchFromApi<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
      ...options,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`[OceanAPI] Failed to fetch from endpoint ${endpoint}:`, err);
    return null;
  }
}

/**
 * Frontend Service / API Boundary Layer
 * Enforces API connectivity to FastAPI backend at localhost:8000 without silent mock fallbacks.
 */
export const oceanApiService = {
  getProvenanceStatus: async () => {
    const health = await fetchFromApi<{ status: string; provenance_mode?: string }>(`/api/health`);
    if (health && health.status === 'ok') {
      const modeStr = health.provenance_mode || 'FASTAPI BACKEND · DEMO DATA';
      return {
        mode: modeStr as string,
        notice: 'Connected to live FastAPI Backend (Active Synthetic Demo Dataset).',
        isRealDataConnected: true
      };
    }
    return {
      mode: 'DATA UNAVAILABLE' as const,
      notice: 'Backend API Unreachable — Check http://localhost:8000',
      isRealDataConnected: false
    };
  },

  getArgoFloats: async (): Promise<ArgoFloat[]> => {
    const data = await fetchFromApi<ArgoFloat[]>(`/api/observations?instrument_type=argo`);
    return data || [];
  },

  getArgoFloatById: async (id: string): Promise<ArgoFloat | undefined> => {
    const data = await fetchFromApi<ArgoFloat>(`/api/observations/${encodeURIComponent(id)}/profile`);
    return data || undefined;
  },

  getModelObsMatch: async (floatId: string, variable: OceanVariable): Promise<ModelObsMatch | null> => {
    const data = await fetchFromApi<ModelObsMatch>(`/api/model-obs-match?float_id=${encodeURIComponent(floatId)}&variable=${encodeURIComponent(variable)}`);
    return data;
  },

  getBiasCorrectionData: async (variable: OceanVariable, depth: DepthLevel): Promise<BiasCorrectionData | null> => {
    const reqBody = {
      targetVariable: variable,
      sensorType: 'argo',
      modelTemperature: 28.5,
      modelSalinity: 35.5,
      modelU: 0.15,
      modelV: -0.05,
      depth: typeof depth === 'number' ? depth : 0,
      latitude: 15.42,
      longitude: 68.12
    };
    const data = await fetchFromApi<BiasCorrectionData>(`/api/bias/predict`, {
      method: 'POST',
      body: JSON.stringify(reqBody)
    });
    return data;
  },

  getValidationMetrics: async (variable: OceanVariable): Promise<ValidationMetrics | null> => {
    const data = await fetchFromApi<ValidationMetrics>(`/api/validation/metrics?variable=${encodeURIComponent(variable)}`);
    return data;
  },

  getReliabilityData: async (): Promise<ReliabilityData | null> => {
    const data = await fetchFromApi<ReliabilityData>(`/api/reliability`);
    return data;
  },

  getAnomalies: async (variable?: OceanVariable): Promise<OceanAnomaly[]> => {
    const data = await fetchFromApi<OceanAnomaly[]>(`/api/anomalies${variable ? `?variable=${variable}` : ''}`);
    return data || [];
  },

  getErrorHeatmap: async (variable: string = 'temperature', mode: string = 'raw', depth: number = 0, time?: string) => {
    const timeParam = time ? `&time=${encodeURIComponent(time)}` : '';
    const data = await fetchFromApi<ErrorHeatmapResponse>(`/api/heatmap?variable=${variable}&mode=${mode}&depth=${depth}${timeParam}`);
    return data;
  },

  getWaveData: async () => {
    const data = await fetchFromApi<any>(`/api/waves`);
    return data;
  },

  runTrajectorySimulation: async (
    startLat: number,
    startLon: number,
    durationHours: 6 | 12 | 24 | 48
  ): Promise<TrajectoryResult | null> => {
    const data = await fetchFromApi<TrajectoryResult>(`/api/trajectory?startLat=${startLat}&startLon=${startLon}&durationHours=${durationHours}`, {
      method: 'POST'
    });
    return data;
  },

  getRegionalInsight: async (lat: number, lon: number): Promise<RegionalInsight | null> => {
    const data = await fetchFromApi<RegionalInsight>(`/api/insight?lat=${lat}&lon=${lon}`);
    return data;
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
    return [];
  },

  getDatasets: async () => {
    const data = await fetchFromApi<any>(`/api/datasets`);
    if (data) {
      if (Array.isArray(data)) return data;
      if (Array.isArray(data.datasets)) return data.datasets;
    }
    return [];
  },

  getDatasetSlice: async (datasetId: string = '02_ocean_model_grid', variable: OceanVariable = 'temp', depth: number = 0, timeIndex: number = 0) => {
    const data = await fetchFromApi<{
      datasetId: string;
      variable: string;
      depth: number;
      time: string;
      values: (number | null)[][];
      latitudes: number[];
      longitudes: number[];
      minVal: number;
      maxVal: number;
      units: string;
      provenance?: any;
    }>(`/api/datasets/${datasetId}/slice?variable=${variable}&depth=${depth}&time=${timeIndex}`);
    return data;
  },

  getReport: async (region: string = 'Arabian Sea', lat: number = 15.42, lon: number = 68.12) => {
    const data = await fetchFromApi<any>(`/api/report?region=${encodeURIComponent(region)}&lat=${lat}&lon=${lon}`);
    return data;
  },

  getLocationProperties: async (lat: number, lon: number, depth: number = 0, time?: string) => {
    const timeParam = time ? `&time=${encodeURIComponent(time)}` : '';
    const data = await fetchFromApi<LocationPropertiesResponse>(`/api/location-properties?lat=${lat}&lon=${lon}&depth=${depth}${timeParam}`);
    return data;
  }
};
