/**
 * Standalone verification tests for particle advection mathematics
 */

import {
  buildVelocityGrid,
  interpolateVelocity,
  advectParticle,
  reseedParticle,
  METERS_PER_DEGREE_LAT,
  Particle,
  VelocityGrid
} from './particleEngine';

export function runParticleEngineTests() {
  const results: string[] = [];

  // Test 1: Synthetic grid construction
  const grid = buildVelocityGrid([]);
  if (grid.bounds.minLat === -5 && grid.bounds.maxLat === 25) {
    results.push('PASS: Synthetic Grid Construction');
  } else {
    results.push('FAIL: Synthetic Grid Construction');
  }

  // Test 2: Interpolation inside grid
  const velCenter = interpolateVelocity(grid, 10.0, 70.0);
  if (velCenter && typeof velCenter.u === 'number' && typeof velCenter.v === 'number') {
    results.push('PASS: Interpolation Inside Grid');
  } else {
    results.push('FAIL: Interpolation Inside Grid');
  }

  // Test 3: Eastward advection displacement
  const eastGrid: VelocityGrid = {
    lats: [0, 10],
    lons: [60, 70],
    uGrid: [[1.0, 1.0], [1.0, 1.0]],
    vGrid: [[0.0, 0.0], [0.0, 0.0]],
    bounds: { minLat: 0, maxLat: 10, minLon: 60, maxLon: 70 }
  };
  const startP: Particle = { id: 1, lat: 5.0, lon: 65.0, speed: 1.0, age: 0, maxAge: 100, history: [] };
  const updatedP = advectParticle(startP, eastGrid, 3600);
  if (updatedP.lon > startP.lon && updatedP.lat === startP.lat) {
    results.push('PASS: Eastward Advection');
  } else {
    results.push('FAIL: Eastward Advection');
  }

  // Test 4: Northward advection displacement
  const northGrid: VelocityGrid = {
    lats: [0, 10],
    lons: [60, 70],
    uGrid: [[0.0, 0.0], [0.0, 0.0]],
    vGrid: [[1.0, 1.0], [1.0, 1.0]],
    bounds: { minLat: 0, maxLat: 10, minLon: 60, maxLon: 70 }
  };
  const northP = advectParticle(startP, northGrid, 3600);
  if (northP.lat > startP.lat && northP.lon === startP.lon) {
    results.push('PASS: Northward Advection');
  } else {
    results.push('FAIL: Northward Advection');
  }

  // Test 5: Boundary reset on out-of-bounds
  const oobP: Particle = { id: 2, lat: 99.0, lon: 99.0, speed: 1.0, age: 0, maxAge: 100, history: [] };
  const reseededP = advectParticle(oobP, eastGrid, 3600);
  if (reseededP.lat >= 0 && reseededP.lat <= 10 && reseededP.lon >= 60 && reseededP.lon <= 70) {
    results.push('PASS: Boundary Reset Handling');
  } else {
    results.push('FAIL: Boundary Reset Handling');
  }

  return results;
}
