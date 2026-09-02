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
  AlertTriangle,
  MapPin,
  CheckCircle2,
  Clock,
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
    <aside className="absolute top-[72px] right-3 bottom-3 z-50 w-[calc(100%-24px)] max-w-md bg-navy-deep border-2 border-navy-sky rounded-xl p-3.5 sm:p-4 shadow-panel text-navy-ice overflow-y-auto flex flex-col justify-between select-none">
      {/* Drawer Header */}
      <div>
        <div className="flex items-center justify-between border-b border-navy-ocean/50 pb-3 mb-4">
          <div className="flex items-center gap-2">
            {activeDrawer === 'argo' && <Radio className="w-5 h-5 text-navy-sky" />}
            {activeDrawer === 'validation' && <Activity className="w-5 h-5 text-navy-sky" />}
            {activeDrawer === 'bias' && <Cpu className="w-5 h-5 text-navy-sky" />}
            {activeDrawer === 'anomaly' && <AlertTriangle className="w-5 h-5 text-navy-sky" />}
            {activeDrawer === 'trajectory' && <Navigation className="w-5 h-5 text-navy-sky" />}
            {activeDrawer === 'explain' && <Sparkles className="w-5 h-5 text-navy-sky" />}
            {activeDrawer === 'report' && <FileText className="w-5 h-5 text-navy-sky" />}

            <h2 className="text-sm font-heading font-bold tracking-wider text-navy-ice uppercase">
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
            className="p-1 rounded-lg bg-navy-darker hover:bg-navy-ocean text-navy-muted hover:text-navy-ice transition border border-navy-ocean/40"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Provenance Notice Banner inside Drawer */}
        <div className="mb-4 px-3 py-2 rounded-lg bg-navy-darker border border-navy-sky/40 text-navy-ice text-[11px] font-mono flex items-center justify-between">
          <span className="font-semibold">{provenanceMode}</span>
          <span className="text-[10px] text-navy-muted">Backend API Pending</span>
        </div>

        {/* ========================================================= */}
        {/* ARGO OBSERVATION STATION DETAILS */}
        {/* ========================================================= */}
        {activeDrawer === 'argo' && selectedArgo && (
          <div className="space-y-4 text-xs font-sans">
            <div className="bg-navy-darker p-3 rounded-xl border border-navy-ocean/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-heading font-bold text-navy-ice text-sm">{selectedArgo.id}</span>
                <span className="px-2 py-0.5 rounded bg-navy-ocean text-navy-ice border border-navy-sky/50 font-mono text-[10px]">
                  {selectedArgo.qualityStatus}
                </span>
              </div>
              <div className="text-navy-muted font-medium">{selectedArgo.name}</div>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-navy-ocean/40 text-navy-ice font-mono">
                <div>Lat: <strong className="text-navy-ice">{selectedArgo.lat}°N</strong></div>
                <div>Lon: <strong className="text-navy-ice">{selectedArgo.lon}°E</strong></div>
                <div>Surface Temp: <strong className="text-navy-sky">{selectedArgo.surfaceTemp}°C</strong></div>
                <div>Salinity: <strong className="text-navy-ice">{selectedArgo.surfaceSalinity} PSU</strong></div>
              </div>
            </div>

            {/* CTD Depth Profile Chart */}
            <div>
              <div className="text-[11px] font-mono font-semibold text-navy-muted uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>In-Situ CTD Depth Profile (0 - 2,000m)</span>
              </div>
              <VerticalProfileChart profileData={selectedArgo.profileData} floatName={selectedArgo.id} />
            </div>

            {/* Model vs Observation Match Section */}
            <div className="bg-navy-darker p-3 rounded-xl border border-navy-ocean/50 space-y-2">
              <div className="font-heading font-semibold text-navy-ice">Model vs Argo Point Match</div>
              <div className="grid grid-cols-3 gap-2 font-mono text-center">
                <div className="p-2 rounded bg-navy-deep border border-navy-ocean/40">
                  <div className="text-[10px] text-navy-muted">Model</div>
                  <div className="text-navy-ice font-bold">{DEMO_MODEL_OBS_MATCH.modelValue}°C</div>
                </div>
                <div className="p-2 rounded bg-navy-deep border border-navy-ocean/40">
                  <div className="text-[10px] text-navy-muted">Observed</div>
                  <div className="text-navy-sky font-bold">{DEMO_MODEL_OBS_MATCH.observedValue}°C</div>
                </div>
                <div className="p-2 rounded bg-navy-deep border border-navy-ocean/40">
                  <div className="text-[10px] text-navy-muted">Difference</div>
                  <div className="text-navy-ice font-bold">+{DEMO_MODEL_OBS_MATCH.difference}°C</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* MODEL VALIDATION & AI BIAS CORRECTION */}
        {/* ========================================================= */}
        {activeDrawer === 'validation' && (
          <div className="space-y-4 text-xs font-sans">
            {/* Reliability Badge */}
            <div className="bg-navy-darker border border-navy-sky/40 p-3 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-navy-muted uppercase font-mono font-semibold">Model Reliability Status</div>
                <div className="text-base font-heading font-bold text-navy-ice">HIGH RELIABILITY (92%)</div>
              </div>
              <ShieldCheck className="w-8 h-8 text-navy-sky" />
            </div>

            {/* Validation Metrics Grid */}
            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">MAE (Mean Abs Error)</div>
                <div className="text-base font-bold text-navy-ice">{DEMO_VALIDATION_METRICS.mae} °C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">RMSE (Root Mean Sq)</div>
                <div className="text-base font-bold text-navy-ice">{DEMO_VALIDATION_METRICS.rmse} °C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Mean Bias</div>
                <div className="text-base font-bold text-navy-sky">{DEMO_VALIDATION_METRICS.bias} °C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Pearson R² Score</div>
                <div className="text-base font-bold text-navy-ice">{DEMO_VALIDATION_METRICS.r2}</div>
              </div>
            </div>

            {/* AI Bias Correction Performance */}
            <div className="bg-navy-darker p-3 rounded-xl border border-navy-ocean/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-heading font-semibold text-navy-ice">AI Bias Correction Performance</span>
                <span className="px-2 py-0.5 rounded bg-navy-ocean text-navy-ice text-[10px] font-mono border border-navy-sky/40">
                  +{DEMO_BIAS_CORRECTION.improvementPct}% Improved
                </span>
              </div>
              <ModelVsObsChart biasData={DEMO_BIAS_CORRECTION} />
            </div>

            {/* Factor Breakdown */}
            <div className="space-y-1.5">
              <div className="text-[11px] font-mono font-semibold text-navy-muted uppercase tracking-wider">Reliability Factors</div>
              {DEMO_RELIABILITY_DATA.factors.map((f, i) => (
                <div key={i} className="p-2 rounded bg-navy-darker border border-navy-ocean/40 flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-navy-sky shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-navy-ice">{f.name}</div>
                    <div className="text-[10px] text-navy-muted">{f.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* OCEAN ANOMALY INSPECTOR */}
        {/* ========================================================= */}
        {activeDrawer === 'anomaly' && selectedAnomaly && (
          <div className="space-y-4 text-xs font-sans">
            <div className="p-3 rounded-xl bg-navy-darker border border-navy-sky/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-heading font-bold text-navy-ice text-sm">{selectedAnomaly.locationName}</span>
                <span className="px-2 py-0.5 rounded bg-navy-ocean text-navy-ice font-mono font-bold border border-navy-sky/50">
                  {selectedAnomaly.severity}
                </span>
              </div>
              <div className="text-navy-muted font-mono">
                Lat: {selectedAnomaly.lat}°N | Lon: {selectedAnomaly.lon}°E
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 font-mono text-center">
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Current Value</div>
                <div className="text-lg font-bold text-navy-ice">{selectedAnomaly.currentValue}°C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Historical Baseline</div>
                <div className="text-lg font-bold text-navy-muted">{selectedAnomaly.baselineValue}°C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Deviation</div>
                <div className="text-lg font-bold text-navy-sky">+{selectedAnomaly.deviation}°C</div>
              </div>
              <div className="p-2.5 rounded-lg bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Z-Score</div>
                <div className="text-lg font-bold text-navy-ice">+{selectedAnomaly.zScore} σ</div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* CURRENT TRAJECTORY SIMULATOR */}
        {/* ========================================================= */}
        {activeDrawer === 'trajectory' && (
          <div className="space-y-4 text-xs font-sans">
            <div className="p-3 rounded-xl bg-navy-darker border border-navy-ocean/50 space-y-2">
              <div className="font-heading font-semibold text-navy-ice">Particle Drift Simulator Parameters</div>
              <div className="text-navy-muted">
                Select duration and click any ocean location on the 3D globe to simulate current drift trajectory.
              </div>

              {/* Duration selector */}
              <div className="flex items-center gap-2 pt-2">
                <span className="text-[11px] text-navy-muted font-mono">Drift Hours:</span>
                {([6, 12, 24, 48] as const).map((dur) => (
                  <button
                    key={dur}
                    onClick={() => setTrajectoryDuration(dur)}
                    className={`px-2.5 py-1 rounded font-mono transition border ${
                      trajectoryDuration === dur
                        ? 'bg-navy-ocean text-navy-ice font-bold border-navy-sky'
                        : 'bg-navy-deep border-navy-ocean/40 text-navy-muted hover:border-navy-sky'
                    }`}
                  >
                    {dur}h
                  </button>
                ))}
              </div>

              <button
                onClick={() => setTrajectoryModeActive(true)}
                className="w-full py-2 rounded-lg bg-navy-ocean hover:bg-navy-sky/30 text-navy-ice font-bold border border-navy-sky transition flex items-center justify-center gap-2 mt-2"
              >
                <MapPin className="w-4 h-4 text-navy-sky" />
                <span>Click Location on Globe to Run</span>
              </button>
            </div>

            {activeTrajectory && (
              <div className="space-y-3 pt-2">
                <div className="font-heading font-bold text-navy-ice flex items-center justify-between">
                  <span>Simulation Results</span>
                  <span className="text-[10px] font-mono text-navy-sky">{activeTrajectory.durationHours} Hours Path</span>
                </div>

                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div className="p-2 rounded bg-navy-darker border border-navy-ocean/50">
                    <div className="text-[10px] text-navy-muted">Start Point</div>
                    <div className="text-navy-ice font-semibold">{activeTrajectory.startLat}°N, {activeTrajectory.startLon}°E</div>
                  </div>
                  <div className="p-2 rounded bg-navy-darker border border-navy-ocean/50">
                    <div className="text-[10px] text-navy-muted">Est. End Point</div>
                    <div className="text-navy-sky font-semibold">{activeTrajectory.endLat}°N, {activeTrajectory.endLon}°E</div>
                  </div>
                  <div className="p-2 rounded bg-navy-darker border border-navy-ocean/50">
                    <div className="text-[10px] text-navy-muted">Total Distance</div>
                    <div className="text-navy-ice font-bold">{activeTrajectory.totalDistanceKm} km</div>
                  </div>
                  <div className="p-2 rounded bg-navy-darker border border-navy-ocean/50">
                    <div className="text-[10px] text-navy-muted">Avg Drift Speed</div>
                    <div className="text-navy-sky font-bold">{activeTrajectory.averageSpeedMps} m/s</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* "EXPLAIN THIS REGION" INSIGHT PANEL */}
        {/* ========================================================= */}
        {activeDrawer === 'explain' && (
          <div className="space-y-4 text-xs font-sans">
            <div className="p-3 rounded-xl bg-navy-darker border border-navy-sky/40 space-y-2">
              <div className="flex items-center gap-2 font-heading font-bold text-navy-ice">
                <Sparkles className="w-4 h-4 text-navy-sky" />
                <span>{selectedLocation.regionName}</span>
              </div>
              <p className="text-navy-ice leading-relaxed font-sans">{DEMO_REGIONAL_INSIGHT.summary}</p>
            </div>

            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-2 rounded bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Mean Temp</div>
                <div className="text-navy-ice font-bold">{DEMO_REGIONAL_INSIGHT.meanTemperature}°C</div>
              </div>
              <div className="p-2 rounded bg-navy-darker border border-navy-ocean/50">
                <div className="text-[10px] text-navy-muted">Mean Salinity</div>
                <div className="text-navy-ice font-bold">{DEMO_REGIONAL_INSIGHT.meanSalinity} PSU</div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-navy-darker border border-navy-ocean/50 space-y-2">
              <div className="text-[11px] font-mono font-semibold text-navy-muted uppercase">LLM Regional Engine Status</div>
              <div className="flex items-center gap-2 text-navy-sky font-mono text-[11px]">
                <Clock className="w-3.5 h-3.5" />
                <span>Awaiting LLM Service FastAPI Endpoint Integration</span>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* OCEAN REPORT GENERATOR */}
        {/* ========================================================= */}
        {activeDrawer === 'report' && (
          <div className="space-y-4 text-xs font-sans">
            <div className="p-3 rounded-xl bg-navy-darker border border-navy-ocean/50 space-y-3">
              <div className="font-heading font-semibold text-navy-ice">Configure Ocean Report</div>

              <div>
                <label className="text-[10px] text-navy-muted block mb-1 font-mono">Target Region</label>
                <input
                  type="text"
                  readOnly
                  value={selectedLocation.regionName}
                  className="w-full bg-navy-deep border border-navy-ocean/60 rounded px-2.5 py-1.5 text-navy-ice font-mono text-xs"
                />
              </div>

              <div>
                <label className="text-[10px] text-navy-muted block mb-1 font-mono">Report Components</label>
                <div className="space-y-1 font-mono text-[11px]">
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-navy-sky" /> Temperature & Salinity Grids</div>
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-navy-sky" /> Argo CTD Profiles</div>
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-navy-sky" /> Validation MAE/RMSE Summary</div>
                  <div className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-navy-sky" /> Anomaly Z-Score Alerts</div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-2 pt-1">
                <button
                  onClick={() => setReportGenerated(true)}
                  className="w-full py-2.5 rounded-lg bg-navy-ocean hover:bg-navy-sky/30 text-navy-ice font-bold border border-navy-sky transition flex items-center justify-center gap-2 shadow-subtle"
                >
                  <FileText className="w-4 h-4 text-navy-sky" />
                  <span>Generate Ocean Intelligence PDF</span>
                </button>

                <button
                  onClick={handleDownloadGeoJSON}
                  className="w-full py-2 rounded-lg bg-navy-deep hover:bg-navy-ocean text-navy-ice font-semibold border border-navy-ocean/50 hover:border-navy-sky transition flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4 text-navy-sky" />
                  <span>Download Regional GeoJSON Dataset</span>
                </button>
              </div>

              {reportGenerated && (
                <div className="p-2.5 rounded-lg bg-navy-ocean/60 border border-navy-sky/50 text-navy-ice font-mono text-center text-[11px]">
                  ✓ Synthetic Report Draft Generated (Placeholder Download)
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-navy-ocean/50 text-[10px] text-navy-muted font-mono flex items-center justify-between">
        <span>OCEANTWIN 3D UI</span>
        <span>LAT: {selectedLocation.lat}° | LON: {selectedLocation.lon}°</span>
      </div>
    </aside>
  );
}
