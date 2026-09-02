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
      backgroundColor: '#061024',
      borderColor: '#4988C4',
      textStyle: { color: '#BDE8F5', fontSize: 11 }
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
      axisLine: { lineStyle: { color: '#1C4D8D' } },
      axisLabel: { color: '#BDE8F5', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: 'Temperature (°C)',
      nameTextStyle: { color: '#7FA9C9', fontSize: 10 },
      axisLine: { lineStyle: { color: '#1C4D8D' } },
      axisLabel: { color: '#7FA9C9', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(73, 136, 196, 0.15)' } }
    },
    series: [
      {
        name: 'Value (°C)',
        type: 'bar',
        barWidth: '35%',
        data: [
          { value: biasData.rawValue, itemStyle: { color: '#1C4D8D' } },
          { value: biasData.correctedValue, itemStyle: { color: '#4988C4' } },
          { value: biasData.observationValue, itemStyle: { color: '#BDE8F5' } }
        ],
        label: {
          show: true,
          position: 'top',
          color: '#BDE8F5',
          fontSize: 11,
          formatter: '{c} °C'
        }
      }
    ]
  };

  return (
    <div className="w-full h-52 bg-navy-darker rounded-xl border border-navy-ocean/50 p-2">
      <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
    </div>
  );
}
