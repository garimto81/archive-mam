/**
 * VideoPlayer Component Examples and Usage Patterns
 *
 * This file demonstrates various ways to use the VideoPlayer component
 * in real-world scenarios.
 */

import React, { useState } from "react";
import { VideoPlayer } from "./VideoPlayer";
import type { VideoPlaybackError, HandTimelineMarker } from "@/types/video";

/**
 * Example 1: Basic Video Player
 *
 * Minimal setup with default settings.
 */
export function BasicVideoPlayerExample() {
  return (
    <VideoPlayer
      videoUrl="https://storage.googleapis.com/poker-videos-prod/wsop_2024/main_event/day5_table3.mp4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=..."
      thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
      startTime={3421.5}
      endTime={3482.0}
    />
  );
}

/**
 * Example 2: Video Player with Event Handlers
 *
 * Demonstrates handling video events like play, pause, seek, and errors.
 */
export function VideoPlayerWithEventsExample() {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleError = (error: VideoPlaybackError) => {
    // Send error to analytics in production
    // analytics.track("video_error", { code: error.code });
  };

  const handleEvent = (event: any) => {
    // Track video metrics
    // if (event.type === "play") {
    //   analytics.track("video_play");
    // } else if (event.type === "pause") {
    //   analytics.track("video_pause", { timestamp: event.timestamp });
    // }
  };

  return (
    <div className="space-y-4">
      <VideoPlayer
        videoUrl="https://storage.googleapis.com/poker-videos-prod/..."
        thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/..."
        startTime={3421.5}
        endTime={3482.0}
        autoplay={false}
        onTimeUpdate={(time) => setCurrentTime(time)}
        onError={handleError}
        onEvent={handleEvent}
        onEnded={() => {
          // Navigate to next hand
          // router.push(`/hands/${nextHandId}`);
        }}
      />

      {/* Display current playback time */}
      <div className="text-sm text-gray-600">
        Current time: {Math.floor(currentTime)}s
      </div>
    </div>
  );
}

/**
 * Example 3: Video Player with URL Refresh (GCS Signed URL Expiration)
 *
 * Demonstrates handling GCS signed URL expiration by refreshing the URL.
 */
export function VideoPlayerWithUrlRefreshExample() {
  const [videoUrl, setVideoUrl] = useState(
    "https://storage.googleapis.com/poker-videos-prod/..."
  );
  const [handId] = useState("wsop_2024_main_event_hand_3421");

  const handleRefreshUrl = async () => {
    try {
      // Call backend API to get new signed URL
      const response = await fetch(`/api/hands/${handId}/video-url`);

      if (!response.ok) {
        throw new Error(`Failed to refresh URL: ${response.statusText}`);
      }

      const data = await response.json();
      setVideoUrl(data.videoUrl);

      return data.videoUrl;
    } catch (error) {
      throw error;
    }
  };

  return (
    <VideoPlayer
      key={videoUrl} // Force re-render when URL changes
      videoUrl={videoUrl}
      thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
      startTime={3421.5}
      endTime={3482.0}
      onRefreshUrl={handleRefreshUrl}
      onError={(error) => {
        // URL expired handled by onRefreshUrl
      }}
    />
  );
}

/**
 * Example 4: Video Player with Timeline Markers
 *
 * Shows poker street markers on the video timeline.
 */
export function VideoPlayerWithMarkersExample() {
  // Timeline markers for different poker streets
  const markers: HandTimelineMarker[] = [
    {
      street: "PREFLOP",
      timestamp: 3421.5,
      label: "Preflop action",
      color: "#E5E7EB", // Gray
    },
    {
      street: "FLOP",
      timestamp: 3435.2,
      label: "Flop - Junglemann leads out",
      color: "#F3E8FF", // Purple
    },
    {
      street: "TURN",
      timestamp: 3450.8,
      label: "Turn - Villain raises",
      color: "#FEE2E2", // Red
    },
    {
      street: "RIVER",
      timestamp: 3465.8,
      label: "River - Hero makes huge call",
      color: "#DBEAFE", // Blue
    },
  ];

  return (
    <VideoPlayer
      videoUrl="https://storage.googleapis.com/poker-videos-prod/..."
      thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
      startTime={3421.5}
      endTime={3482.0}
      markers={markers}
    />
  );
}

/**
 * Example 5: Video Player in Hand Detail Page
 *
 * Complete hand detail with video, metadata, and action log.
 */
export function HandDetailPageExample() {
  const handData = {
    hand_id: "wsop_2024_main_event_hand_3421",
    hero_name: "Junglemann",
    villain_name: "Phil Ivey",
    pot_bb: 145.5,
    result: "WIN",
    tags: ["HERO_CALL", "RIVER_DECISION", "HIGH_STAKES"],
    description:
      "Junglemann makes an insane river call with ace-high against Phil Ivey on a paired board. Incredible read and execution.",
    video_url:
      "https://storage.googleapis.com/poker-videos-prod/wsop_2024/main_event/day5_table3.mp4?X-Goog-Algorithm=...",
    video_start_time: 3421.5,
    video_end_time: 3482.0,
    thumbnail_url:
      "https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg",
  };

  const timelineMarkers: HandTimelineMarker[] = [
    {
      street: "PREFLOP",
      timestamp: 3421.5,
      label: "Preflop",
      color: "#E5E7EB",
    },
    {
      street: "FLOP",
      timestamp: 3435.2,
      label: "Flop",
      color: "#F3E8FF",
    },
    {
      street: "RIVER",
      timestamp: 3465.8,
      label: "Hero call",
      color: "#DBEAFE",
    },
  ];

  const [videoError, setVideoError] = useState<VideoPlaybackError | null>(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Video Player - Takes up 2/3 on large screens */}
      <div className="lg:col-span-2">
        <VideoPlayer
          videoUrl={handData.video_url}
          thumbnailUrl={handData.thumbnail_url}
          startTime={handData.video_start_time}
          endTime={handData.video_end_time}
          markers={timelineMarkers}
          autoplay={false}
          onError={(error) => {
            setVideoError(error);
          }}
          onRefreshUrl={async () => {
            const response = await fetch(
              `/api/hands/${handData.hand_id}/video-url`
            );
            const data = await response.json();
            return data.videoUrl;
          }}
        />

        {videoError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="font-medium text-red-900">Playback Error</p>
            <p className="text-sm text-red-700">{videoError.message}</p>
          </div>
        )}
      </div>

      {/* Hand Details - Takes up 1/3 on large screens */}
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-bold mb-4">Hand #{handData.hand_id}</h2>

          <div className="space-y-3 text-sm">
            <div>
              <span className="text-gray-600">Hero:</span>
              <span className="ml-2 font-medium">{handData.hero_name}</span>
            </div>

            <div>
              <span className="text-gray-600">Villain:</span>
              <span className="ml-2 font-medium">{handData.villain_name}</span>
            </div>

            <div>
              <span className="text-gray-600">Pot:</span>
              <span className="ml-2 font-medium">{handData.pot_bb} BB</span>
            </div>

            <div>
              <span className="text-gray-600">Result:</span>
              <span
                className={`ml-2 font-medium ${
                  handData.result === "WIN"
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {handData.result}
              </span>
            </div>
          </div>

          {/* Tags */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs font-semibold text-gray-600 mb-2">TAGS</p>
            <div className="flex flex-wrap gap-1">
              {handData.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs font-semibold text-gray-600 mb-2">
              DESCRIPTION
            </p>
            <p className="text-sm text-gray-700">{handData.description}</p>
          </div>
        </div>

        {/* Action Log */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3">Action Log</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span>Junglemann posts SB</span>
              <span className="text-gray-500">0.5 BB</span>
            </div>
            <div className="flex justify-between">
              <span>Phil Ivey posts BB</span>
              <span className="text-gray-500">1 BB</span>
            </div>
            <div className="flex justify-between">
              <span>Junglemann raises to 3 BB</span>
              <span className="text-gray-500">3 BB</span>
            </div>
            <div className="flex justify-between">
              <span>Phil Ivey calls</span>
              <span className="text-gray-500">3 BB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Example 6: Mobile-Optimized Video Player
 *
 * Responsive design optimized for mobile devices.
 */
export function MobileVideoPlayerExample() {
  return (
    <div className="w-full max-w-md mx-auto">
      <VideoPlayer
        videoUrl="https://storage.googleapis.com/poker-videos-prod/..."
        thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
        startTime={3421.5}
        endTime={3482.0}
        autoplay={false}
        controls={true}
        className="rounded-lg overflow-hidden shadow-lg"
      />

      {/* Mobile-friendly metadata below video */}
      <div className="mt-4 space-y-2">
        <h3 className="font-bold text-lg">Junglemann vs Phil Ivey</h3>
        <p className="text-sm text-gray-600">WSOP 2024 Main Event - Day 5</p>
        <div className="flex gap-2 flex-wrap">
          <span className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
            HERO_CALL
          </span>
          <span className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
            RIVER
          </span>
          <span className="inline-block bg-green-100 text-green-700 text-xs px-2 py-1 rounded">
            WIN
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Example 7: Video Player with Loading States
 *
 * Shows how to handle loading and error states.
 */
export function VideoPlayerWithLoadingExample() {
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(true);

  const handleVideoReady = () => {
    setIsLoadingMetadata(false);
  };

  return (
    <div className="space-y-4">
      <div className="relative">
        {isLoadingMetadata && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
            <div className="text-white text-center">
              <div className="inline-block mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              </div>
              <p>Loading hand video...</p>
            </div>
          </div>
        )}

        <VideoPlayer
          videoUrl="https://storage.googleapis.com/poker-videos-prod/..."
          thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
          startTime={3421.5}
          endTime={3482.0}
          onEvent={(event) => {
            if (event.type === "ready") {
              handleVideoReady();
            }
          }}
        />
      </div>

      {!isLoadingMetadata && (
        <p className="text-sm text-green-600">
          ✓ Video ready to play. Use Space to play/pause.
        </p>
      )}
    </div>
  );
}
