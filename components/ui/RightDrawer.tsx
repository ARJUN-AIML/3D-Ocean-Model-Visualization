'use client';

import React, { useState } from 'react';
import { useOcean } from '../../context/OceanContext';
import VerticalProfileChart from '../charts/VerticalProfileChart';
import ModelVsObsChart from '../charts/ModelVsObsChart';
import {
  DEMO_BIAS_CORRECTION,
  DEMO_VALIDATION_METRICS,
  DEMO_RELIABILITY_DATA,
  DEMO_REGIONAL_INSIGHT,
  DEMO_MODEL_OBS_MATCH
} from '../../mocks/oceanDemoData';

import {
  X,
  Radio,
  Activity,
  Sparkles,
  Navigation,
  FileText,
  ShieldCheck,
  Cpu,
  BarChart3,
  AlertTriangle,
  MapPin,
  CheckCircle2,
  Clock,
  Compass,
  ArrowUpRight,
  Download
} from 'lucide-react';
import { DEMO_ARGO_FLOATS, DEMO_ANOMALIES } from '../../mocks/oceanDemoData';

export default function RightDrawer() {
  const {
    activeDrawer,
    closeDrawer,
    selectedArgo,
    selectedAnomaly,
    selectedLocation,
    activeTrajectory,
    trajectoryDuration,
    setTrajectoryDuration,
    setTrajectoryModeActive,
    setActiveTrajectory,
    provenanceMode
  } = useOcean();

  const [reportGenerated, setReportGenerated] = useState<boolean>(false);

  const handleDownloadGeoJSON = () => {
    const geojson = {
      type: 'FeatureCollection',
      metadata: {
        platform: 'OceanTwin 3D',
        timestamp: new Date().toISOString(),
        region: selectedLocation.regionName
      },
      features: [
        ...DEMO_ARGO_FLOATS.map((f) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [f.lon, f.lat, 0]
          },
          properties: {
            id: f.id,
            name: f.name,
            wmoNumber: f.wmoNumber,
            surfaceTemp: f.surfaceTemp,
            surfaceSalinity: f.surfaceSalinity,
            qualityStatus: f.qualityStatus
          }
        })),
        ...DEMO_ANOMALIES.map((a) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [a.lon, a.lat, 0]
          },
          properties: {
            id: a.id,
            name: a.locationName,
            severity: a.severity,
            currentValue: a.currentValue,
            baselineValue: a.baselineValue,
            deviation: a.deviation,
            zScore: a.zScore
          }
        }))
      ]
    };

    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/geo+json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `oceantwin_dataset_${Date.now()}.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (activeDrawer === 'none') return null;

  return (
    <aside className="absolute top-20 right-3 bottom-20 z-40 w-full max-w-md bg-ocean-900/90 backdrop-blur-md border border-cyan-500/20 rounded-xl p-4 shadow-panel-dark text-slate-200 overflow-y-auto flex flex-col justify-between select-none">
      {/* Drawer Header */}
      <div>
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            {activeDrawer === 'argo' && <Radio className="w-5 h-5 text-cyan-400" />}
            {activeDrawer === 'validation' && <Activity className="w-5 h-5 text-emerald-400" />}
            {activeDrawer === 'bias' && <Cpu className="w-5 h-5 text-cyan-400" />}
            {activeDrawer === 'anomaly' && <AlertTriangle className="w-5 h-5 text-amber-400" />}
            {activeDrawer === 'trajectory' && <Navigation className="w-5 h-5 text-cyan-400" />}
            {activeDrawer === 'explain' && <Sparkles className="w-5 h-5 text-indigo-400" />}
            {activeDrawer === 'report' && <FileText className="w-5 h-5 text-cyan-400" />}

            <h2 className="text-sm font-bold tracking-wider text-slate-100 uppercase">
              {activeDrawer === 'argo' && 'ARGO Station Profile'}
              {activeDrawer === 'validation' && 'Model Validation Engine'}
              {activeDrawer === 'bias' && 'AI Bias Correction'}
              {activeDrawer === 'anomaly' && 'Ocean Anomaly Inspector'}
              {activeDrawer === 'trajectory' && 'Current Trajectory Drift'}
              {activeDrawer === 'explain' && 'Regional AI Insight'}
              {activeDrawer === 'report' && 'Ocean Report Generator'}
            </h2>
          </div>

          <button
            onClick={closeDrawer}
            className="p-1 rounded-lg bg-ocean-950 hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Provenance Notice Banner inside Drawer */}
        <div className="mb-4 px-3 py-2 rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-300 text-[11px] flex items-center justify-between">
          <span className="font-semibold">{provenanceMode}</span>
          <span className="text-[10px] text-amber-400/80 font-mono">Backend API Pending</span>
        </div>

        {/* ========================================================= */}
        {/* FEATURE 01 & 02: ARGO OBSERVATION STATION DETAILS */}
        {/* ========================================================= */}
        {activeDrawer === 'argo' && selectedArgo && (
          <div className="space-y-4 text-xs">
            <div className="bg-ocean-950/70 p-3 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-100 text-sm">{selectedArgo.id}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/30 font-mono text-[10px]">
                  {selectedArgo.qualityStatus}
                </span>
              </div>
              <div className="text-slate-400 font-medium">{selectedArgo.name}</div>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-slate-300 font-mono">
                <div>Lat: <strong className="text-slate-100">{selectedArgo.lat}°N</strong></div>
                <div>Lon: <strong className="text-slate-100">{selectedArgo.lon}°E</strong></div>
                <div>Surface Temp: <strong className="text-rose-400">{selectedArgo.surfaceTemp}°C</strong></div>
                <div>Salinity: <strong className="text-cyan-400">{selectedArgo.surfaceSalinity} PSU</strong></div>
              </div>
            </div>

            {/* CTD Depth Profile EChart */}
            <div>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>In-Situ CTD Depth Profile (0 - 2,000m)</span>
              </div>
              <VerticalProfileChart profileData={selectedArgo.profileData} floatName={selectedArgo.id} />
            </div>

            {/* Model vs Observation Match Section */}
            <div className="bg-ocean-950/70 p-3 rounded-xl border border-slate-800 space-y-2">
              <div className="font-semibold text-cyan-300">Model vs Argo Point Match</div>
              <div className="grid grid-cols-3 gap-2 font-mono text-center">
                <div className="p-2 rounded bg-ocean-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Model</div>
                  <div className="text-slate-100 font-bold">{DEMO_MODEL_OBS_MATCH.modelValue}°C</div>
                </div>
                <div className="p-2 rounded bg-ocean-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Observed</div>
                  <div className="text-emerald-400 font-bold">{DEMO_MODEL_OBS_MATCH.observedValue}°C</div>
                </div>
                <div className="p-2 rounded bg-ocean-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400">Difference</div>
                  <div className="text-amber-400 font-bold">+{DEMO_MODEL_OBS_MATCH.difference}°C</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* FEATURE 03, 04, 05 & 06: MODEL VALIDATION & AI BIAS CORRECTION */}
        {/* ========================================================= */}
        {activeDrawer === 'validation' && (
          <div className="space-y-4 text-xs">
            {/* Reliability Badge */}
            <div className="bg-emerald-950/40 border border-emerald-500/40 p-3 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-emerald-400 uppercase font-semibold">Model Reliability Status</div>
                <div className="text-base font-bold text-emerald-200">HIGH RELIABILITY (92%)</div>
              </div>
              <ShieldCheck className="w-8 h-8 text-emerald-400" />
            </div>

            {/* Validation Metrics Grid */}
            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">MAE (Mean Abs Error)</div>
                <div className="text-base font-bold text-cyan-300">{DEMO_VALIDATION_METRICS.mae} °C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">RMSE (Root Mean Sq)</div>
                <div className="text-base font-bold text-cyan-300">{DEMO_VALIDATION_METRICS.rmse} °C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Mean Bias</div>
                <div className="text-base font-bold text-amber-400">{DEMO_VALIDATION_METRICS.bias} °C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Pearson R² Score</div>
                <div className="text-base font-bold text-emerald-400">{DEMO_VALIDATION_METRICS.r2}</div>
              </div>
            </div>

            {/* AI Bias Correction Performance */}
            <div className="bg-ocean-950/70 p-3 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-100">AI Bias Correction Performance</span>
                <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 text-[10px] font-mono border border-cyan-500/30">
                  +{DEMO_BIAS_CORRECTION.improvementPct}% Improved
                </span>
              </div>
              <ModelVsObsChart biasData={DEMO_BIAS_CORRECTION} />
            </div>

            {/* Factor Breakdown */}
            <div className="space-y-1.5">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Reliability Factors</div>
              {DEMO_RELIABILITY_DATA.factors.map((f, i) => (
                <div key={i} className="p-2 rounded bg-ocean-950/60 border border-slate-800 flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-slate-200">{f.name}</div>
                    <div className="text-[10px] text-slate-400">{f.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* FEATURE 07 & 08: OCEAN ANOMALY INSPECTOR */}
        {/* ========================================================= */}
        {activeDrawer === 'anomaly' && selectedAnomaly && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-amber-200 text-sm">{selectedAnomaly.locationName}</span>
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 font-bold border border-rose-500/30">
                  {selectedAnomaly.severity}
                </span>
              </div>
              <div className="text-slate-300 font-mono">
                Lat: {selectedAnomaly.lat}°N | Lon: {selectedAnomaly.lon}°E
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 font-mono text-center">
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Current Value</div>
                <div className="text-lg font-bold text-rose-400">{selectedAnomaly.currentValue}°C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Historical Baseline</div>
                <div className="text-lg font-bold text-slate-300">{selectedAnomaly.baselineValue}°C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Deviation</div>
                <div className="text-lg font-bold text-amber-400">+{selectedAnomaly.deviation}°C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Z-Score</div>
                <div className="text-lg font-bold text-cyan-400">+{selectedAnomaly.zScore} σ</div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* FEATURE 09 & 10: CURRENT TRAJECTORY SIMULATOR */}
        {/* ========================================================= */}
        {activeDrawer === 'trajectory' && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-ocean-950 border border-cyan-500/30 space-y-2">
              <div className="font-semibold text-cyan-300">Particle Drift Simulator Parameters</div>
              <div className="text-slate-400">
                Select duration and click any ocean location on the 3D globe to simulate current drift trajectory.
              </div>

              {/* Duration selector */}
              <div className="flex items-center gap-2 pt-2">
                <span className="text-[11px] text-slate-400 font-mono">Drift Hours:</span>
                {([6, 12, 24, 48] as const).map((dur) => (
                  <button
                    key={dur}
                    onClick={() => setTrajectoryDuration(dur)}
                    className={`px-2.5 py-1 rounded font-mono transition border ${
                      trajectoryDuration === dur
                        ? 'bg-cyan-500 text-ocean-950 font-bold border-cyan-400'
                        : 'bg-ocean-900 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    {dur}h
                  </button>
                ))}
              </div>

              <button
                onClick={() => setTrajectoryModeActive(true)}
                className="w-full py-2 rounded-lg bg-cyan-500 text-ocean-950 font-bold hover:bg-cyan-400 transition shadow-glow-cyan flex items-center justify-center gap-2 mt-2"
              >
                <MapPin className="w-4 h-4" />
                <span>Click Location on Globe to Run</span>
              </button>
            </div>

            {activeTrajectory && (
              <div className="space-y-3 pt-2">
                <div className="font-bold text-slate-100 flex items-center justify-between">
                  <span>Simulation Results</span>
                  <span className="text-[10px] font-mono text-cyan-400">{activeTrajectory.durationHours} Hours Path</span>
                </div>

                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div className="p-2 rounded bg-ocean-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Start Point</div>
                    <div className="text-slate-200 font-semibold">{activeTrajectory.startLat}°N, {activeTrajectory.startLon}°E</div>
                  </div>
                  <div className="p-2 rounded bg-ocean-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Est. End Point</div>
                    <div className="text-amber-400 font-semibold">{activeTrajectory.endLat}°N, {activeTrajectory.endLon}°E</div>
                  </div>
                  <div className="p-2 rounded bg-ocean-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Total Distance</div>
                    <div className="text-cyan-300 font-bold">{activeTrajectory.totalDistanceKm} km</div>
                  </div>
                  <div className="p-2 rounded bg-ocean-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Avg Drift Speed</div>
                    <div className="text-emerald-400 font-bold">{activeTrajectory.averageSpeedMps} m/s</div>
                  </div>
                </div>

                <div className="text-[10px] font-mono text-slate-400 bg-ocean-950 p-2 rounded border border-slate-800">
                  ⚠️ Disclaimer: Current-Based Estimated Trajectory (Frontend Demo Physics). Real hydrodynamic drift solver will connect in backend stage.
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* FEATURE 13: "EXPLAIN THIS REGION" INSIGHT PANEL */}
        {/* ========================================================= */}
        {activeDrawer === 'explain' && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/40 space-y-2">
              <div className="flex items-center gap-2 font-bold text-indigo-300">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>{selectedLocation.regionName}</span>
              </div>
              <p className="text-slate-300 leading-relaxed font-sans">{DEMO_REGIONAL_INSIGHT.summary}</p>
            </div>

            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-2 rounded bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Mean Temp</div>
                <div className="text-slate-100 font-bold">{DEMO_REGIONAL_INSIGHT.meanTemperature}°C</div>
              </div>
              <div className="p-2 rounded bg-ocean-950 border border-slate-800">
                <div className="text-[10px] text-slate-400">Mean Salinity</div>
                <div className="text-slate-100 font-bold">{DEMO_REGIONAL_INSIGHT.meanSalinity} PSU</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-ocean-950 border border-slate-800 space-y-2">
              <div className="text-[11px] font-semibold text-slate-400 uppercase">LLM Regional Engine Status</div>
              <div className="flex items-center gap-2 text-amber-400 font-mono text-[11px]">
                <Clock className="w-3.5 h-3.5" />
                <span>Awaiting LLM Service FastAPI Endpoint Integration</span>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* FEATURE 14: OCEAN REPORT GENERATOR */}
        {/* ========================================================= */}
        {activeDrawer === 'report' && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-ocean-950 border border-slate-800 space-y-3">
              <div className="font-semibold text-slate-100">Configure Ocean Report</div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Target Region</label>
                <input
                  type="text"
                  readOnly
                  value={selectedLocation.regionName}
                  className="w-full bg-ocean-900 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 font-mono text-xs"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Report Components</label>
                <div className="space-y-1 font-mono text-[11px]">
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Temperature & Salinity Grids</div>
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Argo CTD Profiles</div>
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Validation MAE/RMSE Summary</div>
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Anomaly Z-Score Alerts</div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-2 pt-1">
                <button
                  onClick={() => setReportGenerated(true)}
                  className="w-full py-2.5 rounded-lg bg-cyan-500 text-ocean-950 font-bold hover:bg-cyan-400 transition shadow-glow-cyan flex items-center justify-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  <span>Generate Ocean Intelligence PDF</span>
                </button>

                <button
                  onClick={handleDownloadGeoJSON}
                  className="w-full py-2 rounded-lg bg-ocean-900/80 hover:bg-slate-800 text-cyan-300 font-semibold border border-cyan-500/30 transition flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Regional GeoJSON Dataset</span>
                </button>
              </div>

              {reportGenerated && (
                <div className="p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-mono text-center text-[11px]">
                  ✓ Synthetic Report Draft Generated (Placeholder Download)
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span>OCEANTWIN 3D UI</span>
        <span>LAT: {selectedLocation.lat}° | LON: {selectedLocation.lon}°</span>
      </div>
    </aside>
  );
}
