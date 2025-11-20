'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Play, AlertCircle } from 'lucide-react';
import ReactPlayer from 'react-player';

interface VideoPlayerProps {
  videoUrl?: string;
  handId: string;
  className?: string;
}

/**
 * VideoPlayer Component
 *
 * Embedded video player for hand replay:
 * - YouTube/Vimeo support via react-player
 * - Thumbnail with play button
 * - Fallback message if no video available
 * - Responsive aspect ratio (16:9)
 *
 * @param videoUrl - URL to video (YouTube, Vimeo, etc.)
 * @param handId - Hand identifier for analytics
 */
export function VideoPlayer({ videoUrl, handId, className }: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasError, setHasError] = useState(false);

  // If no video URL provided
  if (!videoUrl) {
    return (
      <Card
        className={cn('p-8 bg-gray-50 border-dashed', className)}
        data-testid="video-player-empty"
      >
        <div className="flex flex-col items-center justify-center text-center space-y-3">
          <AlertCircle className="w-12 h-12 text-gray-400" />
          <p className="text-sm font-medium text-gray-600">No video available for this hand</p>
          <p className="text-xs text-gray-500">
            Hand ID: {handId}
          </p>
        </div>
      </Card>
    );
  }

  // If video failed to load
  if (hasError) {
    return (
      <Card
        className={cn('p-8 bg-red-50 border-red-200', className)}
        data-testid="video-player-error"
      >
        <div className="flex flex-col items-center justify-center text-center space-y-3">
          <AlertCircle className="w-12 h-12 text-red-500" />
          <p className="text-sm font-medium text-red-700">Failed to load video</p>
          <p className="text-xs text-red-600">
            The video may have been removed or is temporarily unavailable.
          </p>
          <a
            href={videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:text-blue-700 underline"
          >
            Open video in new tab
          </a>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('overflow-hidden', className)} data-testid="video-player">
      {/* Video Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2">
          <Play className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-bold text-gray-900">Hand Replay Video</h2>
        </div>
      </div>

      {/* Video Player */}
      <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
        <div className="absolute inset-0 bg-black">
          <ReactPlayer
            url={videoUrl}
            playing={isPlaying}
            controls={true}
            width="100%"
            height="100%"
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onError={() => setHasError(true)}
            config={{
              youtube: {
                playerVars: {
                  showinfo: 1,
                  modestbranding: 1,
                },
              },
              vimeo: {
                playerOptions: {
                  byline: false,
                  portrait: false,
                },
              },
            }}
          />
        </div>
      </div>

      {/* Video Info */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>Hand ID: {handId}</span>
          <a
            href={videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 underline"
          >
            Watch on {videoUrl.includes('youtube') ? 'YouTube' : 'external site'}
          </a>
        </div>
      </div>
    </Card>
  );
}
