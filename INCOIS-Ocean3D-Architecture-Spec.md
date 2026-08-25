# INCOIS 3D Ocean Data Visualization Platform — Architecture Specification
**Problem Statement 26067 | MoES / INCOIS | Disaster Management**

---

## 1. Executive Summary

In engineering terms, this problem is a **multidimensional scientific data delivery and rendering problem**, not a graphics problem. The hard part is not "make a 3D ocean" — it's getting gridded 4D fields (time × depth × lat × lon) and irregular point/profile observations (Argo, Gliders) out of NetCDF archives, through a bandwidth- and memory-constrained browser, and onto the GPU as something a forecaster can interactively query, fast enough to feel live.

The platform must do three things well:
1. **Ingest and normalize** heterogeneous ocean data (gridded model output + irregular in-situ profiles) into a canonical, queryable form.
2. **Serve** thin, pre-reduced slices of that data over a REST API so the browser never touches a raw multi-GB NetCDF file.
3. **Render** those slices as interactive 3D/geospatial visualizations (depth slices, isosurfaces, vector/particle currents, instrument overlays) with real-time controls, at a frame rate usable on a normal laptop GPU.

Public-outreach usability and operational-forecaster usability are different UX modes on top of the same data layer, not different systems.

---

## 2. Requirements Analysis

**Functional**
- Render model fields (T, S, u/v/w, chlorophyll) as depth slices, isosurfaces, vector/particle fields.
- Overlay Argo/Glider/CTD/BGC observations as geolocated markers; click → profile viewer.
- Time-step animation; depth navigation; variable/colorbar/opacity/vertical-exaggeration controls.
- Ingest NetCDF/ASCII/delimited sources via pluggable parsers.
- Compare model vs. observation at a point (nearest/interpolated).

**Non-functional**
- Browser-native, no desktop scientific software dependency.
- Must run on commodity dev laptops during development (open-source only).
- Must degrade gracefully on modest GPUs (education/exhibition use case).

**Scientific**
- CF-Convention-compliant variable/coordinate semantics; correct handling of missing values, masks, units, depth conventions (positive-down vs positive-up), and grid type (regular lat/lon vs curvilinear).

**Visualization**
- Depth slice, isosurface, vector field, particle advection, colorbar mapping, LOD.

**Scalability**
- Must scale from a single demo NetCDF file (MVP) to routinely-updated multi-GB archives (production) without a rewrite — via chunked/tiled access, not by assuming small data.

**Extensibility**
- New variable or instrument type addable by writing a new ingestion adapter + registering metadata, not by touching rendering code.

**Security**
- Internal-tool-grade auth (not public internet-grade) is a reasonable MVP assumption; upload validation and rate limiting matter regardless because NetCDF parsing is a known attack surface (malformed files, decompression bombs).

**Deployment**
- Must run via Docker Compose locally/for demo; institutional deployment is an unknown (see §3).

---

## 3. Assumptions and Unknowns

**Explicitly assumed (mark all as ASSUMPTION, not fact):**
- ASSUMPTION: Model output grids are regular lat/lon/depth/time NetCDF, CF-convention-ish, similar to typical INCOIS/ROMS/HYCOM-class ocean model output. Curvilinear grids are NOT assumed as the primary case but the ingestion layer must not hard-fail on them.
- ASSUMPTION: A single demo dataset is on the order of 10s–100s of MB to a few GB (not TB-scale); full operational archive size is unknown.
- ASSUMPTION: Time resolution is daily-to-hourly; depth resolution is tens of levels (not thousands).
- ASSUMPTION: Coordinate system is WGS84 lat/lon with depth in meters, positive-down.
- ASSUMPTION: Argo/Glider counts for a demo are in the hundreds-to-low-thousands of profiles, not millions.
- ASSUMPTION: Concurrent users for a competition/demo context: single-digit to low tens. Production concurrency is UNKNOWN.
- UNKNOWN: Real INCOIS infrastructure (on-prem vs cloud, GPU availability server-side, OPeNDAP server availability, existing THREDDS/ERDDAP deployment). Do not assume any of this exists — design the API layer to optionally sit in front of an OPeNDAP/THREDDS server later, but implement direct xarray-based serving first.
- UNKNOWN: Whether INCOIS already exposes any of this data via WMS/WCS. Do not invent such an API.
- Do not treat any of the above as fact in the implementation plan — they are design defaults, override-able per real dataset.

---

## 4. Technology Evaluation

| Candidate | Strength | Weakness | Verdict |
|---|---|---|---|
| **React + TypeScript** | Mature, huge ecosystem, typed contracts with backend | None material | **Selected** |
| **Three.js / React Three Fiber + drei** | Full control of custom GPU shaders for volumetric/isosurface rendering; lightweight | More manual work than a geospatial-first engine for globe-scale geo accuracy | **Selected — primary 3D engine** |
| **CesiumJS** | Best-in-class globe-scale geospatial accuracy, terrain, imagery basemaps | Heavy, opinionated scene graph, awkward to combine with custom volumetric shaders; two full engines in one app is a maintenance trap | **Selected — but only for the 2D/3D basemap + geolocation layer, not for volumetric rendering** (see decision below) |
| **Zustand** | Minimal, unopinionated global state, ideal for "current variable/depth/time" UI state | Not for large data caching | **Selected** for UI state only |
| **Plotly.js** | Battle-tested scientific 2D charts (depth-vs-variable profiles) | Not for 3D volumetric | **Selected** for ProfileViewer only |
| **FastAPI + Pydantic + Uvicorn** | Async, typed request/response contracts, good fit for scientific APIs, auto OpenAPI docs | None material for this scale | **Selected** |
| **xarray + netCDF4/h5netcdf** | Standard for labeled multidimensional scientific arrays, CF-aware | Needs care with memory on large files | **Selected**, with lazy/chunked access |
| **Dask** | Enables chunked/parallel/out-of-core processing of arrays too large for memory | Adds operational complexity if data is actually small | **Selected but optional-at-MVP** — wire the interface so it can be dropped in later; don't force it into the MVP path if the demo dataset is small |
| **Zarr** | Efficient chunked storage, great for repeated slice queries and caching | Extra ingestion step; not needed if NetCDF-direct reads are fast enough | **Selected as an optional preprocessing/cache format**, not a hard requirement |
| **PostgreSQL + PostGIS** | Ideal for observation metadata (Argo/Glider positions, times) with spatial queries | Wrong tool for gridded arrays | **Selected for metadata/observations only** |
| **Object storage (local disk / MinIO/S3-compatible)** | Right place for raw NetCDF + Zarcache | N/A | **Selected** |
| **Redis** | Fast cache for hot slice queries | Adds an extra moving part | **Selected but optional-at-MVP** — justified only once slice-caching becomes a measured bottleneck |
| **Turf.js** | Handy geospatial helper functions in-browser | Not core | **Optional, use only if needed** |

**Decision — Three.js vs CesiumJS (must be explicit):** Three.js/R3F is the **primary rendering engine** for volumetric fields, isosurfaces, vector/particle currents — this is custom GPU work Cesium isn't built for. CesiumJS is **not used** in the MVP; it is a **future option** for a globe-basemap "situational awareness" view if INCOIS later wants a Google-Earth-style entry screen. Running both in one scene graph is explicitly rejected as over-engineering (violates principle H). A flat/regional map (e.g., MapLibre or a simple lat/lon-projected plane inside the Three.js scene) is sufficient for INCOIS's EEZ-scale (not whole-globe) use case.

**Final recommended stack:** React + TypeScript + React Three Fiber/drei + Zustand + Plotly.js (frontend) · FastAPI + Pydantic + xarray + NumPy (backend) · PostgreSQL/PostGIS for metadata · local/object storage for NetCDF + optional Zarr cache · Dask/Redis added later only if measurements justify them.

---

## 5. High-Level System Architecture

```
Browser (React/R3F)
   │  REST/JSON (thin slices, not raw arrays)
   ▼
API Layer (FastAPI)
   │
   ├─→ Scientific Processing Layer (xarray/NumPy) ── reads ──▶ Storage
   │         (slicing, interpolation, isosurface prep,
   │          model-vs-obs comparison)
   │
   ├─→ Metadata/Observation Service ──▶ PostgreSQL/PostGIS
   │         (Argo/Glider/CTD/BGC records, dataset registry)
   │
   └─→ Cache Layer (in-process / Redis later) ── in front of ──▶ Zarr/object storage/NetCDF

Ingestion Pipeline (offline/batch, separate from request path)
   Raw NetCDF/ASCII → Validation → xarray normalization → CF metadata check
        → optional Zarr rechunk → Storage + PostgreSQL metadata registration
```

Caching sits between the scientific processing layer and storage (slice-level cache keyed by variable/time/depth/bbox). Preprocessing/normalization happens only in the ingestion pipeline, never on the request path. Authentication, logging, and monitoring are cross-cutting middleware in the API layer, not separate services (avoids over-engineering per principle H).

---

## 6. Frontend Architecture

**State split (critical decision):** Zustand holds *only* UI/selection state (current variable, depth, time index, colorbar range, selected instrument). It never holds large arrays. Fetched data lives in component-local state / a lightweight data-fetching cache (e.g., a query cache), keyed by request parameters, with LRU eviction.

Module boundaries:
- `OceanScene` — top-level R3F canvas, owns camera/lighting/basemap plane.
- `OceanSurface`, `DepthSlice`, `Isosurface`, `CurrentVectors`, `CurrentParticles` — pure rendering components; each takes typed, pre-shaped data props (never fetches directly).
- `ArgoLayer`, `GliderLayer` — geolocated marker layers; click emits an event, doesn't own profile-fetch logic itself.
- `ProfileViewer` — Plotly-based 2D panel, opened on marker click.
- `Timeline`, `VariableSelector`, `ColorbarControl`, `DepthControl`, `LayerControl`, `DatasetSelector`, `MetadataPanel` — control components; write to Zustand only.
- A thin `data/` layer (hooks) is the *only* place that calls the API and owns loading/error state — rendering components stay dumb and testable.

This separation (control state vs. fetched data vs. pure rendering) is what makes the app testable and lets Antigravity implement pieces independently.

---

## 7. 3D Rendering Architecture

| Concern | Where it happens | Why |
|---|---|---|
| A. Depth slices | Server extracts 2D slice at requested depth/time; browser just textures a plane | Never ship the full 3D array for one slice |
| B. Volume rendering | Server pre-downsamples to a coarse 3D texture (e.g., 64³–128³); GPU ray-marches it in a fragment shader | Full-res volumetric ray-marching of raw model resolution is not real-time in-browser; downsampling is the correct engineering trade-off, not a shortcut |
| C. Isosurfaces | Server computes marching-cubes on the (already downsampled) grid, returns a mesh (vertices/faces) or the browser runs marching-cubes on a small pre-fetched sub-volume for interactivity | Full marching-cubes on raw grid resolution client-side only if the sub-volume is small |
| D. Vector fields | Server subsamples vectors to a renderable density (e.g., every Nth grid point); browser draws instanced arrows/lines | Rendering one arrow per raw grid cell is never useful visually and wastes GPU |
| E. Particle advection | Server precomputes or streams a velocity field texture; browser advects particles per-frame in a compute-like shader (GPGPU via render-to-texture) | This is inherently a GPU/browser job once the velocity field is available |
| F. Vertical exaggeration | Pure browser-side scale transform on Z | Trivial, no server cost |
| G. Color mapping | Browser shader (LUT texture); server only sends raw values + min/max | Keeps recoloring free of network round-trips |
| H. Opacity | Browser shader uniform | Same reason |
| I. Time animation | Browser pre-fetches a short window of nearby time steps (prefetch cache); server serves each step as a thin slice | Avoids stutter without shipping the whole time series |
| J. LOD | Server-side: multiple pre-computed downsample levels selectable by camera distance/zoom | Classic LOD, server does the heavy resampling once |
| K. GPU acceleration | Shaders for volume ray-march, particle advection, color mapping | This is inherent to the visuals, not optional |
| L. Web Workers | Parsing API responses, marching-cubes on client sub-volumes, interpolation math | Keeps the main thread free for 60fps rendering |

**Explicit rule:** the browser never receives a raw multi-dimensional NetCDF-scale array. Every payload is a request-scoped, already-reduced slice/mesh/texture.

---

## 8. Ocean Data Architecture (Canonical Representation)

Canonical in-memory model (xarray `Dataset`), CF-convention-aligned:

- Dimensions: `time`, `depth`, `lat`, `lon` (regular grid case).
- Coordinates: `time` (ISO8601/UTC), `depth` (meters, positive-down, documented explicitly since sign convention is a common bug source), `lat`/`lon` (WGS84 decimal degrees).
- Data variables: `temperature` (°C), `salinity` (PSU), `u`, `v`, `w` (m/s), `chlorophyll` (mg/m³) — each carries CF `standard_name`, `units`, `_FillValue`/mask.
- Missing values: represented as NaN internally after ingestion; `_FillValue` never leaks to the API as a magic number — API returns `null`.
- Grid type is recorded in dataset metadata (`grid_type: regular | curvilinear`) so downstream slicing code can branch rather than assume.

---

## 9. NetCDF Ingestion Architecture

```
NetCDF file → structural validation (open with xarray, check required dims/vars exist)
   → CF-compliance check (units, standard_name present; warn not fail if missing)
   → normalization (rename to canonical variable names, fix depth sign convention)
   → chunking decision (open with dask-backed chunks if file exceeds an in-memory threshold)
   → optional rechunk to Zarr for repeated-access datasets
   → register in PostgreSQL dataset/variable registry (bbox, time range, depth range, variable list)
```
- Chunking: chunk along `time` first for animation-heavy access patterns, `depth` second.
- Compression: rely on NetCDF4's native compression on read; Zarr cache uses blosc/zstd.
- Lazy loading: xarray's default lazy dask arrays mean ingestion validation doesn't require loading full data into memory — only metadata + small samples.
- Large-file handling: if a file exceeds a configurable memory threshold (e.g., 500MB), ingestion must go through the Dask-backed path; small demo files can skip Dask entirely (matches principle J: realistic for incremental student implementation).

---

## 10. Observation Data Architecture

Common observation record (used for Argo, Glider, CTD, BGC alike):

```
Observation {
  instrument_type: "argo" | "glider" | "ctd" | "bgc" | ...   // extensible enum
  platform_id: string
  time: datetime
  lat, lon: float
  profile: [ { depth, temperature?, salinity?, chlorophyll?, ...other_vars } ]
  source_metadata: {...}
}
```
New instrument types are added by: (1) writing a parser adapter that outputs this common shape, (2) adding the type to the enum/registry — rendering and API layers are written against the common shape and need no changes. This is the extensibility mechanism required by the problem statement.

---

## 11. Model vs. Observation Architecture

- **Nearest-point**: find nearest model grid cell (lat/lon/depth/time) via simple index lookup — cheap, always available, always slightly biased.
- **Interpolated**: trilinear (space) + linear (time) interpolation to the observation's exact location — more correct, more expensive, must be computed server-side.
- Uncertainty must be surfaced, not hidden: return both the interpolation method used and a simple distance/time-offset metric (how far the nearest grid point/time step actually was) alongside any comparison value, so a forecaster can judge trust.
- Spatial neighborhood comparison (e.g., mean/std within N grid cells) is a SHOULD-HAVE, not MVP.

---

## 12. API Design (representative, not exhaustive)

| Method | Route | Purpose | Key params | Notes |
|---|---|---|---|---|
| GET | `/datasets` | List available datasets | — | paginated |
| GET | `/datasets/{id}/metadata` | Variable list, bbox, time/depth range | — | |
| GET | `/datasets/{id}/slice` | 2D depth-slice of a variable | `variable, depth, time` | returns array + min/max, not raw NetCDF |
| GET | `/datasets/{id}/volume` | Downsampled 3D volume for volumetric render | `variable, time, resolution` | returns flat typed array + dims |
| GET | `/datasets/{id}/vectors` | Subsampled vector field | `time, depth, stride` | |
| GET | `/observations` | List/query Argo/Glider/CTD/BGC by bbox/time/type | `bbox, time_range, type` | paginated |
| GET | `/observations/{id}/profile` | Full depth-profile for one platform/time | — | |
| GET | `/compare` | Model-vs-observation value | `dataset_id, observation_id, method=nearest|interp` | returns value + method + offset metrics |
| GET | `/health` | Liveness/readiness | — | for monitoring |

All endpoints return typed Pydantic response models (documented via FastAPI's OpenAPI). Errors use standard HTTP codes + a structured `{error, detail}` body. Large list endpoints are paginated (`limit`/`offset`).

---

## 13. Data Caching and Performance

- Slice/volume/vector responses are cache keyed by `(dataset_id, variable, time, depth/resolution, bbox)`; in-process LRU cache is sufficient at MVP; Redis is a drop-in upgrade only once multi-worker deployment makes in-process caching ineffective.
- Time animation: browser prefetches ±2 time steps around the current one.
- Large regions: server-side spatial subsetting by bbox before any slicing, never send global extent if the user is zoomed to a region.
- Browser memory: rendering components discard off-screen/old-timestep textures rather than accumulating them.
- Progressive loading: volumetric requests can return a coarse resolution first, then a refined one, if measured latency requires it (SHOULD-HAVE, not MVP).

---

## 14. Database Architecture

- **NetCDF / Zarr / object storage**: all gridded scientific arrays. Never in PostgreSQL.
- **PostgreSQL + PostGIS**: dataset registry (which files exist, their bbox/time/depth coverage, variable list), and observation metadata/records (Argo/Glider/CTD/BGC — positions and profile *metadata*, with profile arrays either inline as JSONB for small profiles or referenced to object storage if large).
- **Redis**: optional hot-slice cache only, added when justified by measurement, not by default.

---

## 15. Project Repository Structure

```
ocean3d-platform/
├── frontend/                # React + TS + R3F app
│   ├── src/
│   │   ├── scene/           # OceanScene, DepthSlice, Isosurface, CurrentVectors, CurrentParticles
│   │   ├── layers/          # ArgoLayer, GliderLayer
│   │   ├── controls/        # Timeline, VariableSelector, ColorbarControl, DepthControl, LayerControl
│   │   ├── panels/          # ProfileViewer, MetadataPanel, DatasetSelector
│   │   ├── state/           # zustand stores
│   │   ├── data/            # API hooks/client
│   │   └── shaders/         # GLSL for volume/particles/colormap
│   └── tests/
├── backend/                 # FastAPI app
│   ├── api/                 # route modules per §12
│   ├── science/             # xarray-based slicing/interpolation/isosurface prep
│   ├── ingestion/           # NetCDF/ASCII parsers, adapters per instrument type
│   ├── models/              # Pydantic schemas
│   ├── db/                  # PostGIS models/migrations
│   └── tests/
├── shared/                  # shared TS types generated from OpenAPI schema
├── infra/                   # docker-compose, deployment configs
├── docs/                    # this spec + ADRs
└── data-samples/            # small demo NetCDF/observation files for dev
```

---

## 16. Security

- Auth: simple session/JWT-based auth adequate for an internal/demo tool (MUST); role separation (viewer vs admin/ingest) is a SHOULD-HAVE.
- Input validation: strict Pydantic schemas on every query param (bbox, time, depth ranges bounded and type-checked).
- File-upload validation: NetCDF ingestion endpoint (if exposed) must cap file size, validate structure before full parse, and run in a sandboxed/async worker — never parse untrusted files synchronously in the request thread (decompression-bomb risk).
- Rate limiting: basic per-IP limiting on expensive endpoints (`/slice`, `/volume`).
- Secrets management: environment variables / `.env` excluded from VCS; no secrets in frontend bundle.

---

## 17. Testing Strategy

- **Scientific invariants (critical, must exist):** slice values fall within dataset's documented min/max; depth-sign convention consistent; interpolation at an exact grid point equals the raw grid value; NaN/mask propagates correctly and never silently becomes 0.
- Unit tests: ingestion parsers, slicing math, interpolation functions.
- API tests: contract tests against Pydantic schemas, error cases (out-of-range bbox/time/depth).
- Frontend tests: control components (state transitions), data hooks (mocked API).
- Rendering tests: snapshot/regression tests on shader output for known synthetic inputs (not pixel-perfect, but "shape is right").
- Integration tests: ingestion → API → frontend fetch round-trip on a small fixture dataset.
- Performance tests: slice/volume endpoint latency under repeated/varied queries.

---

## 18. Observability

- Structured logging (request id, dataset id, timing) in the API layer.
- Metrics: request latency per endpoint, cache hit rate, ingestion job success/failure.
- Error reporting: centralized exception handler returning structured errors + server-side logging.
- Data pipeline monitoring: ingestion job status recorded in the dataset registry table (success/failure/timestamp).

---

## 19. Deployment Architecture

- **Local dev**: `docker-compose` with `frontend`, `backend`, `postgres` (+ PostGIS) services; sample NetCDF mounted from `data-samples/`.
- **Competition/demo**: same Docker Compose, run on a laptop or a small cloud VM; no Redis/Dask needed at this scale.
- **Institutional/production**: UNKNOWN infrastructure (§3) — design keeps backend stateless behind the API so it can be horizontally scaled, and storage abstracted (local disk now, swappable for S3-compatible object storage later) without architecture changes.

---

## 20. Development Roadmap

- **M0** — Repo scaffold, Docker Compose skeleton, CI stub.
- **M1** — NetCDF ingestion for one sample dataset → registered in PostgreSQL.
- **M2** — Backend API: `/datasets`, `/datasets/{id}/metadata`, `/datasets/{id}/slice`.
- **M3** — Minimal frontend: dataset selector + single depth-slice render (flat plane, not yet 3D).
- **M4** — 2D scientific validation: colorbar correctness, min/max checks against known dataset stats.
- **M5** — True 3D depth-slice navigation + vertical exaggeration.
- **M6** — Current vectors (subsampled arrows), then particle advection.
- **M7** — Argo ingestion + `ArgoLayer` + `ProfileViewer`.
- **M8** — Glider ingestion (proves the observation-adapter extensibility claim).
- **M9** — Model-vs-observation comparison endpoint + UI.
- **M10** — Volume rendering + isosurfaces (highest technical risk, scheduled after the simpler wins exist).
- **M11** — Caching/performance pass (measure first, then add Redis/Zarr/Dask only if justified).
- **M12** — Deployment hardening.
- **M13 (optional)** — ML-derived product overlay, only if time remains.

---

## 21. MVP Definition

- **MVP**: ingest one demo NetCDF, serve depth slices with variable/depth/time controls, render as a textured plane with colorbar, overlay Argo points with a click-to-profile viewer. No isosurfaces, no particle currents, no model-obs comparison. This alone already answers the core gap in the problem statement (co-visualization of model + observations in one browser view).
- **Competition-ready**: MVP + current vectors + vertical exaggeration + time animation + one additional instrument type (Glider) + basic model-obs nearest-point comparison.
- **Production-grade**: adds interpolated comparison, Zarr/Dask for large-file scalability, Redis caching, auth/roles, monitoring, isosurfaces, particle advection.
- **Future**: HF radar/moorings/ADCP/satellite/ML-derived products, OGC WMS/WCS compliance, CesiumJS globe basemap.

---

## 22. Risks and Failure Modes

| Risk | Mitigation |
|---|---|
| Browser GPU limits (weak laptops, exhibition kiosks) | Server-side downsampling with selectable resolution; graceful fallback to 2D slice view if WebGL2/float-texture support absent |
| Huge datasets exceeding memory | Dask-backed chunked reads; never load full array server-side for a slice request |
| Network bandwidth for volume/particle data | Send typed binary arrays (not JSON floats), compress in transit |
| Browser memory growth over long sessions | Explicit disposal of Three.js textures/geometries on unmount/timestep change |
| WebGL feature gaps across browsers | Feature-detect float textures/instancing at startup; degrade rendering mode rather than crash |
| Incorrect interpolation silently producing plausible-looking wrong numbers | Scientific invariant tests (§17); always surface interpolation method + offset to the user |
| Coordinate-system mistakes (depth sign, lon 0–360 vs -180–180) | Normalize explicitly at ingestion; test against known reference points |
| Time synchronization mismatches between model steps and observation timestamps | Explicit time-offset reported in `/compare` response, never silently snapped |
| Irregular/curvilinear grids breaking the "regular grid" slicing assumption | Grid type recorded in metadata; slicing code branches or fails loudly, never silently mis-slices |
| Missing values rendered as 0 (looks like real cold/fresh water) | NaN propagated end-to-end, rendered as transparent/masked, never coerced to 0 |
| Rendering performance collapse with dense vector fields | Mandatory subsampling/stride on the vector endpoint, never "all grid points" |

---

## 23. Architectural Decisions (ADR-style)

- **ADR-1**: React Three Fiber chosen over raw Three.js for maintainability within a React app; over CesiumJS as primary engine because volumetric/isosurface rendering needs custom shader control Cesium's scene graph doesn't expose cleanly.
- **ADR-2**: FastAPI chosen for typed contracts (Pydantic) matching the scientific-correctness priority — wrong-shaped data is rejected at the API boundary, not discovered downstream.
- **ADR-3**: Modular monolith (single FastAPI app with clear internal module boundaries: `api/science/ingestion/db`) chosen over microservices — team size and problem scale don't justify service-per-concern overhead (principle H/I).
- **ADR-4**: Dask/Zarr/Redis marked optional-at-MVP — introducing them before a measured need violates the "avoid unnecessary complexity" instruction; the interfaces are designed so they slot in later without a rewrite.
- **ADR-5**: PostGIS used only for observation/metadata, never gridded arrays — matches the explicit instruction not to put massive scientific arrays into PostgreSQL.
- **ADR-6**: All server-to-browser payloads are pre-reduced (slices/downsampled volumes/subsampled vectors) — the single architectural rule that makes browser performance achievable at all.

---

## 24. Final Recommended Stack

**Frontend**: React + TypeScript, React Three Fiber + drei, Zustand, Plotly.js.
**Backend**: FastAPI + Pydantic + Uvicorn, xarray + NumPy + netCDF4/h5netcdf.
**Data/Storage**: PostgreSQL + PostGIS for metadata/observations; local disk/object storage for NetCDF; Zarr as an optional cache format.
**Deferred (add only when measurement justifies)**: Dask, Redis, CesiumJS.
**Explicitly not used**: MATLAB, ParaView, ArcGIS, QGIS, any desktop/proprietary visualization software.

---

## 25. Antigravity Implementation Plan

> Each task is scoped to be independently reviewable. Do not combine tasks. Do not implement a later task's scope early.

**TASK-01 — Repo scaffold**
- Objective: Create monorepo structure per §15, empty Docker Compose (frontend/backend/postgres services, no logic yet).
- Files: root `docker-compose.yml`, `frontend/` and `backend/` skeletons with placeholder `package.json`/`pyproject.toml`.
- Dependencies: none.
- Acceptance: `docker-compose up` starts three containers that boot without crashing (health endpoints return 200 on backend; frontend serves a placeholder page).
- Tests: a smoke test hitting `/health`.
- Do NOT: add any scientific/rendering code yet.

**TASK-02 — NetCDF ingestion for one sample dataset**
- Objective: Implement `backend/ingestion/netcdf_parser.py` per §9 (validation → normalization → registry insert) for one small sample file placed in `data-samples/`.
- Dependencies: TASK-01.
- Acceptance: running the ingestion script registers the dataset's metadata (bbox, time range, depth range, variables) in PostgreSQL.
- Tests: unit test asserting registered metadata matches the known sample file's actual values.
- Do NOT: implement Dask/Zarr paths yet; do NOT touch API or frontend.

**TASK-03 — Core read API (`/datasets`, `/metadata`, `/slice`)**
- Objective: Implement the three endpoints per §12 backed by `backend/science/slicing.py` (xarray-based).
- Dependencies: TASK-02.
- Acceptance: `/datasets/{id}/slice?variable=temperature&depth=0&time=...` returns a JSON array + min/max matching manually-computed values from the sample file.
- Tests: API contract test + scientific invariant test (values within documented min/max; NaN handling).
- Do NOT: implement `/volume`, `/vectors`, or observation endpoints yet.

**TASK-04 — Minimal frontend: dataset selector + flat slice render**
- Objective: `DatasetSelector`, `VariableSelector`, `DepthControl`, and a single `DepthSlice` component rendering the API's slice as a colored plane (no 3D depth stacking yet).
- Dependencies: TASK-03.
- Acceptance: selecting a variable/depth updates the rendered texture and matches the colorbar range from the API.
- Tests: component test mocking the API response; visual smoke test.
- Do NOT: implement isosurfaces, vectors, or Argo layers yet.

**TASK-05 — Argo ingestion + observation API + ArgoLayer + ProfileViewer**
- Objective: Implement the common `Observation` model (§10) for Argo specifically, `/observations` and `/observations/{id}/profile` endpoints, `ArgoLayer` markers, and `ProfileViewer` (Plotly depth-vs-variable chart) on click.
- Dependencies: TASK-03, TASK-04.
- Acceptance: clicking a rendered Argo marker opens a profile chart matching the sample data.
- Tests: parser unit test; API test; frontend interaction test (click → panel opens with correct data).
- Do NOT: implement Glider yet — but do NOT hardcode "Argo" into shared code paths; the `instrument_type` field must be the only Argo-specific thing in shared layers, proving extensibility.

**TASK-06 — Glider ingestion (extensibility proof)**
- Objective: Add a Glider adapter reusing the same `Observation` model and the same `ArgoLayer`-style rendering (generalize to `ObservationLayer` if needed) with zero changes to `/observations` API contract.
- Dependencies: TASK-05.
- Acceptance: Glider data renders using the same layer/profile components, confirming no rendering-layer changes were required — file a short note if any were.
- Tests: parser unit test for Glider format.
- Do NOT: refactor Argo code beyond generalizing shared naming if strictly necessary.

**TASK-07 — Model-vs-observation comparison**
- Objective: `/compare` endpoint (§11, nearest-point method first), plus a UI affordance (e.g., a value shown in `ProfileViewer` alongside the observed value).
- Dependencies: TASK-05.
- Acceptance: comparison returns correct nearest-grid value plus a distance/time-offset metric for a known observation/model pair.
- Tests: scientific correctness test against a manually computed nearest-point value.
- Do NOT: implement interpolated comparison yet (separate task).

**TASK-08 — 3D depth-slice stacking + vertical exaggeration**
- Objective: Extend `DepthSlice`/`OceanScene` to stack multiple slices in 3D space with a vertical-exaggeration control.
- Dependencies: TASK-04.
- Acceptance: adjusting depth navigates between real 3D-positioned slices; exaggeration control visibly scales Z.
- Tests: component test for exaggeration transform math.
- Do NOT: implement volume rendering or isosurfaces here.

**TASK-09 — Current vectors**
- Objective: `/datasets/{id}/vectors` endpoint (server-side subsampled) + `CurrentVectors` instanced-arrow rendering.
- Dependencies: TASK-08.
- Acceptance: vector density on screen is bounded regardless of raw grid resolution (proves subsampling works).
- Tests: API test asserting response point count respects the `stride` param.
- Do NOT: implement particle advection yet.

**TASK-10 — Particle advection**
- Objective: `CurrentParticles` GPGPU shader advecting particles from the vector field texture.
- Dependencies: TASK-09.
- Acceptance: particles visibly follow the current direction on a known synthetic test vector field (e.g., uniform eastward flow moves particles east).
- Tests: shader-output regression test on the synthetic case.
- Do NOT: touch the vectors API contract.

**TASK-11 — Volume rendering + isosurfaces**
- Objective: `/datasets/{id}/volume` (downsampled 3D texture) endpoint; `Isosurface`/volumetric ray-march shader.
- Dependencies: TASK-08.
- Acceptance: isosurface at a known threshold on a synthetic test volume matches expected geometry (sanity-check shape, not pixel-perfect).
- Tests: correctness test on synthetic volume; performance test at target resolution.
- Do NOT: attempt full-resolution volumetric rendering — must use the downsampled path only.

**TASK-12 — Caching pass**
- Objective: Add in-process LRU cache in front of slice/volume/vector endpoints, keyed per §13.
- Dependencies: TASK-03/09/11 in place.
- Acceptance: repeated identical requests show measured latency improvement; cache correctness test (stale param combo never returns wrong cached value).
- Do NOT: introduce Redis unless a documented measurement shows in-process caching is insufficient.

**TASK-13 — Deployment hardening**
- Objective: production-oriented Docker Compose (env-based config, health checks, no dev-only defaults), basic auth middleware, rate limiting on `/slice`/`/volume`.
- Dependencies: all API tasks.
- Acceptance: containers restart cleanly, auth blocks unauthenticated write/ingest routes, rate limit returns 429 under burst load.
- Do NOT: build a full user-management system — session/JWT auth is sufficient per §16.

---

## 26. Questions That Must Be Answered Before Implementation

Only genuinely blocking items — everything else has a stated assumption above and should not block starting M0–M2:

1. **Do you have an actual sample NetCDF file (or its exact variable/dimension names and CF metadata) to ingest first?** Without one, TASK-02 cannot be scoped precisely — a synthetic fixture can substitute temporarily but must be replaced before scientific-correctness testing is meaningful.
2. **Do you have sample Argo/Glider files (real format, e.g., actual Argo NetCDF/CSV structure), or should TASK-05/06 target a synthetic schema first?** This affects whether the observation adapter is written against real-world format quirks or a clean assumption.
3. **Is any real INCOIS API/data feed available to you, or is this entirely self-hosted with your own sample data for the competition?** This determines whether §19's "institutional deployment" unknowns matter now or can stay deferred.

Everything else (concurrency, infrastructure, dataset scale) has a stated assumption in §3 and should not block starting implementation.
