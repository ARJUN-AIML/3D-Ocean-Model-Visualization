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
  DataProvenanceMode
} from '../types/ocean';

import { DEMO_ARGO_FLOATS, DEMO_ANOMALIES } from '../mocks/oceanDemoData';
import { oceanApiService } from '../lib/api';

interface OceanContextType {
  // Dataset state
  selectedDatasetId: string;
  setSelectedDatasetId: (id: string) => void;
  datasets: any[];

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

const TIME_STEPS = [
  "2026-09-01T00:00:00Z",
  "2026-09-01T06:00:00Z",
  "2026-09-01T12:00:00Z",
  "2026-09-01T18:00:00Z",
  "2026-09-02T00:00:00Z",
  "2026-09-02T06:00:00Z",
  "2026-09-02T12:00:00Z",
  "2026-09-02T18:00:00Z",
  "2026-09-03T00:00:00Z",
];

export const OceanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('indian_ocean_demo');
  const [selectedVariable, setSelectedVariable] = useState<OceanVariable>('temp');
  const [selectedDepth, setSelectedDepth] = useState<DepthLevel>(0);
  
  const [timeIndex, setTimeIndex] = useState<number>(5); // Default 02 SEP 06:00 UTC
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);

  const [layers, setLayers] = useState<LayerVisibilityState>(defaultLayers);
  const [activeDrawer, setActiveDrawer] = useState<ActiveDrawerView>('none');

  const [selectedArgo, setSelectedArgo] = useState<ArgoFloat | null>(DEMO_ARGO_FLOATS[0]);
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

  useEffect(() => {
    oceanApiService.getProvenanceStatus().then(status => {
      if (status && status.isRealDataConnected) {
        setProvenanceMode(status.mode as DataProvenanceMode);
      }
    });

    oceanApiService.getDatasets().then(list => {
      if (list && list.length > 0) {
        setDatasets(list);
        if (list[0].id) {
          setSelectedDatasetId(list[0].id);
        }
      }
    });
  }, []);

  // Time playback ticker
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimeIndex((prev) => (prev + 1) % TIME_STEPS.length);
      }, 2000 / playbackSpeed);
    }
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed]);

  const resetView = useCallback(() => {
    setZoomAction('reset');
    setCameraFlyTarget({ lat: -2.0, lon: 78.0, height: 6500000, pitch: -45, heading: 0 });
  }, []);

  // Global Keyboard Shortcuts (Space: Play/Pause, R: Reset View, A: Auto-Rotate, Esc: Close Drawer)
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

  // Responsive panel management: Auto-collapse left controls on smaller screens when right drawer opens
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

  const formattedCurrentTime = useMemo(() => TIME_STEPS[timeIndex] || TIME_STEPS[0], [timeIndex]);

  const contextValue = useMemo(() => ({
    selectedDatasetId,
    setSelectedDatasetId,
    datasets,
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
