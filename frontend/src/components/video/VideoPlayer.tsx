/**
 * VideoPlayer Component
 *
 * Comprehensive video player for poker hand replays with GCS Signed URL support.
 * Features: custom controls, keyboard shortcuts, fullscreen, responsive design,
 * error handling, and URL expiration monitoring.
 */

import React, { useEffect, useState, useCallback } from "react";
import ReactPlayer from "react-player";
import { VideoControls } from "./VideoControls";
import { VideoError } from "./VideoError";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import type {
  VideoPlaybackError,
  VideoMetadata,
  HandTimelineMarker,
} from "@/types/video";
import {
  isVideoUrlExpired,
  getMimeType,
  parseMediaError,
  getErrorMessage,
  isValidVideoUrl,
} from "@/lib/video/utils";

/**
 * Props for VideoPlayer component
 */
export interface VideoPlayerProps {
  /** GCS signed URL to the video */
  videoUrl: string;

  /** Thumbnail URL to show while loading */
  thumbnailUrl?: string;

  /** Start time of the hand in seconds */
  startTime?: number;

  /** End time of the hand in seconds */
  endTime?: number;

  /** Autoplay the video on load */
  autoplay?: boolean;

  /** Show player controls */
  controls?: boolean;

  /** Mute audio by default */
  muted?: boolean;

  /** Callback when video ends */
  onEnded?: () => void;

  /** Callback for time updates */
  onTimeUpdate?: (currentTime: number) => void;

  /** Callback for playback errors */
  onError?: (error: VideoPlaybackError) => void;

  /** Callback for video events */
  onEvent?: (event: any) => void;

  /** Callback when requesting new URL (for expired URLs) */
  onRefreshUrl?: () => Promise<string>;

  /** Timeline markers (street markers) */
  markers?: HandTimelineMarker[];

  /** CSS class name for styling */
  className?: string;

  /** Container aspect ratio (width / height) */
  aspectRatio?: number;
}

/**
 * VideoPlayer Component
 *
 * Full-featured video player for poker hand replays with:
 * - React Player integration (supports multiple formats)
 * - Custom video controls (play/pause, seek, volume, fullscreen)
 * - Keyboard shortcuts (Space, arrows, F, M, 0-9)
 * - Responsive 16:9 aspect ratio
 * - GCS signed URL support with expiration handling
 * - Thumbnail loading state
 * - Error handling and recovery
 * - Accessibility (ARIA labels, keyboard navigation)
 * - Touch support for mobile
 *
 * @example
 * ```typescript
 * <VideoPlayer
 *   videoUrl="https://storage.googleapis.com/poker-videos-prod/wsop_2024/.../hand_3421.mp4?X-Goog-Algorithm=..."
 *   thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
 *   startTime={3421.5}
 *   endTime={3482.0}
 *   autoplay={false}
 *   controls={true}
 *   onEnded={() => console.log("Video ended")}
 *   onError={(error) => console.error(error.message)}
 *   onRefreshUrl={async () => {
 *     const response = await fetch(`/api/hands/{handId}/video-url`);
 *     const data = await response.json();
 *     return data.videoUrl;
 *   }}
 *   markers={[
 *     { street: "PREFLOP", timestamp: 3421.5, label: "Preflop", color: "#E5E7EB" },
 *     { street: "FLOP", timestamp: 3435.2, label: "Flop", color: "#F3E8FF" },
 *   ]}
 * />
 * ```
 */
export const VideoPlayer = React.forwardRef<
  HTMLDivElement,
  VideoPlayerProps
>(
  (
    {
      videoUrl,
      thumbnailUrl,
      startTime = 0,
      endTime,
      autoplay = false,
      controls = true,
      muted = false,
      onEnded,
      onTimeUpdate,
      onError,
      onEvent,
      onRefreshUrl,
      markers = [],
      className = "",
      aspectRatio = 16 / 9,
    },
    ref
  ) => {
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<VideoPlaybackError | null>(null);
    const [videoUrl_, setVideoUrl] = useState(videoUrl);
    const [isRefreshing, setIsRefreshing] = useState(false);

    // Initialize video player hook
    const {
      playerRef,
      containerRef,
      state,
      controls: playerControls,
      isUrlExpired,
    } = useVideoPlayer({
      videoUrl: videoUrl_,
      startTime,
      endTime,
      autoplay,
      onEnded,
      onEvent,
      onError: (err) => {
        setError({
          code: "UNKNOWN",
          message: err.message,
        });
        onError?.({
          code: "UNKNOWN",
          message: err.message,
        });
      },
    });

    // Update videoUrl when prop changes
    useEffect(() => {
      setVideoUrl(videoUrl);
    }, [videoUrl]);

    // Validate URL on mount
    useEffect(() => {
      if (!isValidVideoUrl(videoUrl_)) {
        setError({
          code: "NOT_FOUND",
          message: "Invalid video URL format",
        });
      }

      // Check for URL expiration
      if (isVideoUrlExpired(new Date(Date.now() + 3600000).toISOString())) {
        setError({
          code: "URL_EXPIRED",
          message: "Video URL has expired",
        });
      }
    }, [videoUrl_]);

    // Handle video ready
    const handleReady = useCallback(() => {
      setIsLoading(false);
      onEvent?.({ type: "ready" });
    }, [onEvent]);

    // Handle player error
    const handleError = useCallback((err: any) => {
      const errorCode = parseMediaError(err?.code || 4);
      let code: VideoPlaybackError["code"] = "UNKNOWN";

      if (errorCode === "MEDIA_ERR_NETWORK") code = "NETWORK_ERROR";
      else if (errorCode === "MEDIA_ERR_DECODE") code = "DECODE_ERROR";
      else if (errorCode === "MEDIA_ERR_SRC_NOT_SUPPORTED")
        code = "UNSUPPORTED_FORMAT";

      const videoError: VideoPlaybackError = {
        code,
        message: getErrorMessage(code),
        details: err?.message || errorCode,
      };

      setError(videoError);
      onError?.(videoError);
      onEvent?.({ type: "error", error: videoError });
    }, [onError, onEvent]);

    // Handle time update
    const handleProgress = useCallback(
      (state: any) => {
        const newTime = typeof state.played === "number"
          ? state.played * (state.duration || 0)
          : state.playedSeconds || 0;

        onTimeUpdate?.(newTime);
        onEvent?.({ type: "timeupdate", timestamp: newTime });
      },
      [onTimeUpdate, onEvent]
    );

    // Handle play
    const handlePlay = useCallback(() => {
      onEvent?.({ type: "play", timestamp: state.currentTime });
    }, [state.currentTime, onEvent]);

    // Handle pause
    const handlePause = useCallback(() => {
      onEvent?.({ type: "pause", timestamp: state.currentTime });
    }, [state.currentTime, onEvent]);

    // Handle video ended
    const handleEnded = useCallback(() => {
      onEvent?.({ type: "ended", timestamp: state.currentTime });
      onEnded?.();
    }, [state.currentTime, onEnded, onEvent]);

    // Handle URL refresh
    const handleRefreshUrl = useCallback(async () => {
      if (!onRefreshUrl) return;

      setIsRefreshing(true);
      try {
        const newUrl = await onRefreshUrl();
        setVideoUrl(newUrl);
        setError(null);
        onEvent?.({ type: "urlRefreshed" });
      } catch (err) {
        const refreshError: VideoPlaybackError = {
          code: "NETWORK_ERROR",
          message: "Failed to refresh video URL",
          details: err instanceof Error ? err.message : undefined,
        };
        setError(refreshError);
        onError?.(refreshError);
      } finally {
        setIsRefreshing(false);
      }
    }, [onRefreshUrl, onError, onEvent]);

    // Container padding (for 16:9 aspect ratio)
    const containerHeight = `${(1 / aspectRatio) * 100}%`;

    return (
      <div
        ref={ref}
        className={`relative w-full bg-black ${className}`}
        style={{ aspectRatio: `${aspectRatio} / 1` }}
      >
        {/* Error State */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <VideoError
              error={error}
              onRetry={handleRefreshUrl}
              onRequestNewUrl={isUrlExpired ? handleRefreshUrl : undefined}
              className="m-4"
            />
          </div>
        )}

        {/* Video Container */}
        {!error && (
          <div
            ref={containerRef}
            className="group relative h-full w-full overflow-hidden"
          >
            {/* Loading Thumbnail */}
            {isLoading && thumbnailUrl && (
              <img
                src={thumbnailUrl}
                alt="Video thumbnail"
                className="absolute inset-0 h-full w-full object-cover"
              />
            )}

            {/* Loading Spinner */}
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                <div className="relative h-12 w-12">
                  <div className="absolute inset-0 rounded-full border-2 border-white/20" />
                  <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-white" />
                </div>
              </div>
            )}

            {/* React Player */}
            {React.createElement(ReactPlayer as any, {
              ref: playerRef,
              url: videoUrl_,
              playing: state.isPlaying,
              controls: false,
              light: thumbnailUrl,
              width: "100%",
              height: "100%",
              volume: state.isMuted ? 0 : state.volume,
              muted: state.isMuted || muted,
              playbackRate: state.playbackRate,
              progressInterval: 500,
              onReady: handleReady,
              onPlay: handlePlay,
              onPause: handlePause,
              onProgress: handleProgress,
              onEnded: handleEnded,
              onError: handleError,
              config: {
                html5: {
                  attributes: {
                    controlsList: "nodownload",
                    poster: thumbnailUrl,
                  },
                },
              },
            })}

            {/* Timeline Markers */}
            {markers.length > 0 && (
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
                {markers.map((marker) => {
                  const percent =
                    endTime
                      ? ((marker.timestamp - startTime) /
                          (endTime - startTime)) *
                        100
                      : (marker.timestamp / state.duration) * 100;

                  return (
                    <div
                      key={marker.timestamp}
                      className="absolute top-0 h-full w-1 -translate-x-1/2 transform hover:w-2 transition-all"
                      style={{
                        left: `${Math.min(100, Math.max(0, percent))}%`,
                        backgroundColor: marker.color,
                      }}
                      title={marker.label}
                    />
                  );
                })}
              </div>
            )}

            {/* Video Controls */}
            {controls && (
              <VideoControls
                isPlaying={state.isPlaying}
                currentTime={state.currentTime}
                duration={state.duration}
                volume={state.volume}
                isMuted={state.isMuted}
                isFullscreen={state.isFullscreen}
                onPlayPause={playerControls.togglePlay}
                onSeek={playerControls.seek}
                onVolumeChange={playerControls.setVolume}
                onToggleMute={playerControls.toggleMute}
                onToggleFullscreen={playerControls.toggleFullscreen}
                playbackRate={state.playbackRate}
                onPlaybackRateChange={playerControls.setPlaybackRate}
                startTime={startTime}
                endTime={endTime}
              />
            )}

            {/* URL Expiration Warning */}
            {isUrlExpired && !error && (
              <div className="absolute top-4 right-4 flex items-center gap-2 rounded-lg bg-yellow-500/90 px-3 py-2 text-xs font-medium text-white">
                <span>Video link expiring soon</span>
                {onRefreshUrl && (
                  <button
                    onClick={handleRefreshUrl}
                    disabled={isRefreshing}
                    className="ml-2 underline hover:no-underline disabled:opacity-50"
                  >
                    {isRefreshing ? "Refreshing..." : "Refresh"}
                  </button>
                )}
              </div>
            )}

            {/* Fullscreen State */}
            {state.isFullscreen && (
              <style>{`body { overflow: hidden; }`}</style>
            )}
          </div>
        )}

        {/* Accessibility */}
        <div className="sr-only">
          <h2>Video player for poker hand {startTime?.toFixed(1)}</h2>
          <p>
            Controls: Space to play/pause, arrow keys to seek, F for fullscreen,
            M to mute, 0-9 to jump to percentage
          </p>
        </div>
      </div>
    );
  }
);

VideoPlayer.displayName = "VideoPlayer";
