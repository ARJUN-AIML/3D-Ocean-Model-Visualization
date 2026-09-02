'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';
import { Compass, Globe, ShieldAlert, FileText, Activity } from 'lucide-react';
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
    <header className="absolute top-3 left-3 right-3 z-40 min-h-[56px] py-1.5 bg-navy-deep border-2 border-navy-sky rounded-xl px-3 sm:px-4 flex items-center justify-between gap-3 shadow-panel">
      {/* Brand & Platform Identity */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-navy-ocean border border-navy-sky flex items-center justify-center shadow-md">
          <Globe className="w-4 h-4 sm:w-5 sm:h-5 text-navy-ice" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm sm:text-base font-heading font-bold tracking-wider text-navy-ice uppercase">OceanTwin 3D</h1>
            <span className="text-[9px] sm:text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-navy-ocean text-navy-ice border border-navy-sky">
              v1.0 FRONTEND
            </span>
          </div>
          <p className="hidden sm:block text-[10px] text-navy-sky font-sans tracking-wide">Interactive 3D Ocean Intelligence & Validation Platform</p>
        </div>
      </div>

      {/* Compact Location & Data Indicators */}
      <div className="hidden xl:flex items-center gap-3 text-xs font-mono flex-shrink">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-ocean border border-navy-sky text-navy-ice">
          <Compass className="w-3.5 h-3.5 text-navy-ice" />
          <span className="text-navy-ice font-sans">Region:</span>
          <span className="font-semibold text-navy-ice truncate max-w-[160px]">{selectedLocation.regionName}</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-ocean border border-navy-sky text-navy-ice">
          <span className="text-navy-ice font-sans">Var:</span>
          <span className="font-semibold text-navy-ice uppercase">{selectedVariable}</span>
          <span className="text-navy-ice">@</span>
          <span className="font-semibold text-navy-ice">{selectedDepth}m</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-ocean border border-navy-sky text-navy-ice">
          <span className="text-navy-ice font-sans">UTC:</span>
          <span className="font-semibold text-navy-ice">
            {new Date(formattedCurrentTime).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })} — {new Date(formattedCurrentTime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>

      {/* Data Provenance & Utility Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Extensible Marine Sea / Region Selector Dropdown */}
        <MarineRegionSelector />

        {/* Data Provenance Badge */}
        <div 
          title="Backend API not connected yet. Displaying isolate demo UI placeholders."
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-navy-ocean border border-navy-sky text-navy-ice text-[11px] font-mono font-semibold cursor-help flex-shrink-0"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-navy-ice" />
          <span>{provenanceMode}</span>
        </div>

        {/* Contextual Action Trigger Buttons */}
        <button
          onClick={() => setActiveDrawer(activeDrawer === 'validation' ? 'none' : 'validation')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-sans font-semibold transition border-2 flex-shrink-0 ${
            activeDrawer === 'validation'
              ? 'bg-navy-sky text-navy-deep border-navy-ice font-bold shadow-md'
              : 'bg-navy-ocean text-navy-ice border-navy-sky hover:bg-navy-sky hover:text-navy-deep'
          }`}
          title="Open Model Validation & Accuracy Drawer"
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Validation</span>
        </button>

        <button
          onClick={() => setActiveDrawer(activeDrawer === 'report' ? 'none' : 'report')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-sans font-semibold transition border-2 flex-shrink-0 ${
            activeDrawer === 'report'
              ? 'bg-navy-sky text-navy-deep border-navy-ice font-bold shadow-md'
              : 'bg-navy-ocean text-navy-ice border-navy-sky hover:bg-navy-sky hover:text-navy-deep'
          }`}
          title="Open Scientific Export & Report Drawer"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Report</span>
        </button>
      </div>
    </header>
  );
}
