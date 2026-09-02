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
      <div className="bg-navy-deep border-2 border-navy-sky rounded-xl p-3 shadow-panel text-navy-ice">
        <div className="flex items-center justify-between gap-4 mb-2">
          {/* Playback Actions */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={handlePrev}
              className="p-1.5 rounded-lg bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep text-navy-ice border border-navy-sky transition"
              title="Previous Timestep"
            >
              <SkipBack className="w-4 h-4" />
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 rounded-lg bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep text-navy-ice font-bold border-2 border-navy-sky transition shadow-md flex items-center gap-1.5"
              title={isPlaying ? 'Pause Animation' : 'Play Timeline'}
            >
              {isPlaying ? <Pause className="w-4 h-4 text-navy-ice" /> : <Play className="w-4 h-4 text-navy-ice fill-current" />}
              <span className="text-xs font-mono">{isPlaying ? 'PAUSE' : 'PLAY'}</span>
            </button>

            <button
              onClick={handleNext}
              className="p-1.5 rounded-lg bg-navy-ocean hover:bg-navy-sky hover:text-navy-deep text-navy-ice border border-navy-sky transition"
              title="Next Timestep"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          {/* Current Date/Time Display */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-ocean border border-navy-sky text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-navy-ice" />
            <span className="text-navy-ice font-sans">Timestep:</span>
            <span className="font-bold text-navy-ice">{TIME_STEPS[timeIndex]}</span>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 bg-navy-ocean p-1 rounded-lg border border-navy-sky text-[11px] font-mono">
            {[1, 2, 4].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-2 py-0.5 rounded transition ${
                  playbackSpeed === spd
                    ? 'bg-navy-sky text-navy-deep font-bold border border-navy-ice'
                    : 'text-navy-ice hover:bg-navy-sky hover:text-navy-deep'
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
            className="w-full h-2.5 bg-navy-ocean border border-navy-sky rounded-lg appearance-none cursor-pointer accent-[#4988C4]"
          />
        </div>

        {/* Step Tick Markers */}
        <div className="flex justify-between px-1 mt-1.5 text-[9px] font-mono text-navy-ice font-semibold">
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
