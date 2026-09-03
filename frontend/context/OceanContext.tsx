'use client';

import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import {
  OceanVariable,
  DepthLevel,
  LayerVisibilityState,
  ActiveDrawerView,
  ArgoFloat,
  OceanAnomaly,
  SelectedLocationState,
  TrajectoryResult,
  DataProvenanceMode,
  LocationPropertiesResponse
} from '../types/ocean';

import { oceanApiService } from '../lib/api';

interface OceanContextType {
  // Dataset state
  selectedDatasetId: string;
  setSelectedDatasetId: (id: string) => void;
  datasets: any[];
  availableTimeSteps: string[];
  availableDepths: number[];
  availableVariables: string[];

  // Variable & Depth state
  selectedVariable: OceanVariable;
  setSelectedVariable: (variable: OceanVariable) => void;
  selectedDepth: DepthLevel;
  setSelectedDepth: (depth: DepthLevel) => void;

  // Time & Playback state
  timeIndex: number;
  setTimeIndex: (index: number) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  playbackSpeed: number;
  setPlaybackSpeed: (speed: number) => void;
  formattedCurrentTime: string;

  // Layer Visibility
  layers: LayerVisibilityState;
  toggleLayer: (layerName: keyof LayerVisibilityState) => void;
  setLayerState: (layerName: keyof LayerVisibilityState, enabled: boolean) => void;

  // Drawer navigation
  activeDrawer: ActiveDrawerView;
  setActiveDrawer: (drawer: ActiveDrawerView) => void;
  closeDrawer: () => void;

  // Selections
  selectedArgo: ArgoFloat | null;
  setSelectedArgo: (argo: ArgoFloat | null) => void;
  selectedAnomaly: OceanAnomaly | null;
  setSelectedAnomaly: (anomaly: OceanAnomaly | null) => void;
  selectedLocation: SelectedLocationState;
  setSelectedLocation: (loc: SelectedLocationState) => void;

  // Trajectory Simulation Mode
  trajectoryModeActive: boolean;
  setTrajectoryModeActive: (active: boolean) => void;
  trajectoryDuration: 6 | 12 | 24 | 48;
  setTrajectoryDuration: (dur: 6 | 12 | 24 | 48) => void;
  activeTrajectory: TrajectoryResult | null;
  setActiveTrajectory: (result: TrajectoryResult | null) => void;

  // Camera preset flyTo & Zoom target
  cameraFlyTarget: { lat: number; lon: number; height: number; pitch?: number; heading?: number } | null;
  flyToLocation: (lat: number, lon: number, height?: number, pitch?: number, heading?: number) => void;
  clearFlyTarget: () => void;
  zoomAction: 'in' | 'out' | 'reset' | null;
  zoomIn: () => void;
  zoomOut: () => void;
  resetView: () => void;
  clearZoomAction: () => void;

  // Auto Rotate mode
  autoRotate: boolean;
  setAutoRotate: (autoRotate: boolean) => void;
  toggleAutoRotate: () => void;

  // Data Provenance Mode
  provenanceMode: DataProvenanceMode;

  // Location Inspection & Drifter Telemetry
  locationProperties: LocationPropertiesResponse | null;
  setLocationProperties: (props: LocationPropertiesResponse | null) => void;
  isLocationInspecting: boolean;
  fetchLocationProperties: (lat: number, lon: number, depth?: number, time?: string) => Promise<void>;
  drifterTelemetry: {
    lat: number;
    lon: number;
    speedKts: number;
    elapsedHours: number;
    totalDistanceKm: number;
    waveHeightM?: number | null;
  } | null;
  setDrifterTelemetry: (telemetry: {
    lat: number;
    lon: number;
    speedKts: number;
    elapsedHours: number;
    totalDistanceKm: number;
    waveHeightM?: number | null;
  } | null) => void;

  // UI state
  leftControlsOpen: boolean;
  setLeftControlsOpen: (open: boolean) => void;
}

const defaultLayers: LayerVisibilityState = {
  oceanDataGrid: true,
  argoFloats: true,
  currentParticles: true,
  errorHeatmap: false,
  anomalies: true,
  reliabilityOverlay: false,
  trajectoryPath: true,
};

const OceanContext = createContext<OceanContextType | undefined>(undefined);

export const OceanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('02_ocean_model_grid');
  const [selectedVariable, setSelectedVariable] = useState<OceanVariable>('temp');
  const [selectedDepth, setSelectedDepth] = useState<DepthLevel>(0);

  const [availableTimeSteps, setAvailableTimeSteps] = useState<string[]>([
    "2026-08-23T00:00:00Z",
    "2026-08-23T06:00:00Z",
    "2026-08-23T12:00:00Z",
    "2026-08-23T18:00:00Z",
  ]);
  const [availableDepths, setAvailableDepths] = useState<number[]>([0, 10, 25, 50, 100, 250, 500, 1000]);
  const [availableVariables, setAvailableVariables] = useState<string[]>(["temp", "salinity", "currents", "waves"]);

  const [timeIndex, setTimeIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);

  const [layers, setLayers] = useState<LayerVisibilityState>(defaultLayers);
  const [activeDrawer, setActiveDrawer] = useState<ActiveDrawerView>('none');

  const [selectedArgo, setSelectedArgo] = useState<ArgoFloat | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<OceanAnomaly | null>(null);

  const [selectedLocation, setSelectedLocation] = useState<SelectedLocationState>({
    lat: 15.42,
    lon: 68.12,
    regionName: 'Arabian Sea / Central Indian Ocean',
    seaDepthM: 3420
  });

  const [trajectoryModeActive, setTrajectoryModeActive] = useState<boolean>(false);
  const [trajectoryDuration, setTrajectoryDuration] = useState<6 | 12 | 24 | 48>(24);
  const [activeTrajectory, setActiveTrajectory] = useState<TrajectoryResult | null>(null);

  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const toggleAutoRotate = useCallback(() => setAutoRotate(prev => !prev), []);

  const [cameraFlyTarget, setCameraFlyTarget] = useState<{ lat: number; lon: number; height: number; pitch?: number; heading?: number } | null>(null);
  const [leftControlsOpen, setLeftControlsOpen] = useState<boolean>(true);

  const [provenanceMode, setProvenanceMode] = useState<DataProvenanceMode>('DEMO / MOCK DATA');

  const [locationProperties, setLocationProperties] = useState<LocationPropertiesResponse | null>(null);
  const [isLocationInspecting, setIsLocationInspecting] = useState<boolean>(false);
  const [drifterTelemetry, setDrifterTelemetry] = useState<{
    lat: number;
    lon: number;
    speedKts: number;
    elapsedHours: number;
    totalDistanceKm: number;
    waveHeightM?: number | null;
  } | null>(null);

  const fetchLocationProperties = useCallback(async (lat: number, lon: number, depth: number = 0, time?: string) => {
    setIsLocationInspecting(true);
    const props = await oceanApiService.getLocationProperties(lat, lon, depth, time);
    setLocationProperties(props);
    setIsLocationInspecting(false);
  }, []);

  useEffect(() => {
    oceanApiService.getProvenanceStatus().then(status => {
      if (status && status.isRealDataConnected) {
        setProvenanceMode(status.mode as DataProvenanceMode);
      }
    });

    oceanApiService.getDatasets().then(list => {
      if (list && list.length > 0) {
        setDatasets(list);
        const activeDs = list[0];
        if (activeDs.id) {
          setSelectedDatasetId(activeDs.id);
        }
        if (activeDs.time_steps && Array.isArray(activeDs.time_steps) && activeDs.time_steps.length > 0) {
          setAvailableTimeSteps(activeDs.time_steps);
        }
        if (activeDs.depth_levels && Array.isArray(activeDs.depth_levels) && activeDs.depth_levels.length > 0) {
          setAvailableDepths(activeDs.depth_levels);
        }
        if (activeDs.variables && Array.isArray(activeDs.variables) && activeDs.variables.length > 0) {
          setAvailableVariables(activeDs.variables);
        }
      }
    });
  }, []);

  // Time playback ticker
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && availableTimeSteps.length > 0) {
      interval = setInterval(() => {
        setTimeIndex((prev) => (prev + 1) % availableTimeSteps.length);
      }, 2000 / playbackSpeed);
    }
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, availableTimeSteps]);

  const resetView = useCallback(() => {
    setZoomAction('reset');
    setCameraFlyTarget({ lat: -2.0, lon: 78.0, height: 6500000, pitch: -45, heading: 0 });
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.key === 'r' || e.key === 'R') {
        if (!e.ctrlKey && !e.metaKey) {
          resetView();
        }
      } else if (e.key === 'a' || e.key === 'A') {
        if (!e.ctrlKey && !e.metaKey) {
          setAutoRotate((prev) => !prev);
        }
      } else if (e.key === 'Escape') {
        setActiveDrawer('none');
        setTrajectoryModeActive(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [resetView]);

  useEffect(() => {
    if (typeof window !== 'undefined' && activeDrawer !== 'none') {
      if (window.innerWidth < 1280) {
        setLeftControlsOpen(false);
      }
    }
  }, [activeDrawer]);

  const toggleLayer = useCallback((layerName: keyof LayerVisibilityState) => {
    setLayers(prev => ({ ...prev, [layerName]: !prev[layerName] }));
  }, []);

  const setLayerState = useCallback((layerName: keyof LayerVisibilityState, enabled: boolean) => {
    setLayers(prev => ({ ...prev, [layerName]: enabled }));
  }, []);

  const [zoomAction, setZoomAction] = useState<'in' | 'out' | 'reset' | null>(null);

  const zoomIn = useCallback(() => setZoomAction('in'), []);
  const zoomOut = useCallback(() => setZoomAction('out'), []);
  const clearZoomAction = useCallback(() => setZoomAction(null), []);

  const closeDrawer = useCallback(() => {
    setActiveDrawer('none');
  }, []);

  const flyToLocation = useCallback((lat: number, lon: number, height = 3000000, pitch = -40, heading = 0) => {
    setCameraFlyTarget({ lat, lon, height, pitch, heading });
  }, []);

  const clearFlyTarget = useCallback(() => {
    setCameraFlyTarget(null);
  }, []);

  const formattedCurrentTime = useMemo(() => availableTimeSteps[timeIndex] || availableTimeSteps[0] || "2026-08-23T00:00:00Z", [availableTimeSteps, timeIndex]);

  const contextValue = useMemo(() => ({
    selectedDatasetId,
    setSelectedDatasetId,
    datasets,
    availableTimeSteps,
    availableDepths,
    availableVariables,
    selectedVariable,
    setSelectedVariable,
    selectedDepth,
    setSelectedDepth,
    timeIndex,
    setTimeIndex,
    isPlaying,
    setIsPlaying,
    playbackSpeed,
    setPlaybackSpeed,
    formattedCurrentTime,
    layers,
    toggleLayer,
    setLayerState,
    activeDrawer,
    setActiveDrawer,
    closeDrawer,
    selectedArgo,
    setSelectedArgo,
    selectedAnomaly,
    setSelectedAnomaly,
    selectedLocation,
    setSelectedLocation,
    trajectoryModeActive,
    setTrajectoryModeActive,
    trajectoryDuration,
    setTrajectoryDuration,
    activeTrajectory,
    setActiveTrajectory,
    cameraFlyTarget,
    flyToLocation,
    clearFlyTarget,
    zoomAction,
    zoomIn,
    zoomOut,
    resetView,
    clearZoomAction,
    autoRotate,
    setAutoRotate,
    toggleAutoRotate,
    provenanceMode,
    leftControlsOpen,
    setLeftControlsOpen
  }), [
    selectedDatasetId,
    datasets,
    availableTimeSteps,
    availableDepths,
    availableVariables,
    selectedVariable,
    selectedDepth,
    timeIndex,
    isPlaying,
    playbackSpeed,
    formattedCurrentTime,
    layers,
    toggleLayer,
    setLayerState,
    activeDrawer,
    closeDrawer,
    selectedArgo,
    selectedAnomaly,
    selectedLocation,
    trajectoryModeActive,
    trajectoryDuration,
    activeTrajectory,
    cameraFlyTarget,
    flyToLocation,
    clearFlyTarget,
    zoomAction,
    zoomIn,
    zoomOut,
    resetView,
    clearZoomAction,
    autoRotate,
    toggleAutoRotate,
    provenanceMode,
    leftControlsOpen
  ]);

  return (
    <OceanContext.Provider value={contextValue}>
      {children}
    </OceanContext.Provider>
  );
};

export const useOcean = () => {
  const context = useContext(OceanContext);
  if (!context) {
    throw new Error('useOcean must be used within an OceanProvider');
  }
  return context;
};
