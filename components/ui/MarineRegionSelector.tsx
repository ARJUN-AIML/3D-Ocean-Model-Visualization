'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useOcean } from '../../context/OceanContext';
import { MARINE_REGIONS, MarineRegion } from '../../mocks/marineRegions';
import { Anchor, ChevronDown, Compass } from 'lucide-react';

export default function MarineRegionSelector() {
  const { flyToLocation, setSelectedLocation } = useOcean();
  const [selectedRegion, setSelectedRegion] = useState<MarineRegion>(MARINE_REGIONS[0]);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (region: MarineRegion) => {
    setSelectedRegion(region);
    setIsOpen(false);
    
    // Fly camera with dynamic 3D perspective angle
    flyToLocation(region.lat, region.lon, region.height, region.pitch, region.heading);
    
    setSelectedLocation({
      lat: region.lat,
      lon: region.lon,
      regionName: region.name.replace(/^[^\w]+/, '').trim(),
      seaDepthM: 3500
    });
  };

  return (
    <div ref={dropdownRef} className="relative z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-ocean-950/90 border border-cyan-500/40 hover:border-cyan-400 text-xs font-semibold text-cyan-200 transition shadow-glow-cyan/20"
        title="Select Marine Sea / Ocean Region"
      >
        <Anchor className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
        <span className="truncate max-w-[140px] sm:max-w-[180px]">{selectedRegion.name}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-72 max-h-96 overflow-y-auto bg-ocean-900/95 border border-cyan-500/30 rounded-xl shadow-panel-dark backdrop-blur-xl p-1.5 flex flex-col gap-1 text-xs">
          <div className="px-2.5 py-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-cyan-400 border-b border-slate-800 flex items-center gap-1.5">
            <Compass className="w-3 h-3 text-cyan-400" />
            <span>Select Marine Domain / Ocean Surface</span>
          </div>

          {MARINE_REGIONS.map((region) => (
            <button
              key={region.id}
              onClick={() => handleSelect(region)}
              className={`flex flex-col items-start px-2.5 py-2 rounded-lg transition text-left ${
                selectedRegion.id === region.id
                  ? 'bg-cyan-950/80 border border-cyan-400/50 text-cyan-200'
                  : 'hover:bg-ocean-950 text-slate-200 hover:text-cyan-300'
              }`}
            >
              <div className="font-semibold text-xs flex items-center justify-between w-full">
                <span>{region.name}</span>
                <span className="text-[9px] font-mono text-slate-400">{region.category}</span>
              </div>
              <span className="text-[10px] text-slate-400 mt-0.5 font-sans leading-tight">
                {region.description}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
