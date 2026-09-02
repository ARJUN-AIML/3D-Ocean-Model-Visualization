/**
 * OceanTwin 3D — Physical Ocean Particle Advection Engine
 * 
 * Computes bilinear velocity interpolation, physical geographic coordinate displacement,
 * particle lifecycle, and trail updates for high-performance WebGL/Cesium current rendering.
 */

export interface VectorFieldPoint {
  lat: number;
  lon: number;
  u: number;
  v: number;
  speed?: number;
  directionDeg?: number;
}

export interface VelocityGrid {
  lats: number[];
  lons: number[];
  uGrid: number[][]; // [latIndex][lonIndex]
  vGrid: number[][]; // [latIndex][lonIndex]
  bounds: {
    minLat: number;
    maxLat: number;
    minLon: number;
    maxLon: number;
  };
}

export interface Particle {
  id: number;
  lat: number;
  lon: number;
  age: number;
  maxAge: number;
  speed: number;
  history: Array<{ lat: number; lon: number }>;
}

export const METERS_PER_DEGREE_LAT = 111320.0;

/**
 * Converts a raw list of vector field points into a structured 2D velocity grid
 * suitable for fast bilinear interpolation.
 */
export function buildVelocityGrid(points: VectorFieldPoint[]): VelocityGrid {
  if (!points || points.length === 0) {
    return createSyntheticFallbackGrid();
  }

  // Extract unique sorted lats and lons
  const rawLats = Array.from(new Set(points.map(p => Number(p.lat.toFixed(2))))).sort((a, b) => a - b);
  const rawLons = Array.from(new Set(points.map(p => Number(p.lon.toFixed(2))))).sort((a, b) => a - b);

  // If unique grid lines are sparse (less than 2 points per dimension), pad into a regular grid
  if (rawLats.length < 2 || rawLons.length < 2) {
    return createSyntheticFallbackGrid(points);
  }

  const uGrid: number[][] = Array.from({ length: rawLats.length }, () => new Array(rawLons.length).fill(0));
  const vGrid: number[][] = Array.from({ length: rawLats.length }, () => new Array(rawLons.length).fill(0));

  // Populate grid lookup map
  const latMap = new Map(rawLats.map((lat, idx) => [lat, idx]));
  const lonMap = new Map(rawLons.map((lon, idx) => [lon, idx]));

  for (const pt of points) {
    const latKey = Number(pt.lat.toFixed(2));
    const lonKey = Number(pt.lon.toFixed(2));
    const i = latMap.get(latKey);
    const j = lonMap.get(lonKey);
    if (i !== undefined && j !== undefined) {
      uGrid[i][j] = pt.u;
      vGrid[i][j] = pt.v;
    }
  }

  return {
    lats: rawLats,
    lons: rawLons,
    uGrid,
    vGrid,
    bounds: {
      minLat: rawLats[0],
      maxLat: rawLats[rawLats.length - 1],
      minLon: rawLons[0],
      maxLon: rawLons[rawLons.length - 1],
    }
  };
}

/**
 * Creates a synthetic full-basin ocean velocity grid for Indian Ocean / Arabian Sea
 * when backend returns sparse demo points or fallback mode is active.
 */
export function createSyntheticFallbackGrid(seedPoints?: VectorFieldPoint[]): VelocityGrid {
  const lats: number[] = [];
  const lons: number[] = [];
  
  for (let lat = -5.0; lat <= 25.0; lat += 2.5) lats.push(Number(lat.toFixed(1)));
  for (let lon = 50.0; lon <= 95.0; lon += 2.5) lons.push(Number(lon.toFixed(1)));

  const uGrid: number[][] = Array.from({ length: lats.length }, () => new Array(lons.length).fill(0));
  const vGrid: number[][] = Array.from({ length: lats.length }, () => new Array(lons.length).fill(0));

  for (let i = 0; i < lats.length; i++) {
    for (let j = 0; j < lons.length; j++) {
      const lat = lats[i];
      const lon = lons[j];

      // Simulated monsoonal gyre pattern in the Indian Ocean basin
      const uVal = 0.5 * Math.sin((lat + 10) * 0.15) + 0.3 * Math.cos(lon * 0.1);
      const vVal = 0.3 * Math.cos((lat + 5) * 0.2) + 0.2 * Math.sin(lon * 0.15);

      uGrid[i][j] = Number(uVal.toFixed(3));
      vGrid[i][j] = Number(vVal.toFixed(3));
    }
  }

  // Overlay any explicit seed points if available
  if (seedPoints && seedPoints.length > 0) {
    for (const pt of seedPoints) {
      const nearestI = findNearestIndex(lats, pt.lat);
      const nearestJ = findNearestIndex(lons, pt.lon);
      if (nearestI >= 0 && nearestJ >= 0) {
        uGrid[nearestI][nearestJ] = pt.u;
        vGrid[nearestI][nearestJ] = pt.v;
      }
    }
  }

  return {
    lats,
    lons,
    uGrid,
    vGrid,
    bounds: {
      minLat: lats[0],
      maxLat: lats[lats.length - 1],
      minLon: lons[0],
      maxLon: lons[lons.length - 1],
    }
  };
}

/**
 * Performs bilinear interpolation of (u, v) velocity components at geographic position (lat, lon).
 */
export function interpolateVelocity(
  grid: VelocityGrid,
  lat: number,
  lon: number
): { u: number; v: number; speed: number } | null {
  const { lats, lons, uGrid, vGrid, bounds } = grid;

  // Boundary safety check
  if (lat < bounds.minLat || lat > bounds.maxLat || lon < bounds.minLon || lon > bounds.maxLon) {
    return null;
  }

  // Find lower-left grid cell indices
  let i = findLowerIndex(lats, lat);
  let j = findLowerIndex(lons, lon);

  if (i < 0) i = 0;
  if (i >= lats.length - 1) i = lats.length - 2;
  if (j < 0) j = 0;
  if (j >= lons.length - 1) j = lons.length - 2;

  const lat0 = lats[i];
  const lat1 = lats[i + 1];
  const lon0 = lons[j];
  const lon1 = lons[j + 1];

  const t = (lat - lat0) / (lat1 - lat0 || 1.0);
  const s = (lon - lon0) / (lon1 - lon0 || 1.0);

  const u00 = uGrid[i][j];
  const u10 = uGrid[i + 1][j];
  const u01 = uGrid[i][j + 1];
  const u11 = uGrid[i + 1][j + 1];

  const v00 = vGrid[i][j];
  const v10 = vGrid[i + 1][j];
  const v01 = vGrid[i][j + 1];
  const v11 = vGrid[i + 1][j + 1];

  const u = (1 - t) * (1 - s) * u00 + t * (1 - s) * u10 + (1 - t) * s * u01 + t * s * u11;
  const v = (1 - t) * (1 - s) * v00 + t * (1 - s) * v10 + (1 - t) * s * v01 + t * s * v11;

  if (isNaN(u) || isNaN(v) || !isFinite(u) || !isFinite(v)) {
    return null;
  }

  const speed = Math.sqrt(u * u + v * v);
  return { u, v, speed };
}

/**
 * Physical advection step: calculates geographic displacement (dLat, dLon) from velocity (u, v).
 * x(t + dt) = x(t) + u * dt
 * y(t + dt) = y(t) + v * dt
 */
export function advectParticle(
  particle: Particle,
  grid: VelocityGrid,
  dtSeconds: number = 3600,
  maxTrailLength: number = 6
): Particle {
  const vel = interpolateVelocity(grid, particle.lat, particle.lon);

  // If outside domain or invalid velocity or age expired, reseed
  if (!vel || particle.age >= particle.maxAge) {
    return reseedParticle(particle, grid, maxTrailLength);
  }

  // Convert u (m/s) and v (m/s) to degree shifts
  const dLat = (vel.v * dtSeconds) / METERS_PER_DEGREE_LAT;
  const radLat = (particle.lat * Math.PI) / 180.0;
  const metersPerLon = METERS_PER_DEGREE_LAT * Math.max(0.1, Math.cos(radLat));
  const dLon = (vel.u * dtSeconds) / metersPerLon;

  const nextLat = particle.lat + dLat;
  const nextLon = particle.lon + dLon;

  // Append position to tail history
  const newHistory = [...particle.history, { lat: particle.lat, lon: particle.lon }];
  if (newHistory.length > maxTrailLength) {
    newHistory.shift();
  }

  return {
    ...particle,
    lat: nextLat,
    lon: nextLon,
    speed: vel.speed,
    age: particle.age + 1,
    history: newHistory,
  };
}

/**
 * Reseeds a particle randomly inside the velocity grid bounds with new lifecycle params.
 */
export function reseedParticle(particle: Particle, grid: VelocityGrid, maxTrailLength: number = 6): Particle {
  const { minLat, maxLat, minLon, maxLon } = grid.bounds;

  let lat = minLat + Math.random() * (maxLat - minLat);
  let lon = minLon + Math.random() * (maxLon - minLon);

  // Sample valid ocean cells to ensure particles spawn over ocean, not land
  for (let attempt = 0; attempt < 15; attempt++) {
    const testLat = minLat + Math.random() * (maxLat - minLat);
    const testLon = minLon + Math.random() * (maxLon - minLon);
    const vel = interpolateVelocity(grid, testLat, testLon);
    if (vel && vel.speed > 0.001) {
      lat = testLat;
      lon = testLon;
      break;
    }
  }

  const maxAge = Math.floor(60 + Math.random() * 90); // 60 to 150 frames life duration

  return {
    id: particle.id,
    lat,
    lon,
    speed: 0.1,
    age: 0,
    maxAge,
    history: [],
  };
}

/**
 * Initializes a pool of N random particles within the velocity grid.
 */
export function initializeParticlePool(count: number, grid: VelocityGrid): Particle[] {
  const particles: Particle[] = [];
  for (let i = 0; i < count; i++) {
    particles.push(
      reseedParticle({ id: i, lat: 0, lon: 0, speed: 0, age: 999, maxAge: 100, history: [] }, grid)
    );
  }
  return particles;
}

// Internal helper search functions
function findLowerIndex(arr: number[], val: number): number {
  for (let i = 0; i < arr.length - 1; i++) {
    if (val >= arr[i] && val <= arr[i + 1]) {
      return i;
    }
  }
  return arr.length - 2;
}

function findNearestIndex(arr: number[], val: number): number {
  let minDiff = Infinity;
  let idx = -1;
  for (let i = 0; i < arr.length; i++) {
    const diff = Math.abs(arr[i] - val);
    if (diff < minDiff) {
      minDiff = diff;
      idx = i;
    }
  }
  return idx;
}
