'use client';

import React from 'react';
import ReactECharts from 'echarts-for-react';
import { ArgoProfilePoint } from '../../types/ocean';

interface VerticalProfileChartProps {
  profileData: ArgoProfilePoint[];
  floatName?: string;
}

export default function VerticalProfileChart({ profileData, floatName }: VerticalProfileChartProps) {
  // Sort profile data by depth ascending
  const sorted = [...profileData].sort((a, b) => a.depth - b.depth);

  const depths = sorted.map((p) => p.depth);
  const temperatures = sorted.map((p) => p.temperature);
  const salinities = sorted.map((p) => p.salinity);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0a1120',
      borderColor: '#38bdf8',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (params: any[]) => {
        let depthVal = params[0]?.value[1] ?? params[0]?.value;
        let res = `<div style="font-weight:bold;margin-bottom:4px;color:#38bdf8">Depth: ${depthVal} m</div>`;
        params.forEach((item) => {
          const color = item.color;
          const seriesName = item.seriesName;
          const val = item.value[0] !== undefined ? item.value[0] : item.value;
          const unit = seriesName.includes('Temp') ? '°C' : 'PSU';
          res += `<div style="display:flex;align-items:center;justify-between;gap:8px;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};"></span>
            <span>${seriesName}: <strong>${val} ${unit}</strong></span>
          </div>`;
        });
        return res;
      }
    },
    legend: {
      top: 0,
      textStyle: { color: '#94a3b8', fontSize: 11 },
      data: ['Temperature (°C)', 'Salinity (PSU)']
    },
    grid: {
      left: '12%',
      right: '12%',
      bottom: '10%',
      top: '15%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'value',
        name: 'Temp (°C)',
        nameTextStyle: { color: '#f43f5e', fontSize: 10 },
        position: 'top',
        axisLine: { lineStyle: { color: '#f43f5e' } },
        axisLabel: { color: '#f43f5e', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      {
        type: 'value',
        name: 'Salinity (PSU)',
        nameTextStyle: { color: '#38bdf8', fontSize: 10 },
        position: 'bottom',
        axisLine: { lineStyle: { color: '#38bdf8' } },
        axisLabel: { color: '#38bdf8', fontSize: 10 },
        splitLine: { show: false }
      }
    ],
    yAxis: {
      type: 'value',
      name: 'Depth (m)',
      inverse: true, // Oceanographic standard: Surface at top, deep water at bottom
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } }
    },
    series: [
      {
        name: 'Temperature (°C)',
        type: 'line',
        xAxisIndex: 0,
        smooth: true,
        data: temperatures.map((t, i) => [t, depths[i]]),
        lineStyle: { color: '#f43f5e', width: 2.5 },
        itemStyle: { color: '#f43f5e' }
      },
      {
        name: 'Salinity (PSU)',
        type: 'line',
        xAxisIndex: 1,
        smooth: true,
        data: salinities.map((s, i) => [s, depths[i]]),
        lineStyle: { color: '#38bdf8', width: 2, type: 'dashed' },
        itemStyle: { color: '#38bdf8' }
      }
    ]
  };

  return (
    <div className="w-full h-64 bg-ocean-950/60 rounded-xl border border-slate-800 p-2">
      <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
    </div>
  );
}
