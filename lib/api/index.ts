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
  DEMO_DATA_NOTICE
} from '../../mocks/oceanDemoData';

/**
 * Frontend Service / API Boundary Layer
 * 
 * IMPORTANT: Currently returns typed DEMO / MOCK datasets.
 * In the future, these methods will connect to actual FastAPI endpoints.
 */

export const oceanApiService = {
  getProvenanceStatus: async () => {
    return {
      mode: 'DEMO / MOCK DATA' as const,
      notice: DEMO_DATA_NOTICE,
      isRealDataConnected: false
    };
  },

  getArgoFloats: async (): Promise<ArgoFloat[]> => {
    // Simulated async API call
    return DEMO_ARGO_FLOATS;
  },

  getArgoFloatById: async (id: string): Promise<ArgoFloat | undefined> => {
    return DEMO_ARGO_FLOATS.find(f => f.id === id || f.wmoNumber === id);
  },

  getModelObsMatch: async (floatId: string, variable: OceanVariable): Promise<ModelObsMatch> => {
    return {
      ...DEMO_MODEL_OBS_MATCH,
      floatId,
      variable
    };
  },

  getBiasCorrectionData: async (variable: OceanVariable, depth: DepthLevel): Promise<BiasCorrectionData> => {
    return {
      ...DEMO_BIAS_CORRECTION,
      variable,
      depth
    };
  },

  getValidationMetrics: async (variable: OceanVariable): Promise<ValidationMetrics> => {
    return {
      ...DEMO_VALIDATION_METRICS,
      variable
    };
  },

  getReliabilityData: async (): Promise<ReliabilityData> => {
    return DEMO_RELIABILITY_DATA;
  },

  getAnomalies: async (): Promise<OceanAnomaly[]> => {
    return DEMO_ANOMALIES;
  },

  getErrorHeatmap: async (): Promise<ErrorHeatmapPoint[]> => {
    return DEMO_ERROR_HEATMAP;
  },

  runTrajectorySimulation: async (
    startLat: number,
    startLon: number,
    durationHours: 6 | 12 | 24 | 48
  ): Promise<TrajectoryResult> => {
    return DEMO_TRAJECTORY_SIMULATION(startLat, startLon, durationHours);
  },

  getRegionalInsight: async (lat: number, lon: number): Promise<RegionalInsight> => {
    return {
      ...DEMO_REGIONAL_INSIGHT,
      regionName: `Location (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`
    };
  }
};
