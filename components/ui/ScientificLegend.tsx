'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';

export default function ScientificLegend() {
  const { selectedVariable, layers } = useOcean();

  const getLegendDetails = () => {
    if (layers.errorHeatmap) {
      return {
        title: 'MODEL ERROR (RAW vs CORRECTED)',
        unit: '°C Residual',
        gradient: 'from-emerald-500 via-yellow-400 to-rose-600',
        min: '0.0 °C',
        mid: '1.5 °C',
        max: '3.0+ °C'
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
    <div className="absolute bottom-24 left-3 z-30 w-64 bg-ocean-900/85 backdrop-blur-md border border-cyan-500/20 rounded-xl p-3 shadow-panel-dark text-slate-200">
      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-2">
        <span>{legend.title}</span>
        <span className="font-mono text-cyan-400">[{legend.unit}]</span>
      </div>

      {/* Color Gradient Bar */}
      <div className={`w-full h-3 rounded-md bg-gradient-to-r ${legend.gradient} shadow-inner mb-1.5`} />

      {/* Range Markers */}
      <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
        <span>{legend.min}</span>
        <span>{legend.mid}</span>
        <span>{legend.max}</span>
      </div>
    </div>
  );
}
