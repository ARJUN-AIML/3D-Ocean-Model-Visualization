'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';
import { Plus, Minus, RotateCcw, RotateCw } from 'lucide-react';

export default function ZoomControls() {
  const { zoomIn, zoomOut, resetView, autoRotate, toggleAutoRotate } = useOcean();

  return (
    <div className="absolute top-20 right-3 z-30 flex flex-col gap-1.5 p-1.5 bg-ocean-900/85 backdrop-blur-md border border-cyan-500/20 rounded-xl shadow-panel-dark text-slate-200">
      <button
        onClick={zoomIn}
        className="p-2 rounded-lg bg-ocean-950/80 hover:bg-cyan-950 hover:border-cyan-400 text-slate-200 hover:text-cyan-300 transition border border-transparent"
        title="Zoom In (+)"
      >
        <Plus className="w-4 h-4" />
      </button>

      <button
        onClick={zoomOut}
        className="p-2 rounded-lg bg-ocean-950/80 hover:bg-cyan-950 hover:border-cyan-400 text-slate-200 hover:text-cyan-300 transition border border-transparent"
        title="Zoom Out (-)"
      >
        <Minus className="w-4 h-4" />
      </button>

      <div className="w-full h-px bg-slate-800 my-0.5" />

      <button
        onClick={toggleAutoRotate}
        className={`p-2 rounded-lg transition border ${
          autoRotate
            ? 'bg-cyan-500 text-ocean-950 border-cyan-400 font-bold shadow-glow-cyan'
            : 'bg-ocean-950/80 hover:bg-cyan-950 hover:border-cyan-400 text-slate-200 hover:text-cyan-300 border-transparent'
        }`}
        title={autoRotate ? 'Stop Globe Auto-Rotate' : 'Start Globe Auto-Rotate'}
      >
        <RotateCw className={`w-4 h-4 ${autoRotate ? 'animate-spin' : ''}`} />
      </button>

      <button
        onClick={resetView}
        className="p-2 rounded-lg bg-ocean-950/80 hover:bg-cyan-950 hover:border-cyan-400 text-slate-200 hover:text-cyan-300 transition border border-transparent"
        title="Reset Orbit View"
      >
        <RotateCcw className="w-4 h-4" />
      </button>
    </div>
  );
}
