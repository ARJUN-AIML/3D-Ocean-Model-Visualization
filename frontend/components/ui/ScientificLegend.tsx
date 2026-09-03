'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';

export default function ScientificLegend() {
  const { selectedVariable, layers, heatmapMode, heatmapVariable } = useOcean();

  const getLegendDetails = () => {
    if (layers.errorHeatmap) {
      const varName = (heatmapVariable || selectedVariable || 'temperature').toUpperCase();
      const isSal = (heatmapVariable || selectedVariable) === 'salinity';
      const modeName = (heatmapMode || 'raw').toUpperCase();

      return {
        title: `HEATMAP (${modeName} ${varName})`,
        unit: isSal ? 'PSU (Obs-Model)' : '°C (Obs-Model)',
        gradient: 'from-blue-600 via-cyan-400 via-emerald-500 via-amber-400 to-rose-600',
        min: isSal ? '-0.5' : '-2.0',
        mid: '0.0 (Agree)',
        max: isSal ? '+0.5' : '+2.0'
      };
    }

    switch (selectedVariable) {
      case 'temp':
        return {
          title: 'SEA TEMPERATURE',
          unit: '°C',
          gradient: 'from-indigo-600 via-cyan-400 via-amber-400 to-rose-600',
          min: '-2 °C',
          mid: '15 °C',
          max: '32 °C'
        };
      case 'salinity':
        return {
          title: 'SEA SALINITY',
          unit: 'PSU',
          gradient: 'from-cyan-400 via-blue-600 to-purple-600',
          min: '32.0 PSU',
          mid: '35.0 PSU',
          max: '38.0 PSU'
        };
      case 'currents':
        return {
          title: 'CURRENT VELOCITY',
          unit: 'm/s',
          gradient: 'from-slate-700 via-emerald-400 via-cyan-400 to-fuchsia-500',
          min: '0.0 m/s',
          mid: '1.0 m/s',
          max: '2.5+ m/s'
        };
      case 'waves':
        return {
          title: 'SIGNIFICANT WAVE HEIGHT',
          unit: 'm',
          gradient: 'from-teal-600 via-blue-500 to-purple-600',
          min: '0.5 m',
          mid: '3.0 m',
          max: '8.0+ m'
        };
      default:
        return {
          title: 'SEA TEMPERATURE',
          unit: '°C',
          gradient: 'from-indigo-600 via-cyan-400 via-amber-400 to-rose-600',
          min: '-2 °C',
          mid: '15 °C',
          max: '32 °C'
        };
    }
  };

  const legend = getLegendDetails();

  return (
    <div className="hidden sm:block absolute bottom-3 right-3 z-20 w-48 sm:w-56 md:w-64 bg-navy-deep border-2 border-navy-sky rounded-xl p-2.5 sm:p-3 shadow-panel text-navy-ice select-none">
      <div className="flex items-center justify-between text-[11px] font-heading font-semibold text-navy-ice uppercase tracking-wider mb-2">
        <span>{legend.title}</span>
        <span className="font-mono text-navy-ice font-bold">[{legend.unit}]</span>
      </div>

      {/* Scientific Color Gradient Bar (preserved as-is) */}
      <div className={`w-full h-3 rounded-md bg-gradient-to-r ${legend.gradient} shadow-inner mb-1.5`} />

      {/* Range Markers */}
      <div className="flex justify-between items-center text-[10px] font-mono text-navy-ice font-semibold">
        <span>{legend.min}</span>
        <span>{legend.mid}</span>
        <span>{legend.max}</span>
      </div>
    </div>
  );
}
