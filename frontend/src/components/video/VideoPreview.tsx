"use client";

/**
 * Video Preview Component
 *
 * Lightweight video player for hover previews in search results.
 * Automatically plays a muted video segment when user hovers over a hand card.
 *
 * Features:
 * - Auto-play on mount (muted)
 * - No controls (minimal UI)
 * - Segment playback (start to end time)
 * - Loop playback
 * - Fallback to thumbnail on error
 * - Optimized for performance (lazy loading)
 */

import React, { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export interface VideoPreviewProps {
  /** Hand ID for fetching video URL */
  handId: string;

  /** Video URL (if available) */
  videoUrl?: string;

  /** Fallback thumbnail URL */
  thumbnailUrl?: string;

  /** Hand start time (seconds) */
  startTime?: number;

  /** Hand end time (seconds) */
  endTime?: number;

  /** Custom CSS class name */
  className?: string;

  /** Callback when video starts playing */
  onPlay?: () => void;

  /** Callback when video encounters error */
  onError?: () => void;
}

/**
 * VideoPreview Component
 *
 * Displays a short auto-playing video preview when hovering over a hand card.
 * Automatically loops the hand segment (start to end time) with no audio.
 *
 * **Mock Mode Behavior**: When NEXT_PUBLIC_ENABLE_MOCK_DATA=true, this component
 * will show a placeholder animation instead of actual video, since mock data
 * doesn't have real GCS video URLs.
 *
 * @example
 * ```tsx
 * <VideoPreview
 *   handId="wsop_2023_hand_0001"
 *   videoUrl="https://storage.googleapis.com/.../hand.mp4"
 *   thumbnailUrl="/thumbnails/hand_0001.jpg"
 *   startTime={10.5}
 *   endTime={70.2}
 * />
 * ```
 */
export function VideoPreview({
  handId,
  videoUrl,
  thumbnailUrl,
  startTime = 0,
  endTime,
  className,
  onPlay,
  onError,
}: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check if we're in mock mode
  const isMockMode =
    process.env.NEXT_PUBLIC_ENABLE_MOCK_DATA === "true" ||
    !videoUrl ||
    videoUrl === "";

  /**
   * Initialize video on mount
   */
  useEffect(() => {
    const video = videoRef.current;
    if (!video || isMockMode) {
      setIsLoading(false);
      return;
    }

    // Set start time
    video.currentTime = startTime;

    // Auto-play (muted, so it's allowed by browsers)
    const playPromise = video.play();

    if (playPromise !== undefined) {
      playPromise
        .then(() => {
          setIsLoading(false);
          onPlay?.();
        })
        .catch((error) => {
          console.warn("[VideoPreview] Autoplay failed:", error);
          setHasError(true);
          setIsLoading(false);
          onError?.();
        });
    }
  }, [startTime, isMockMode, onPlay, onError]);

  /**
   * Loop video at end time
   */
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !endTime || isMockMode) return;

    const handleTimeUpdate = () => {
      if (video.currentTime >= endTime) {
        video.currentTime = startTime;
        video.play().catch((error) => {
          console.warn("[VideoPreview] Loop playback failed:", error);
        });
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [startTime, endTime, isMockMode]);

  /**
   * Handle video errors
   */
  const handleError = () => {
    console.error("[VideoPreview] Video playback error:", handId);
    setHasError(true);
    setIsLoading(false);
    onError?.();
  };

  /**
   * Handle video load
   */
  const handleLoadedData = () => {
    setIsLoading(false);
  };

  // Mock mode placeholder
  if (isMockMode) {
    return (
      <div
        className={cn(
          "relative w-full h-full bg-gradient-to-br from-gray-800 to-gray-900",
          "flex items-center justify-center",
          className
        )}
      >
        {/* Animated pulse effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-gray-700/20 to-transparent animate-pulse" />

        {/* Mock video icon */}
        <div className="relative z-10 text-gray-400">
          <svg
            className="w-12 h-12 animate-pulse"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-xs mt-2 text-center">Video Preview</p>
          <p className="text-xs text-gray-500 text-center">(Mock Mode)</p>
        </div>

        {/* Show thumbnail if available */}
        {thumbnailUrl && (
          <img
            src={thumbnailUrl}
            alt="Hand thumbnail"
            className="absolute inset-0 w-full h-full object-cover opacity-20"
          />
        )}
      </div>
    );
  }

  // Fallback to thumbnail if error or no video URL
  if (hasError || !videoUrl) {
    return (
      <div
        className={cn(
          "relative w-full h-full bg-gray-900 flex items-center justify-center",
          className
        )}
      >
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt="Hand thumbnail"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-gray-500 text-center">
            <svg
              className="w-8 h-8 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            <p className="text-xs">Video unavailable</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn("relative w-full h-full overflow-hidden", className)}>
      {/* Loading state */}
      {isLoading && (
        <div className="absolute inset-0 bg-gray-900 flex items-center justify-center z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white" />
        </div>
      )}

      {/* Video element */}
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full h-full object-cover"
        muted
        playsInline
        preload="auto"
        onError={handleError}
        onLoadedData={handleLoadedData}
        aria-label={`Video preview for hand ${handId}`}
      />

      {/* Optional: Subtle play indicator */}
      {!isLoading && (
        <div className="absolute bottom-2 right-2 bg-black/50 rounded-full p-1">
          <svg
            className="w-4 h-4 text-white"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M8 5v14l11-7z" />
          </svg>
        </div>
      )}
    </div>
  );
}

export default VideoPreview;
