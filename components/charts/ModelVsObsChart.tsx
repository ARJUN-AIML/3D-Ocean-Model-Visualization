'use client';

import React from 'react';
import ReactECharts from 'echarts-for-react';
import { BiasCorrectionData } from '../../types/ocean';

interface ModelVsObsChartProps {
  biasData: BiasCorrectionData;
}

export default function ModelVsObsChart({ biasData }: ModelVsObsChartProps) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0a1120',
      borderColor: '#38bdf8',
      textStyle: { color: '#e2e8f0', fontSize: 11 }
    },
    grid: {
      left: '10%',
      right: '8%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['Raw Model', 'AI Corrected', 'Observed (Argo)'],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#cbd5e1', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: 'Temperature (°C)',
      nameTextStyle: { color: '#94a3b8', fontSize: 10 },
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)' } }
    },
    series: [
      {
        name: 'Value (°C)',
        type: 'bar',
        barWidth: '35%',
        data: [
          { value: biasData.rawValue, itemStyle: { color: '#ef4444' } },
          { value: biasData.correctedValue, itemStyle: { color: '#0ea5e9' } },
          { value: biasData.observationValue, itemStyle: { color: '#10b981' } }
        ],
        label: {
          show: true,
          position: 'top',
          color: '#e2e8f0',
          fontSize: 11,
          formatter: '{c} °C'
        }
      }
    ]
  };

  return (
    <div className="w-full h-52 bg-ocean-950/60 rounded-xl border border-slate-800 p-2">
      <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
    </div>
  );
}
