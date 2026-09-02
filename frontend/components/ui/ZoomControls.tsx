'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';
import { Plus, Minus, RotateCcw, RotateCw } from 'lucide-react';

export default function ZoomControls() {
  const { zoomIn, zoomOut, resetView, autoRotate, toggleAutoRotate } = useOcean();

  return (
    <div className="absolute top-[72px] right-3 z-20 flex flex-col gap-1.5 p-1.5 bg-navy-deep border-2 border-navy-sky rounded-xl shadow-panel text-navy-ice">
      <button
        onClick={zoomIn}
        className="p-2 rounded-lg bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep border border-navy-sky text-navy-ice transition"
        title="Zoom In (+)"
      >
        <Plus className="w-4 h-4" />
      </button>

      <button
        onClick={zoomOut}
        className="p-2 rounded-lg bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep border border-navy-sky text-navy-ice transition"
        title="Zoom Out (-)"
      >
        <Minus className="w-4 h-4" />
      </button>

      <div className="w-full h-px bg-navy-sky my-0.5" />

      <button
        onClick={toggleAutoRotate}
        className={`p-2 rounded-lg transition border ${
          autoRotate
            ? 'bg-navy-sky text-navy-deep border-2 border-navy-ice font-bold shadow-md'
            : 'bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep border border-navy-sky text-navy-ice'
        }`}
        title={autoRotate ? 'Stop Globe Auto-Rotate' : 'Start Globe Auto-Rotate'}
      >
        <RotateCw className={`w-4 h-4 ${autoRotate ? 'animate-spin' : ''}`} />
      </button>

      <button
        onClick={resetView}
        className="p-2 rounded-lg bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep border border-navy-sky text-navy-ice transition"
        title="Reset Orbit View"
      >
        <RotateCcw className="w-4 h-4" />
      </button>
    </div>
  );
}
