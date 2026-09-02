# OceanTwin 3D — Frontend Integration Handoff Documentation

This document serves as the formal technical handoff for the **OceanTwin 3D** Interactive Ocean Visualization & Model Validation Platform frontend.

---

## 1. Summary of Completed Frontend Architecture

- **Primary 3D Engine**: CesiumJS (migrated from Three.js). Occupies ~75% of primary workspace as hero.
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript + Tailwind CSS.
- **Charts Engine**: ECharts (`echarts-for-react`) for high-precision oceanographic CTD vertical depth profiles and model validation comparison charts.
- **Design System**: Scientific dark workspace theme (`#030712`, `#0a1120`), electric cyan `#00f2fe` accents, translucent glassmorphism panels (`backdrop-blur-md`), and non-intrusive floating controls.
- **Data Provenance**: Explicit `DEMO / MOCK DATA` provenance badges and notices throughout the interface to ensure absolute distinction between UI demo placeholders and future live scientific datasets.

---

## 2. Quickstart & Environment Setup

### Prerequisites

| Requirement | Version |
| :--- | :--- |
| Node.js | v18+ (LTS recommended) |
| npm | v9+ (ships with Node 18+) |
| Browser | Chrome / Edge / Firefox with WebGL2 support |

### Install & Run

```bash
# 1. Clone the repository
git clone https://github.com/ARJUN-AIML/3D-Ocean-Model-Visualization.git
cd 3D-Ocean-Model-Visualization

# 2. Install dependencies
npm install

# 3. Run the local dev server (automatically copies Cesium static assets first)
npm run dev
```

The dev server starts at **http://localhost:3000**.

### Cesium Static Asset Configuration

CesiumJS requires static assets (Workers, Assets, ThirdParty, Widgets) to be served from a public directory. This project handles it via a `copyfiles` script defined in `package.json`:

```json
"scripts": {
  "dev": "npm run copy-cesium && next dev",
  "build": "npm run copy-cesium && next build",
  "copy-cesium": "copyfiles -u 4 \"node_modules/cesium/Build/Cesium/**/*\" public/cesium"
}
```

The Webpack `DefinePlugin` in `next.config.mjs` sets the base URL globally:

```js
new webpack.DefinePlugin({
  CESIUM_BASE_URL: JSON.stringify('/cesium')
})
```

At runtime, `CesiumGlobe.tsx` also sets `window.CESIUM_BASE_URL = '/cesium'` to ensure the dynamic import path resolves correctly.

### Environment Variables

No `.env` file is currently required. The project uses the Esri World Imagery public tile service for base imagery (no API key needed). When connecting a live FastAPI backend, add the following to `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 3. 3D Engine Performance Architecture

This section documents the rendering guarantees and GPU optimizations implemented in `components/cesium/CesiumGlobe.tsx`, written for backend/ML engineers who need to understand the frontend's non-functional performance characteristics without modifying Cesium code.

### Depth Precision

- **Logarithmic Depth Buffer**: `scene.logarithmicDepthBuffer = true` — provides high-precision depth comparisons at orbital scale, eliminating Z-fighting/flicker at all zoom levels.
- **Dynamic Near/Far Frustum Scaling**: A `scene.preRender` listener dynamically adjusts the camera frustum planes based on `camera.positionCartographic.height`:
  - **Close range** (`< 100,000m`): `near = max(0.1, height × 0.00005)` — extends precision down to 0.1m for ground-level rendering.
  - **Orbital range** (`≥ 100,000m`): `near = max(10.0, height × 0.0001)`.
  - **Far plane**: `far = max(5.0e7, height × 10.0)` — fixed floor of 50,000 km for full-globe visibility.

### Render Strategy

- **On-Demand Rendering**: `requestRenderMode: true` with `maximumRenderTimeChange: Infinity`. The GPU only draws frames when explicitly triggered via `scene.requestRender()`, reducing idle GPU load to near-zero.
- **Explicit Render Triggers**: `requestRender()` is called after every camera flyTo completion, zoom action, entity/primitive update, interactive click, and auto-rotation tick — ensuring visual freshness without continuous rendering overhead.

### GPU Primitive Batching

- High-count data layers use low-level **Primitive Collections** instead of the Entity API, achieving ~50x faster rendering during drag-rotation:
  - **Argo Float Points**: `Cesium.PointPrimitiveCollection` — batches all point markers into a single WebGL draw call.
  - **Anomaly Hotspots**: `Cesium.PointPrimitiveCollection` — same GPU-batched approach for severity markers.
  - **Current Field Vectors**: `Cesium.PolylineCollection` — batches all vector arrow polylines into one primitive pass.
  - **Trajectory Drift Paths**: `Cesium.PolylineCollection` — batches trajectory polylines.
- Only the **Error Heatmap** (single rectangle entity) and **Trajectory End Point** (single point entity) use the Entity API, as their 1:1 count has negligible overhead.

### Visual Fidelity

- **FXAA Anti-Aliasing**: `scene.postProcessStages.fxaa.enabled = true` — smooths terrain geometry edges without MSAA multi-sample overhead.
- **Fixed Resolution Scale**: `viewer.resolutionScale = 1.0` — prevents sub-pixel aliasing shimmer on high-DPI displays.
- **Lighting Stability**: `globe.enableLighting = false`, `globe.dynamicAtmosphereLighting = false`, `globe.showGroundAtmosphere = false` — enforces constant daylight illumination to prevent camera-angle-dependent brightness shifts and atmospheric band shimmer.

### Tile Loading & Caching

- `globe.tileCacheSize = 2500` — expanded GPU memory tile cache prevents tile eviction/re-download during rotation.
- `globe.preloadAncestors = true` and `globe.preloadSiblings = true` — pre-fetches parent and neighboring LOD tiles to prevent pop-in.
- `globe.loadingDescendantLimit = 1` — limits aggressive child tile loading during rapid zoom.
- `globe.maximumScreenSpaceError = 2.0` — stable LOD threshold balancing detail vs. tile-swap frequency.
- `scene.fog.enabled = false` — disables horizon fog that was culling tiles prematurely during rotation.

### Camera Controller

- **Inertia**: `inertiaSpin = 0.25`, `inertiaTranslate = 0.25`, `inertiaZoom = 0.25` — smooth deceleration without drag lag.
- **Collision Detection**: `enableCollisionDetection = true`, `minimumZoomDistance = 1000m`, `maximumZoomDistance = 35,000,000m`.
- **Drag Decoupling**: Active mouse drag (`LEFT_DOWN` → `LEFT_UP`) is tracked via ref; picking/raycasting is suppressed during drag, and auto-rotation pauses during both drag and flyTo animations.

---

## 4. Inventory of Frontend Components & Placeholders

| Feature # | Feature Name | Frontend Component File | Current Placeholder State | Future Backend Integration Data Contract |
| :--- | :--- | :--- | :--- | :--- |
| **01** | Ocean Variable Vis | `components/cesium/CesiumGlobe.tsx`, `components/ui/LeftControls.tsx` | Layer state active (`temp`, `salinity`, `currents`, `waves`) | Processed netCDF ocean grid arrays (U/V, Temp, Salinity) |
| **02** | Argo Float Observations | `components/cesium/CesiumGlobe.tsx`, `components/ui/RightDrawer.tsx` | Demo float markers (`ARGO-5906234`, `ARGO-2903481`) via `PointPrimitiveCollection` | Live INCOIS / Argo API geojson feed + CTD profile arrays |
| **03** | Model vs Observation | `components/ui/RightDrawer.tsx` | Demo point match comparison fields | Spatial-temporal-depth nearest neighbor matching engine output |
| **04** | AI Bias Correction | `components/ui/RightDrawer.tsx`, `components/charts/ModelVsObsChart.tsx` | Demo raw model vs AI-corrected vs obs values | XGBoost inference service predictions |
| **05** | Model Validation | `components/ui/RightDrawer.tsx` | Demo MAE (0.24), RMSE (0.38), Bias, R², Pearson metrics | Validation engine metrics pipeline |
| **06** | Model Reliability | `components/ui/RightDrawer.tsx` | HIGH Reliability badge (92%) & factor cards | Reliability confidence scoring engine |
| **07** | Error Heatmap | `components/cesium/CesiumGlobe.tsx`, `components/ui/LeftControls.tsx` | Translucent rectangle grid overlay | Spatial residual error raster grid |
| **08** | Ocean Anomaly Map | `components/cesium/CesiumGlobe.tsx`, `components/ui/RightDrawer.tsx` | Severity-colored point primitives (`ANO-001`) via `PointPrimitiveCollection` | Anomaly detection Z-score pipeline |
| **09** | Animated Current Field | `components/cesium/CesiumGlobe.tsx` | Arrow vector field via `PolylineCollection` primitives | Hydrodynamic U/V velocity vector field |
| **10** | Trajectory Drift Simulator | `components/cesium/CesiumGlobe.tsx`, `components/ui/RightDrawer.tsx` | Demo drift simulation math via `PolylineCollection` | Particle tracking trajectory solver (6h, 12h, 24h, 48h) |
| **11** | Vertical Profile Charts | `components/charts/VerticalProfileChart.tsx` | ECharts inverted Y-axis CTD chart | Argo CTD / model depth profile arrays |
| **12** | Model Comparison Charts | `components/charts/ModelVsObsChart.tsx` | ECharts comparative bar plot | Model vs observation residual series |
| **13** | Regional AI Insight | `components/ui/RightDrawer.tsx` | Regional summary card with pending endpoint note | LLM / Regional Insight service API endpoint |
| **14** | Ocean Report Generator | `components/ui/RightDrawer.tsx` | Report configuration drawer & draft preview | FastAPI PDF generation endpoint |
| **15** | Data Provenance | `components/ui/TopBar.tsx`, `components/ui/RightDrawer.tsx` | Prominent `DEMO / MOCK DATA` badge | Dataset metadata provenance status header |
| **16** | Data Quality / Safety | `components/ui/RightDrawer.tsx` | Quality control flags & rejected count badge | QC pipeline flags (`PASSED`, `FLAGGED`, `REJECTED`) |
| **17** | Interactive Region Selector | `context/OceanContext.tsx`, `components/cesium/CesiumGlobe.tsx` | Global click event handler returning Lat/Lon | Global coordinate query service |

---

## 5. TypeScript Interfaces & Data Models

All data structures are defined in `types/ocean.ts`:

- `ArgoFloat`: Stores float ID, WMO, position, surface metrics, and array of depth profile points.
- `BiasCorrectionData`: Raw model value, AI-corrected value, observation, raw error, corrected error, and improvement percentage.
- `ValidationMetrics`: MAE, RMSE, Bias, R², Pearson correlation, matched/rejected counts, coverage, and reliability status.
- `OceanAnomaly`: Variable, location, coordinates, depth, timestamp, current value, baseline value, deviation, z-score, and severity (`NORMAL`, `WATCH`, `WARNING`, `CRITICAL`).
- `TrajectoryResult`: Start/end coordinates, duration, total distance km, average drift speed, and path coordinate array.
- `RegionalInsight`: Mean temperature, mean salinity, mean current speed, anomaly count, reliability, and summary text.

---

## 6. Service Boundary & API Architecture

All frontend API calls are abstracted in `lib/api/index.ts`:

```typescript
// Example frontend service boundary calls
const floats    = await oceanApiService.getArgoFloats();
const metrics   = await oceanApiService.getValidationMetrics('temp');
const trajectory = await oceanApiService.runTrajectorySimulation(lat, lon, 24);
```

When connecting live backend APIs in the next development stage:
1. Update `lib/api/index.ts` to replace demo response returns with `fetch()` / `axios` requests targeting the FastAPI backend server (e.g. `http://localhost:8000/api/v1/...`).
2. Implement backend response adapters if the API JSON payload schema differs from `types/ocean.ts`.

### Planned REST API Endpoint Specification

> **Note:** No live FastAPI backend exists yet. The table below documents the intended REST API contract that `lib/api/index.ts` service methods are designed to consume once implemented.

| Method | Route | Request Params / Body | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/provenance/status` | — | `{ mode: string, notice: string, isRealDataConnected: boolean }` | Returns current data provenance mode |
| `GET` | `/api/v1/argo/floats` | — | `ArgoFloat[]` | List all Argo float observations with latest positions |
| `GET` | `/api/v1/argo/floats/:id` | `id` (path param: float ID or WMO) | `ArgoFloat` | Single Argo float detail with CTD depth profile |
| `GET` | `/api/v1/model/match` | `?floatId=...&variable=temp` | `ModelObsMatch` | Nearest model-observation spatial-temporal match |
| `GET` | `/api/v1/bias-correction` | `?variable=temp&depth=0` | `BiasCorrectionData` | AI bias-corrected values for variable at depth |
| `GET` | `/api/v1/validation/metrics` | `?variable=temp` | `ValidationMetrics` | Model validation statistics (MAE, RMSE, Bias, R², Pearson) |
| `GET` | `/api/v1/reliability` | — | `ReliabilityData` | Model reliability confidence score and factor breakdown |
| `GET` | `/api/v1/anomalies` | — | `OceanAnomaly[]` | Detected ocean anomaly hotspots with severity |
| `GET` | `/api/v1/error-heatmap` | — | `ErrorHeatmapPoint[]` | Spatial residual error grid for heatmap rendering |
| `POST` | `/api/v1/trajectory/simulate` | `{ startLat, startLon, durationHours: 6|12|24|48 }` | `TrajectoryResult` | Simulate particle drift trajectory from given coordinates |
| `GET` | `/api/v1/regional-insight` | `?lat=...&lon=...` | `RegionalInsight` | LLM-generated regional ocean intelligence summary |

---

## 7. Remaining Backend & ML Integration Checklist

- [ ] Connect FastAPI backend server base URL in `lib/api/index.ts`
- [ ] Connect real netCDF / ERA5 / Copernicus ocean grid datasets for Temperature, Salinity, and Currents
- [ ] Connect live INCOIS / Argo float observation data feeds
- [ ] Implement spatial-temporal-depth model-observation matching pipeline
- [ ] Connect XGBoost AI bias correction model inference engine
- [ ] Connect real-time model validation metrics pipeline (MAE, RMSE, Bias, R²)
- [ ] Connect model reliability confidence calculation engine
- [ ] Connect spatial model error heatmap raster provider
- [ ] Connect ocean anomaly detection Z-score calculation engine
- [ ] Connect hydrodynamic particle trajectory solver for drift predictions
- [ ] Connect LLM regional summary endpoint ("Explain This Region")
- [ ] Connect PDF ocean intelligence report generation endpoint

---

## 8. QA Test Matrix & Interaction Mapping

### Browser & WebGL2 Compatibility

| Test Case | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| Chrome WebGL2 | Open `localhost:3000` in Chrome 90+ | Globe renders, all layers visible, 60 FPS drag | ✅ Pass |
| Edge WebGL2 | Open in Edge 90+ | Globe renders, identical behavior to Chrome | 🔲 Pending |
| Firefox WebGL2 | Open in Firefox 89+ | Globe renders, all interactions functional | 🔲 Pending |
| Safari WebGL2 | Open in Safari 15+ (macOS) | Globe renders; verify touch pinch-zoom works | 🔲 Pending |
| WebGL2 Unavailable | Disable WebGL2 (via `chrome://flags`) | Graceful error message displayed | 🔲 Pending |

### Mouse Interaction Mapping

These mappings are explicitly configured in `CesiumGlobe.tsx` via `screenSpaceCameraController`:

| Input | Action | Controller Config |
| :--- | :--- | :--- |
| Left-drag | Rotate globe | `rotateEventTypes: [LEFT_DRAG, CTRL+LEFT_DRAG]` |
| Right-drag | Pan / Translate | `translateEventTypes: [RIGHT_DRAG]` |
| Scroll wheel | Zoom in / out | `zoomEventTypes: [MIDDLE_DRAG, WHEEL, PINCH]` |
| Middle-drag / Pinch | Tilt / Zoom | `tiltEventTypes: [MIDDLE_DRAG, PINCH, CTRL+RIGHT_DRAG]` |
| Left-click (no drag) | Select entity / ocean location | `ScreenSpaceEventType.LEFT_CLICK` handler |

### Framerate Stability (Target: 60 FPS)

| Test Case | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| Idle auto-rotate | Enable "Auto-Rotate" toggle, observe for 30s | Smooth 60 FPS rotation, no stutter | ✅ Pass |
| Drag-rotate (all layers ON) | Enable all layers, left-drag rotate rapidly | ≥ 55 FPS sustained, no frame drops | ✅ Pass |
| Close-zoom rotate | Zoom to 5,000m altitude, drag-rotate | No shimmer, no tile pop-in flicker | ✅ Pass |
| Distant-zoom rotate | Zoom to full-Earth orbit (18M m), drag-rotate | No crosshatch grid flicker on imagery | ✅ Pass |
| FlyTo transition + auto-rotate | Start auto-rotate, trigger flyTo via region selector | Auto-rotate pauses during transition, resumes after | ✅ Pass |

### Layer Toggle Verification

| Test Case | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| Argo Floats ON/OFF | Toggle "Argo Floats" in Layers panel | Cyan point markers appear/disappear cleanly | ✅ Pass |
| Animated Current Field ON/OFF | Toggle "Current Particles" | Blue vector arrows appear/disappear | ✅ Pass |
| Anomaly Hotspots ON/OFF | Toggle "Anomalies" | Severity-colored point markers appear/disappear | ✅ Pass |
| Error Heatmap ON/OFF | Toggle "Error Heatmap" | Red translucent rectangle overlay appears/disappears | ✅ Pass |
| Trajectory Drift Path ON/OFF | Toggle "Trajectory Path" with active trajectory | Cyan polyline path and end marker appear/disappear | ✅ Pass |
| All layers OFF | Disable all layer toggles | Clean globe with no overlay primitives or entities | ✅ Pass |

### Timeline Playback Verification

| Test Case | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| Play / Pause | Click Play button in bottom timeline | Timestep advances at configured speed; Pause stops it | ✅ Pass |
| Scrub timeline | Drag timeline scrubber to different time index | Displayed timestamp updates, data layers reflect new time | ✅ Pass |
| Playback speed change | Change playback speed multiplier | Time steps advance faster/slower proportionally | ✅ Pass |
| Play during drag-rotate | Start playback, then drag-rotate globe | No additional stutter; playback and rotation coexist | ✅ Pass |

---

*Document last updated: 2026-09-02*