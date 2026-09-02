'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';
import { Compass, Globe, Play, Pause, Layers, ShieldAlert, FileText, Activity } from 'lucide-react';

import MarineRegionSelector from './MarineRegionSelector';

export default function TopBar() {
  const {
    selectedVariable,
    selectedDepth,
    formattedCurrentTime,
    selectedLocation,
    setActiveDrawer,
    activeDrawer,
    provenanceMode
  } = useOcean();

  return (
    <header className="absolute top-3 left-3 right-3 z-40 h-14 bg-ocean-900/80 backdrop-blur-md border border-cyan-500/20 rounded-xl px-4 flex items-center justify-between shadow-panel-dark">
      {/* Brand & Platform Identity */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-cyan-400 p-0.5 shadow-glow-cyan">
          <div className="w-full h-full bg-ocean-950 rounded-[7px] flex items-center justify-center">
            <Globe className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-wider text-slate-100 uppercase">OceanTwin 3D</h1>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-500/30">
              v1.0 FRONTEND
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono tracking-wide">Interactive 3D Ocean Intelligence & Validation Platform</p>
        </div>
      </div>

      {/* Compact Location & Data Indicators */}
      <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-ocean-950/70 border border-slate-800 text-slate-300">
          <Compass className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">Region:</span>
          <span className="font-semibold text-slate-100">{selectedLocation.regionName}</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-ocean-950/70 border border-slate-800 text-slate-300">
          <span className="text-slate-400">Variable:</span>
          <span className="font-semibold text-cyan-300 uppercase">{selectedVariable}</span>
          <span className="text-slate-500">@</span>
          <span className="font-semibold text-amber-400">{selectedDepth}m</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-ocean-950/70 border border-slate-800 text-slate-300">
          <span className="text-slate-400">UTC:</span>
          <span className="font-semibold text-slate-200">
            {new Date(formattedCurrentTime).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })} — {new Date(formattedCurrentTime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>

      {/* Data Provenance & Utility Actions */}
      <div className="flex items-center gap-2">
        {/* Extensible Marine Sea / Region Selector Dropdown */}
        <MarineRegionSelector />

        {/* Data Provenance Badge */}
        <div 
          title="Backend API not connected yet. Displaying isolate demo UI placeholders."
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-950/50 border border-amber-500/40 text-amber-300 text-[11px] font-semibold cursor-help"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span>{provenanceMode}</span>
        </div>

        {/* Contextual Action Trigger Buttons */}
        <button
          onClick={() => setActiveDrawer(activeDrawer === 'validation' ? 'none' : 'validation')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
            activeDrawer === 'validation'
              ? 'bg-cyan-500 text-ocean-950 border-cyan-400 font-semibold'
              : 'bg-ocean-950/80 text-slate-200 border-slate-700 hover:border-cyan-500/50'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Validation</span>
        </button>

        <button
          onClick={() => setActiveDrawer(activeDrawer === 'report' ? 'none' : 'report')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
            activeDrawer === 'report'
              ? 'bg-cyan-500 text-ocean-950 border-cyan-400 font-semibold'
              : 'bg-ocean-950/80 text-slate-200 border-slate-700 hover:border-cyan-500/50'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Report</span>
        </button>
      </div>
    </header>
  );
}
