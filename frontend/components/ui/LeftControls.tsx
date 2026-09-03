'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';
import { DepthLevel, LayerVisibilityState } from '../../types/ocean';
import {
  Thermometer,
  Droplets,
  Wind,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Navigation,
  Sparkles,
  Sliders,
  Radio
} from 'lucide-react';

const DEPTH_LEVELS: DepthLevel[] = [0, 10, 50, 100, 500, 1000, 2000];

export default function LeftControls() {
  const {
    selectedVariable,
    setSelectedVariable,
    selectedDepth,
    setSelectedDepth,
    layers,
    toggleLayer,
    leftControlsOpen,
    setLeftControlsOpen,
    trajectoryModeActive,
    setTrajectoryModeActive,
    setActiveDrawer,
    activeDrawer
  } = useOcean();

  return (
    <aside
      className={`absolute top-[72px] left-3 z-40 transition-all duration-300 ${
        leftControlsOpen ? 'w-80 max-w-[calc(100vw-24px)]' : 'w-11'
      }`}
    >
      <div className="bg-navy-deep border-2 border-navy-sky rounded-xl p-3 shadow-panel text-navy-ice max-h-[calc(100vh-160px)] sm:max-h-[calc(100vh-180px)] overflow-y-auto">
        {/* Panel Header & Collapse Toggle */}
        <div className="flex items-center justify-between border-b-2 border-navy-sky pb-2.5 mb-3 sticky top-0 bg-navy-deep z-10">
          {leftControlsOpen && (
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-navy-sky" />
              <h2 className="text-xs font-heading font-bold tracking-wider text-navy-ice uppercase">Scientific Controls</h2>
            </div>
          )}
          <button
            onClick={() => setLeftControlsOpen(!leftControlsOpen)}
            className="p-1 rounded bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep text-navy-ice border border-navy-sky transition ml-auto"
            title={leftControlsOpen ? 'Collapse Controls' : 'Expand Controls'}
          >
            {leftControlsOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {leftControlsOpen && (
          <div className="space-y-4 text-xs font-sans">
            {/* 1. VARIABLE SELECTOR */}
            <div>
              <label className="text-[11px] font-mono font-semibold text-navy-sky uppercase tracking-wider block mb-2">
                Ocean Variable
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  onClick={() => setSelectedVariable('temp')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'temp'
                      ? 'bg-navy-sky text-navy-deep border-2 border-navy-ice font-bold shadow-md'
                      : 'bg-navy-ocean text-navy-ice border border-navy-sky hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                >
                  <Thermometer className="w-4 h-4" />
                  <div>
                    <div className="font-semibold text-xs">Temperature</div>
                    <div className="text-[10px] font-mono">°C</div>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedVariable('salinity')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'salinity'
                      ? 'bg-navy-sky text-navy-deep border-2 border-navy-ice font-bold shadow-md'
                      : 'bg-navy-ocean text-navy-ice border border-navy-sky hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                >
                  <Droplets className="w-4 h-4" />
                  <div>
                    <div className="font-semibold text-xs">Salinity</div>
                    <div className="text-[10px] font-mono">PSU</div>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedVariable('currents')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'currents'
                      ? 'bg-navy-sky text-navy-deep border-2 border-navy-ice font-bold shadow-md'
                      : 'bg-navy-ocean text-navy-ice border border-navy-sky hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                >
                  <Wind className="w-4 h-4" />
                  <div>
                    <div className="font-semibold text-xs">Currents</div>
                    <div className="text-[10px] font-mono">m/s</div>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedVariable('waves')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'waves'
                      ? 'bg-navy-sky text-navy-deep border-2 border-navy-ice font-bold shadow-md'
                      : 'bg-navy-ocean text-navy-ice border border-navy-sky hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                >
                  <Radio className="w-4 h-4" />
                  <div>
                    <div className="font-semibold text-xs">Waves</div>
                    <div className="text-[10px] font-mono">Height (m)</div>
                  </div>
                </button>
              </div>
            </div>

            {/* 2. DEPTH SLICING CONTROL */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-mono font-semibold text-navy-sky uppercase tracking-wider">
                  Depth Level
                </label>
                <span className="font-mono font-bold text-navy-ice bg-navy-ocean px-2 py-0.5 rounded border border-navy-sky">
                  {selectedDepth === 0 ? 'Surface (0m)' : `${selectedDepth} m`}
                </span>
              </div>

              {/* Depth Selector Buttons */}
              <div className="flex flex-wrap gap-1 mb-2">
                {DEPTH_LEVELS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setSelectedDepth(d)}
                    className={`flex-1 py-1 rounded text-[11px] font-mono transition border ${
                      selectedDepth === d
                        ? 'bg-navy-sky text-navy-deep font-bold border-2 border-navy-ice shadow-md'
                        : 'bg-navy-ocean border border-navy-sky text-navy-ice hover:bg-navy-sky hover:text-navy-deep'
                    }`}
                  >
                    {d === 0 ? '0m' : `${d}m`}
                  </button>
                ))}
              </div>
            </div>

            {/* 3. SCIENTIFIC VISUAL LAYERS TOGGLES */}
            <div>
              <label className="text-[11px] font-mono font-semibold text-navy-sky uppercase tracking-wider block mb-2">
                Layers & Overlays
              </label>

              <div className="space-y-1">
                {[
                  { key: 'argoFloats', label: '📡 Argo Float Observations' },
                  { key: 'currentParticles', label: '🌊 Animated Current Field' },
                  { key: 'errorHeatmap', label: '🗺️ Model Error Heatmap' },
                  { key: 'anomalies', label: '⚠️ Ocean Anomaly Hotspots' },
                  { key: 'trajectoryPath', label: '📍 Trajectory Drift Paths' },
                ].map(({ key, label }) => {
                  const isActive = layers[key as keyof LayerVisibilityState];
                  return (
                    <button
                      key={key}
                      onClick={() => toggleLayer(key as keyof LayerVisibilityState)}
                      className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg border text-left transition text-[11px] ${
                        isActive
                          ? 'bg-navy-sky text-navy-deep font-bold border-2 border-navy-ice shadow-md'
                          : 'bg-navy-ocean text-navy-ice border border-navy-sky/60 hover:bg-navy-sky hover:text-navy-deep'
                      }`}
                    >
                      <span>{label}</span>
                      {isActive ? (
                        <Eye className="w-3.5 h-3.5 text-navy-deep" />
                      ) : (
                        <EyeOff className="w-3.5 h-3.5 text-navy-ice/50" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 4. TRAJECTORY & PROMINENT AI INSIGHT ACTIONS */}
            <div className="pt-2 border-t-2 border-navy-sky space-y-2">
              <button
                onClick={() => setTrajectoryModeActive(!trajectoryModeActive)}
                className={`w-full flex items-center justify-center gap-2 py-2 rounded-lg font-semibold text-xs transition border-2 ${
                  trajectoryModeActive
                    ? 'bg-navy-sky text-navy-deep border-navy-ice shadow-md'
                    : 'bg-navy-ocean border border-navy-sky text-navy-ice hover:bg-navy-sky hover:text-navy-deep'
                }`}
              >
                <Navigation className="w-4 h-4" />
                <span>{trajectoryModeActive ? 'Selecting Drift Origin...' : 'Current Trajectory Mode'}</span>
              </button>

              {/* PROMINENT AI MODEL INSIGHTS BUTTON */}
              <button
                onClick={() => setActiveDrawer(activeDrawer === 'explain' ? 'none' : 'explain')}
                className={`w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl transition border-2 ${
                  activeDrawer === 'explain'
                    ? 'bg-navy-sky text-navy-deep border-navy-ice font-bold shadow-md'
                    : 'bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep border-navy-sky text-navy-ice font-bold shadow-md'
                }`}
                title="Open AI Ocean Model Insights & Physics Explanation Drawer"
              >
                <Sparkles className="w-4 h-4" />
                <span className="tracking-wide">AI MODEL INSIGHTS & PREDICTIONS</span>
              </button>

              {/* QUICK SCIENTIFIC ANALYTICS DRAWERS */}
              <div className="grid grid-cols-3 gap-1 pt-1">
                <button
                  onClick={() => setActiveDrawer(activeDrawer === 'reliability' ? 'none' : 'reliability')}
                  className={`py-1 px-1.5 rounded text-[10px] font-mono text-center transition border ${
                    activeDrawer === 'reliability'
                      ? 'bg-navy-sky text-navy-deep font-bold border-navy-ice'
                      : 'bg-navy-ocean text-navy-ice border-navy-sky/60 hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                  title="View Model Reliability Score"
                >
                  🛡️ Reliability
                </button>
                <button
                  onClick={() => setActiveDrawer(activeDrawer === 'argo' ? 'none' : 'argo')}
                  className={`py-1 px-1.5 rounded text-[10px] font-mono text-center transition border ${
                    activeDrawer === 'argo'
                      ? 'bg-navy-sky text-navy-deep font-bold border-navy-ice'
                      : 'bg-navy-ocean text-navy-ice border-navy-sky/60 hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                  title="View Vertical CTD Depth Profile"
                >
                  📈 Profile
                </button>
                <button
                  onClick={() => setActiveDrawer(activeDrawer === 'bias' ? 'none' : 'bias')}
                  className={`py-1 px-1.5 rounded text-[10px] font-mono text-center transition border ${
                    activeDrawer === 'bias'
                      ? 'bg-navy-sky text-navy-deep font-bold border-navy-ice'
                      : 'bg-navy-ocean text-navy-ice border-navy-sky/60 hover:bg-navy-sky hover:text-navy-deep'
                  }`}
                  title="View XGBoost Bias-Correction"
                >
                  ⚡ Bias Field
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
