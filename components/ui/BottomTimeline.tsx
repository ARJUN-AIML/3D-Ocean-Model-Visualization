'use client';

import React from 'react';
import { useOcean } from '../../context/OceanContext';
import { Play, Pause, SkipBack, SkipForward, Clock } from 'lucide-react';

const TIME_STEPS = [
  "01 SEP 00:00 UTC",
  "01 SEP 06:00 UTC",
  "01 SEP 12:00 UTC",
  "01 SEP 18:00 UTC",
  "02 SEP 00:00 UTC",
  "02 SEP 06:00 UTC",
  "02 SEP 12:00 UTC",
  "02 SEP 18:00 UTC",
  "03 SEP 00:00 UTC",
];

export default function BottomTimeline() {
  const {
    timeIndex,
    setTimeIndex,
    isPlaying,
    setIsPlaying,
    playbackSpeed,
    setPlaybackSpeed
  } = useOcean();

  const handlePrev = () => {
    setTimeIndex((timeIndex - 1 + TIME_STEPS.length) % TIME_STEPS.length);
  };

  const handleNext = () => {
    setTimeIndex((timeIndex + 1) % TIME_STEPS.length);
  };

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 w-full max-w-2xl px-4 select-none">
      <div className="bg-ocean-900/85 backdrop-blur-md border border-cyan-500/20 rounded-xl p-3 shadow-panel-dark text-slate-200">
        <div className="flex items-center justify-between gap-4 mb-2">
          {/* Playback Actions */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={handlePrev}
              className="p-1.5 rounded-lg bg-ocean-950 hover:bg-slate-800 text-slate-300 transition"
              title="Previous Timestep"
            >
              <SkipBack className="w-4 h-4" />
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-ocean-950 font-bold transition shadow-glow-cyan flex items-center gap-1.5"
              title={isPlaying ? 'Pause Animation' : 'Play Timeline'}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
              <span className="text-xs">{isPlaying ? 'PAUSE' : 'PLAY'}</span>
            </button>

            <button
              onClick={handleNext}
              className="p-1.5 rounded-lg bg-ocean-950 hover:bg-slate-800 text-slate-300 transition"
              title="Next Timestep"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          {/* Current Date/Time Display */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-ocean-950 border border-slate-800 text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">Timestep:</span>
            <span className="font-bold text-cyan-300">{TIME_STEPS[timeIndex]}</span>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 bg-ocean-950 p-1 rounded-lg border border-slate-800 text-[11px] font-mono">
            {[1, 2, 4].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-2 py-0.5 rounded transition ${
                  playbackSpeed === spd
                    ? 'bg-cyan-950 text-cyan-300 font-bold border border-cyan-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        {/* Scrubber Slider Bar */}
        <div className="relative flex items-center px-1">
          <input
            type="range"
            min="0"
            max={TIME_STEPS.length - 1}
            value={timeIndex}
            onChange={(e) => setTimeIndex(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>

        {/* Step Tick Markers */}
        <div className="flex justify-between px-1 mt-1.5 text-[9px] font-mono text-slate-400">
          <span>01 SEP</span>
          <span>01 SEP 12:00</span>
          <span>02 SEP (CURRENT)</span>
          <span>02 SEP 18:00</span>
          <span>03 SEP</span>
        </div>
      </div>
    </div>
  );
}
