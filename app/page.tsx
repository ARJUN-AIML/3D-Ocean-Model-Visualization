'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import TopBar from '../components/ui/TopBar';
import LeftControls from '../components/ui/LeftControls';
import ZoomControls from '../components/ui/ZoomControls';
import BottomTimeline from '../components/ui/BottomTimeline';
import ScientificLegend from '../components/ui/ScientificLegend';
import RightDrawer from '../components/ui/RightDrawer';

// Load CesiumGlobe dynamically with SSR disabled to prevent server-side DOM window errors
const CesiumGlobe = dynamic(() => import('../components/cesium/CesiumGlobe'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex flex-col items-center justify-center bg-ocean-950 text-cyan-400">
      <div className="w-12 h-12 rounded-full border-4 border-cyan-500/20 border-t-cyan-400 animate-spin mb-4" />
      <div className="text-sm font-semibold tracking-wider font-mono uppercase">Loading 3D Cesium Viewport...</div>
    </div>
  )
});

export default function OceanTwinPage() {
  return (
    <main className="relative w-screen h-screen overflow-hidden bg-ocean-950">
      {/* 3D CESIUM GLOBE — THE HERO OF THE APPLICATION (70%+ WORKSPACE) */}
      <div className="absolute inset-0 z-0">
        <CesiumGlobe />
      </div>

      {/* Floating Scientific Header Top Bar */}
      <TopBar />

      {/* Floating Collapsible Left Control Panel */}
      <LeftControls />

      {/* Floating Zoom Controls (Top Right) */}
      <ZoomControls />

      {/* Floating Bottom Timeline Scrubber */}
      <BottomTimeline />

      {/* Floating Scientific Legend */}
      <ScientificLegend />

      {/* Contextual Right Drawer */}
      <RightDrawer />
    </main>
  );
}
