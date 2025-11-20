/**
 * VideoControls Component
 *
 * Custom video player controls with play/pause, seek, volume, and fullscreen buttons.
 * Accessible keyboard shortcuts and responsive design.
 */

import React, { useState, useRef, useEffect } from "react";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  ChevronDown,
} from "lucide-react";
import { formatTime } from "@/lib/video/utils";

/**
 * Props for VideoControls component
 */
export interface VideoControlsProps {
  /** Whether video is currently playing */
  isPlaying: boolean;

  /** Current playback position in seconds */
  currentTime: number;

  /** Total video duration in seconds */
  duration: number;

  /** Volume level (0.0 to 1.0) */
  volume: number;

  /** Whether audio is muted */
  isMuted: boolean;

  /** Whether player is in fullscreen mode */
  isFullscreen: boolean;

  /** Callback when play/pause is toggled */
  onPlayPause: () => void;

  /** Callback when seeking to a new time */
  onSeek: (time: number) => void;

  /** Callback when volume is changed */
  onVolumeChange: (volume: number) => void;

  /** Callback when mute is toggled */
  onToggleMute: () => void;

  /** Callback when fullscreen is toggled */
  onToggleFullscreen: () => void;

  /** Start time of the hand (for looping) */
  startTime?: number;

  /** End time of the hand (for looping) */
  endTime?: number;

  /** Available playback speeds */
  playbackRates?: number[];

  /** Current playback rate */
  playbackRate?: number;

  /** Callback when playback rate changes */
  onPlaybackRateChange?: (rate: number) => void;

  /** CSS class name for styling */
  className?: string;
}

/**
 * VideoControls Component
 *
 * Renders custom video player controls with:
 * - Play/pause button
 * - Seek bar with progress
 * - Time display
 * - Volume slider with mute
 * - Playback speed selector
 * - Fullscreen button
 *
 * @example
 * ```typescript
 * <VideoControls
 *   isPlaying={state.isPlaying}
 *   currentTime={state.currentTime}
 *   duration={state.duration}
 *   volume={state.volume}
 *   isMuted={state.isMuted}
 *   isFullscreen={state.isFullscreen}
 *   onPlayPause={controls.togglePlay}
 *   onSeek={controls.seek}
 *   onVolumeChange={controls.setVolume}
 *   onToggleMute={controls.toggleMute}
 *   onToggleFullscreen={controls.toggleFullscreen}
 *   playbackRate={state.playbackRate}
 *   onPlaybackRateChange={controls.setPlaybackRate}
 *   startTime={3421.5}
 *   endTime={3482.0}
 * />
 * ```
 */
export const VideoControls = React.forwardRef<
  HTMLDivElement,
  VideoControlsProps
>(
  (
    {
      isPlaying,
      currentTime,
      duration,
      volume,
      isMuted,
      isFullscreen,
      onPlayPause,
      onSeek,
      onVolumeChange,
      onToggleMute,
      onToggleFullscreen,
      startTime = 0,
      endTime,
      playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2],
      playbackRate = 1,
      onPlaybackRateChange,
      className = "",
    },
    ref
  ) => {
    const [showVolumeSlider, setShowVolumeSlider] = useState(false);
    const [showSpeedMenu, setShowSpeedMenu] = useState(false);
    const progressBarRef = useRef<HTMLDivElement>(null);
    const volumeRef = useRef<HTMLDivElement>(null);
    const speedMenuRef = useRef<HTMLDivElement>(null);

    // Handle progress bar click/drag
    const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
      if (!progressBarRef.current) return;

      const rect = progressBarRef.current.getBoundingClientRect();
      const percent = (e.clientX - rect.left) / rect.width;
      const newTime = percent * duration;

      onSeek(newTime);
    };

    // Handle progress bar drag
    const handleProgressDrag = (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.buttons !== 1) return;
      handleProgressClick(e);
    };

    // Handle volume click outside
    useEffect(() => {
      const handleClickOutside = (e: MouseEvent) => {
        if (
          volumeRef.current &&
          !volumeRef.current.contains(e.target as Node)
        ) {
          setShowVolumeSlider(false);
        }
        if (
          speedMenuRef.current &&
          !speedMenuRef.current.contains(e.target as Node)
        ) {
          setShowSpeedMenu(false);
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Calculate display time range
    const displayStartTime = startTime || 0;
    const displayDuration = endTime ? endTime - displayStartTime : duration;
    const displayCurrentTime = Math.max(0, currentTime - displayStartTime);

    // Progress percentage
    const progressPercent =
      displayDuration > 0 ? (displayCurrentTime / displayDuration) * 100 : 0;

    return (
      <div
        ref={ref}
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 opacity-0 transition-opacity group-hover:opacity-100 ${className}`}
      >
        {/* Progress Bar */}
        <div
          ref={progressBarRef}
          className="group/progress mb-3 flex h-1 cursor-pointer items-center rounded bg-white/30 hover:h-2"
          onClick={handleProgressClick}
          onMouseMove={handleProgressDrag}
        >
          <div
            className="h-full rounded bg-red-500 transition-all group-hover/progress:bg-red-600"
            style={{ width: `${progressPercent}%` }}
          >
            <div className="absolute right-0 top-1/2 h-3 w-3 -translate-y-1/2 translate-x-1/2 transform rounded-full bg-white shadow-lg opacity-0 transition-opacity group-hover/progress:opacity-100" />
          </div>
        </div>

        {/* Controls Row */}
        <div className="flex items-center justify-between gap-2">
          {/* Left Controls: Play/Pause + Time */}
          <div className="flex items-center gap-3">
            {/* Play/Pause Button */}
            <button
              onClick={onPlayPause}
              className="flex h-8 w-8 items-center justify-center rounded hover:bg-white/20 transition-colors"
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? (
                <Pause className="h-5 w-5 text-white" />
              ) : (
                <Play className="h-5 w-5 text-white" />
              )}
            </button>

            {/* Time Display */}
            <div className="text-xs font-medium text-white/90 select-none whitespace-nowrap">
              <span>{formatTime(displayCurrentTime)}</span>
              <span className="text-white/60"> / </span>
              <span>{formatTime(displayDuration)}</span>
            </div>
          </div>

          {/* Right Controls: Volume, Speed, Fullscreen */}
          <div className="flex items-center gap-2">
            {/* Volume Control */}
            <div ref={volumeRef} className="relative flex items-center">
              <button
                onClick={() => {
                  onToggleMute();
                  setShowVolumeSlider(!showVolumeSlider);
                }}
                className="flex h-8 w-8 items-center justify-center rounded hover:bg-white/20 transition-colors"
                aria-label={isMuted ? "Unmute" : "Mute"}
              >
                {isMuted || volume === 0 ? (
                  <VolumeX className="h-5 w-5 text-white" />
                ) : (
                  <Volume2 className="h-5 w-5 text-white" />
                )}
              </button>

              {/* Volume Slider Popup */}
              {showVolumeSlider && (
                <div className="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 transform rounded bg-black/90 p-2">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={isMuted ? 0 : volume * 100}
                    onChange={(e) => {
                      const newVolume = parseInt(e.target.value) / 100;
                      onVolumeChange(newVolume);
                      if (isMuted && newVolume > 0) {
                        onToggleMute();
                      }
                    }}
                    className="h-20 w-1 cursor-pointer accent-red-500"
                    aria-label="Volume"
                  />
                </div>
              )}
            </div>

            {/* Playback Speed */}
            <div ref={speedMenuRef} className="relative">
              <button
                onClick={() => setShowSpeedMenu(!showSpeedMenu)}
                className="flex h-8 w-10 items-center justify-center rounded text-xs font-medium text-white hover:bg-white/20 transition-colors"
                aria-label="Playback speed"
              >
                {playbackRate}x
              </button>

              {showSpeedMenu && (
                <div className="absolute bottom-full right-0 mb-2 min-w-12 rounded bg-black/90 py-1 shadow-lg">
                  {playbackRates.map((rate) => (
                    <button
                      key={rate}
                      onClick={() => {
                        onPlaybackRateChange?.(rate);
                        setShowSpeedMenu(false);
                      }}
                      className={`block w-full px-3 py-1 text-xs font-medium transition-colors ${
                        playbackRate === rate
                          ? "bg-red-500 text-white"
                          : "text-white hover:bg-white/20"
                      }`}
                    >
                      {rate}x
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Fullscreen Button */}
            <button
              onClick={onToggleFullscreen}
              className="flex h-8 w-8 items-center justify-center rounded hover:bg-white/20 transition-colors"
              aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            >
              {isFullscreen ? (
                <Minimize className="h-5 w-5 text-white" />
              ) : (
                <Maximize className="h-5 w-5 text-white" />
              )}
            </button>
          </div>
        </div>

        {/* Keyboard Shortcuts Hint */}
        <div className="mt-2 text-xs text-white/50 hidden group-hover:block">
          Space: play/pause | Arrow keys: seek | F: fullscreen | M: mute |
          0-9: jump to %
        </div>
      </div>
    );
  }
);

VideoControls.displayName = "VideoControls";
