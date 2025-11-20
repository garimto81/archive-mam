"use client";

/**
 * Video Preview Thumbnail Component
 *
 * Container component that switches between static thumbnail and video preview
 * based on hover state. Provides smooth transition between the two states.
 *
 * Features:
 * - Static thumbnail by default
 * - Video preview on hover
 * - Smooth fade transitions
 * - Debounced hover to prevent flickering
 * - Lazy loading for performance
 * - Accessible keyboard interactions
 */

import React, { useState, useCallback, useEffect, useRef } from "react";
import { VideoPreview } from "./VideoPreview";
import { cn } from "@/lib/utils";

export interface VideoPreviewThumbnailProps {
  /** Hand ID for fetching video */
  handId: string;

  /** Video URL (if available) */
  videoUrl?: string;

  /** Thumbnail image URL */
  thumbnailUrl?: string;

  /** Hand start time (seconds) */
  startTime?: number;

  /** Hand end time (seconds) */
  endTime?: number;

  /** Hover delay before showing video (ms) */
  hoverDelay?: number;

  /** Custom CSS class name */
  className?: string;

  /** Callback when user starts hovering */
  onHoverStart?: () => void;

  /** Callback when user stops hovering */
  onHoverEnd?: () => void;
}

/**
 * VideoPreviewThumbnail Component
 *
 * Smart container that displays a static thumbnail by default and switches
 * to an auto-playing video preview when the user hovers over it.
 *
 * **Behavior**:
 * - Default: Shows static thumbnail image
 * - Hover: Shows VideoPreview component with auto-playing muted video
 * - Debounced: 300ms delay before showing video (prevents flickering)
 * - Smooth transitions: Fade effect between thumbnail and video
 *
 * **Performance**:
 * - Lazy loads video only when needed (on hover)
 * - Cleans up video resources when hover ends
 * - Optimized for large lists of hand cards
 *
 * @example
 * ```tsx
 * <VideoPreviewThumbnail
 *   handId="wsop_2023_hand_0001"
 *   videoUrl="https://storage.googleapis.com/.../hand.mp4"
 *   thumbnailUrl="/thumbnails/hand_0001.jpg"
 *   startTime={10.5}
 *   endTime={70.2}
 *   hoverDelay={300}
 * />
 * ```
 */
export function VideoPreviewThumbnail({
  handId,
  videoUrl,
  thumbnailUrl,
  startTime = 0,
  endTime,
  hoverDelay = 300,
  className,
  onHoverStart,
  onHoverEnd,
}: VideoPreviewThumbnailProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Handle mouse enter with debounce
   */
  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    onHoverStart?.();

    // Debounce video loading to prevent flickering on quick hovers
    hoverTimeoutRef.current = setTimeout(() => {
      setShowVideo(true);
    }, hoverDelay);
  }, [hoverDelay, onHoverStart]);

  /**
   * Handle mouse leave
   */
  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    setShowVideo(false);
    onHoverEnd?.();

    // Clear hover timeout if user leaves before delay completes
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
  }, [onHoverEnd]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  /**
   * Handle focus (keyboard accessibility)
   */
  const handleFocus = useCallback(() => {
    handleMouseEnter();
  }, [handleMouseEnter]);

  /**
   * Handle blur (keyboard accessibility)
   */
  const handleBlur = useCallback(() => {
    handleMouseLeave();
  }, [handleMouseLeave]);

  return (
    <div
      className={cn(
        "relative w-full h-full overflow-hidden bg-gray-900",
        className
      )}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
      role="img"
      aria-label={`Hand ${handId} preview`}
      tabIndex={0}
    >
      {/* Static thumbnail (always rendered, hidden when video shows) */}
      <div
        className={cn(
          "absolute inset-0 transition-opacity duration-300",
          showVideo ? "opacity-0" : "opacity-100"
        )}
      >
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={`Hand ${handId} thumbnail`}
            className={cn(
              "w-full h-full object-cover",
              "transition-transform duration-300",
              isHovered ? "scale-105" : "scale-100"
            )}
            loading="lazy"
          />
        ) : (
          // Fallback gradient if no thumbnail
          <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
            <svg
              className="w-12 h-12 text-gray-600"
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
          </div>
        )}

        {/* Hover indicator overlay */}
        {isHovered && !showVideo && (
          <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
            <div className="bg-white/90 rounded-full p-3 shadow-lg">
              <svg
                className="w-6 h-6 text-gray-900"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
        )}
      </div>

      {/* Video preview (lazy loaded on hover) */}
      {showVideo && (
        <div
          className={cn(
            "absolute inset-0 transition-opacity duration-300",
            "opacity-0 animate-in fade-in"
          )}
          style={{
            animation: "fadeIn 300ms ease-in-out forwards",
          }}
        >
          <VideoPreview
            handId={handId}
            videoUrl={videoUrl}
            thumbnailUrl={thumbnailUrl}
            startTime={startTime}
            endTime={endTime}
            onError={() => {
              // On video error, show thumbnail again
              setShowVideo(false);
            }}
          />
        </div>
      )}

      {/* Screen reader only description */}
      <span className="sr-only">
        {isHovered
          ? `Playing video preview for hand ${handId}`
          : `Thumbnail for hand ${handId}. Hover to preview video.`}
      </span>
    </div>
  );
}

export default VideoPreviewThumbnail;
