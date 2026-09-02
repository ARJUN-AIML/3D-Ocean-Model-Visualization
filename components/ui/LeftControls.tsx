'use client';

import React, { useState } from 'react';
import { useOcean } from '../../context/OceanContext';
import { OceanVariable, DepthLevel, LayerVisibilityState } from '../../types/ocean';
import {
  Thermometer,
  Droplets,
  Wind,
  Layers,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Navigation,
  Sparkles,
  Sliders,
  Radio,
  MapPin
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
      className={`absolute top-20 left-3 z-30 transition-all duration-300 ${
        leftControlsOpen ? 'w-80' : 'w-12'
      }`}
    >
      <div className="bg-ocean-900/85 backdrop-blur-md border border-cyan-500/20 rounded-xl p-3 shadow-panel-dark text-slate-200 overflow-hidden">
        {/* Panel Header & Collapse Toggle */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
          {leftControlsOpen && (
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs font-bold tracking-wider text-slate-100 uppercase">Scientific Controls</h2>
            </div>
          )}
          <button
            onClick={() => setLeftControlsOpen(!leftControlsOpen)}
            className="p-1 rounded bg-ocean-950 hover:bg-slate-800 text-slate-300 transition ml-auto"
            title={leftControlsOpen ? 'Collapse Controls' : 'Expand Controls'}
          >
            {leftControlsOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {leftControlsOpen && (
          <div className="space-y-4 text-xs">
            {/* 1. VARIABLE SELECTOR */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Ocean Variable
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  onClick={() => setSelectedVariable('temp')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'temp'
                      ? 'bg-cyan-950 border-cyan-400 text-cyan-200 font-medium shadow-glow-cyan'
                      : 'bg-ocean-950/70 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <Thermometer className="w-4 h-4 text-rose-400" />
                  <div>
                    <div className="font-semibold">Temperature</div>
                    <div className="text-[10px] text-slate-400 font-mono">°C</div>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedVariable('salinity')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'salinity'
                      ? 'bg-cyan-950 border-cyan-400 text-cyan-200 font-medium shadow-glow-cyan'
                      : 'bg-ocean-950/70 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <Droplets className="w-4 h-4 text-cyan-400" />
                  <div>
                    <div className="font-semibold">Salinity</div>
                    <div className="text-[10px] text-slate-400 font-mono">PSU</div>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedVariable('currents')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition ${
                    selectedVariable === 'currents'
                      ? 'bg-cyan-950 border-cyan-400 text-cyan-200 font-medium shadow-glow-cyan'
                      : 'bg-ocean-950/70 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <Wind className="w-4 h-4 text-emerald-400" />
                  <div>
                    <div className="font-semibold">Currents</div>
                    <div className="text-[10px] text-slate-400 font-mono">m/s</div>
                  </div>
                </button>

                <button
                  onClick={() => setSelectedVariable('waves')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-left transition focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                    selectedVariable === 'waves'
                      ? 'bg-cyan-950 border-cyan-400 text-cyan-200 font-medium shadow-glow-cyan'
                      : 'bg-ocean-950/70 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <Radio className="w-4 h-4 text-indigo-400" />
                  <div>
                    <div className="font-semibold">Waves</div>
                    <div className="text-[10px] text-slate-400 font-mono">Height (m)</div>
                  </div>
                </button>
              </div>
            </div>

            {/* 2. DEPTH SLICING CONTROL */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Depth Level
                </label>
                <span className="font-mono font-bold text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-500/30">
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
                        ? 'bg-amber-500 text-ocean-950 font-bold border-amber-400 shadow-sm'
                        : 'bg-ocean-950/80 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    {d === 0 ? '0m' : `${d}m`}
                  </button>
                ))}
              </div>
            </div>

            {/* 3. SCIENTIFIC VISUAL LAYERS TOGGLES */}
            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Layers & Overlays
              </label>

              <div className="space-y-1">
                {[
                  { key: 'argoFloats', label: '📡 Argo Float Observations', color: 'text-cyan-400' },
                  { key: 'currentParticles', label: '🌊 Animated Current Field', color: 'text-emerald-400' },
                  { key: 'errorHeatmap', label: '🗺️ Model Error Heatmap', color: 'text-rose-400' },
                  { key: 'anomalies', label: '⚠️ Ocean Anomaly Hotspots', color: 'text-amber-400' },
                  { key: 'trajectoryPath', label: '📍 Trajectory Drift Paths', color: 'text-indigo-400' },
                ].map(({ key, label }) => {
                  const isActive = layers[key as keyof LayerVisibilityState];
                  return (
                    <button
                      key={key}
                      onClick={() => toggleLayer(key as keyof LayerVisibilityState)}
                      className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg border text-left transition text-[11px] ${
                        isActive
                          ? 'bg-ocean-950 border-slate-700 text-slate-100 font-medium'
                          : 'bg-ocean-950/40 border-slate-800/60 text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      <span>{label}</span>
                      {isActive ? (
                        <Eye className="w-3.5 h-3.5 text-cyan-400" />
                      ) : (
                        <EyeOff className="w-3.5 h-3.5 text-slate-600" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 4. TRAJECTORY & INSIGHT ACTIONS */}
            <div className="pt-2 border-t border-slate-800 space-y-1.5">
              <button
                onClick={() => setTrajectoryModeActive(!trajectoryModeActive)}
                className={`w-full flex items-center justify-center gap-2 py-2 rounded-lg font-semibold text-xs transition border ${
                  trajectoryModeActive
                    ? 'bg-cyan-500 text-ocean-950 border-cyan-400 animate-pulse'
                    : 'bg-cyan-950/60 border-cyan-500/40 text-cyan-300 hover:bg-cyan-900/80'
                }`}
              >
                <Navigation className="w-4 h-4" />
                <span>{trajectoryModeActive ? 'Selecting Drift Origin...' : 'Current Trajectory Mode'}</span>
              </button>

              <button
                onClick={() => setActiveDrawer(activeDrawer === 'explain' ? 'none' : 'explain')}
                className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-indigo-950/60 border border-indigo-500/40 text-indigo-300 font-semibold text-xs hover:bg-indigo-900/80 transition"
              >
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Explain This Region</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
