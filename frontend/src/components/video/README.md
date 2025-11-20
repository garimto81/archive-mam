# Video Player Components

Comprehensive video player system for poker hand replays with GCS Signed URL support.

## Components

### VideoPlayer

Main video player component with integrated controls, keyboard shortcuts, and error handling.

**Features:**
- React Player integration (MP4, WebM, HLS support)
- Custom video controls (play/pause, seek, volume, fullscreen)
- Keyboard shortcuts (Space, arrows, F, M, 0-9)
- Responsive 16:9 aspect ratio
- GCS signed URL support with expiration handling
- Thumbnail loading state
- Error handling and recovery
- Accessibility (ARIA labels, keyboard navigation)
- Touch support for mobile

**Props:**
```typescript
interface VideoPlayerProps {
  videoUrl: string;                    // GCS signed URL
  thumbnailUrl?: string;               // Thumbnail while loading
  startTime?: number;                  // Start time in seconds
  endTime?: number;                    // End time in seconds
  autoplay?: boolean;                  // Auto-play on load
  controls?: boolean;                  // Show controls
  muted?: boolean;                     // Mute by default
  onEnded?: () => void;                // Callback on end
  onTimeUpdate?: (time: number) => void;
  onError?: (error: VideoPlaybackError) => void;
  onEvent?: (event: any) => void;
  onRefreshUrl?: () => Promise<string>; // Refresh URL handler
  markers?: HandTimelineMarker[];       // Street markers
  className?: string;
  aspectRatio?: number;
}
```

**Example:**
```typescript
<VideoPlayer
  videoUrl="https://storage.googleapis.com/poker-videos-prod/wsop_2024/..."
  thumbnailUrl="https://storage.googleapis.com/poker-videos-prod/thumbnails/hand_3421.jpg"
  startTime={3421.5}
  endTime={3482.0}
  autoplay={false}
  onEnded={() => console.log("Video ended")}
  onError={(error) => console.error(error.message)}
  onRefreshUrl={async () => {
    const response = await fetch(`/api/hands/{handId}/video-url`);
    const data = await response.json();
    return data.videoUrl;
  }}
  markers={[
    { street: "PREFLOP", timestamp: 3421.5, label: "Preflop", color: "#E5E7EB" },
    { street: "FLOP", timestamp: 3435.2, label: "Flop", color: "#F3E8FF" },
    { street: "RIVER", timestamp: 3465.8, label: "River", color: "#DBEAFE" },
  ]}
/>
```

### VideoControls

Custom video controls overlay with play/pause, seek, volume, and fullscreen buttons.

**Features:**
- Play/pause button
- Progress bar with scrubbing
- Time display (current / duration)
- Volume slider with mute toggle
- Playback speed selector (0.5x - 2x)
- Fullscreen button
- Keyboard shortcuts hint
- Responsive design
- Mobile touch support

**Props:**
```typescript
interface VideoControlsProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  isFullscreen: boolean;
  onPlayPause: () => void;
  onSeek: (time: number) => void;
  onVolumeChange: (volume: number) => void;
  onToggleMute: () => void;
  onToggleFullscreen: () => void;
  startTime?: number;
  endTime?: number;
  playbackRates?: number[];
  playbackRate?: number;
  onPlaybackRateChange?: (rate: number) => void;
  className?: string;
}
```

### VideoError

Error display component with user-friendly messages and recovery options.

**Features:**
- Error icon and title
- User-friendly error messages
- Detailed error information (expandable)
- Retry button
- Refresh URL button (for expired URLs)
- Help section with troubleshooting steps
- Contact support link
- Error code display

**Props:**
```typescript
interface VideoErrorProps {
  error: VideoPlaybackError;
  onRetry?: () => void;
  onRequestNewUrl?: () => void;
  customMessage?: string;
  className?: string;
}
```

## Hooks

### useVideoPlayer

Comprehensive state management hook for video player functionality.

**Features:**
- Playback state management
- Keyboard event handling
- Fullscreen API integration
- Error handling
- Auto-seek to start time
- Loop between start/end times
- URL expiration monitoring

**Returns:**
```typescript
interface UseVideoPlayerReturn {
  playerRef: RefObject<any>;
  containerRef: RefObject<HTMLDivElement>;
  state: VideoPlayerState;
  controls: VideoPlayerControls;
  error: Error | null;
  timeRemaining: number;
  isUrlExpired: boolean;
}
```

**Example:**
```typescript
const {
  playerRef,
  containerRef,
  state,
  controls,
  error,
  isUrlExpired,
} = useVideoPlayer({
  videoUrl: "https://storage.googleapis.com/...",
  startTime: 3421.5,
  endTime: 3482.0,
  autoplay: false,
  onEnded: () => console.log("Video ended"),
});
```

## Utilities

### formatTime(seconds: number): string

Format seconds to human-readable time string.

```typescript
formatTime(90) // "1:30"
formatTime(3661) // "1:01:01"
```

### isVideoUrlExpired(expiresAt: string): boolean

Check if a GCS signed URL is expired.

```typescript
if (isVideoUrlExpired(metadata.expiresAt)) {
  const newUrl = await refreshVideoUrl();
}
```

### getTimeUntilExpiration(expiresAt: string): number

Get remaining seconds until URL expires.

```typescript
const secondsRemaining = getTimeUntilExpiration(metadata.expiresAt);
if (secondsRemaining < 300) {
  refreshVideoUrl(); // Less than 5 minutes left
}
```

### isValidVideoUrl(url: string): boolean

Validate if a URL is a valid video source.

```typescript
if (isValidVideoUrl(videoUrl)) {
  player.load(videoUrl);
}
```

### getMimeType(url: string): string

Get MIME type from video URL.

```typescript
const mimeType = getMimeType("video.mp4");
// Returns: "video/mp4"
```

### supportsFullscreen(): boolean

Check if browser supports fullscreen API.

```typescript
if (supportsFullscreen()) {
  showFullscreenButton();
}
```

### supportsPictureInPicture(): boolean

Check if browser supports Picture-in-Picture API.

```typescript
if (supportsPictureInPicture()) {
  showPipButton();
}
```

### getErrorMessage(code: string): string

Get user-friendly error message.

```typescript
const message = getErrorMessage("URL_EXPIRED");
// "Video URL has expired. Please refresh the page."
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| → | Seek forward 5 seconds |
| ← | Seek backward 5 seconds |
| F | Toggle fullscreen |
| M | Toggle mute |
| 0-9 | Jump to percentage (0% = 0, 5 = 50%, 9 = 90%) |
| ↑ | Increase volume 10% |
| ↓ | Decrease volume 10% |

## Accessibility

- ARIA labels on all buttons
- Keyboard navigation support
- Semantic HTML structure
- Screen reader friendly
- Sufficient color contrast
- Focus visible indicators

## Type Definitions

All components are fully typed with TypeScript. Import types from `@/types/video`:

```typescript
import type {
  VideoMetadata,
  VideoPlayerState,
  VideoPlaybackError,
  HandTimelineMarker,
  VideoQualitySettings,
  VideoPlaybackPosition,
  VideoPlaybackRange,
} from "@/types/video";
```

## GCS Signed URL Handling

The player includes built-in support for GCS signed URLs with expiration handling:

1. **Expiration Monitoring**: Tracks URL expiration and warns before expiry
2. **Automatic Refresh**: Calls `onRefreshUrl` to get new URL when expired
3. **Error Recovery**: Displays error with refresh option if URL has expired
4. **URL Validation**: Validates URL format on mount

Example with URL refresh:

```typescript
<VideoPlayer
  videoUrl={url}
  onRefreshUrl={async () => {
    const response = await fetch(`/api/hands/${handId}/video-url`);
    const { videoUrl } = await response.json();
    return videoUrl;
  }}
/>
```

## Error Handling

Supported error codes:

- `UNSUPPORTED_FORMAT`: Browser doesn't support video format
- `NETWORK_ERROR`: Failed to load video (connection issue)
- `DECODE_ERROR`: Video file is corrupted
- `URL_EXPIRED`: GCS signed URL has expired
- `NOT_FOUND`: Video file doesn't exist
- `UNKNOWN`: Unexpected error

## Performance Considerations

1. **Lazy Loading**: Video loads on demand, not preloaded
2. **Thumbnail Preloading**: Shows thumbnail while video loads
3. **Responsive Sizing**: Uses CSS aspect ratio for efficiency
4. **Memoized Controls**: Callbacks are memoized to prevent unnecessary re-renders
5. **Event Debouncing**: Progress updates throttled to 500ms intervals

## Browser Support

- Chrome 90+
- Firefox 85+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari 14+, Android Chrome)

## Installation

```bash
npm install react-player
```

## Related Files

- `src/types/video.ts` - Type definitions
- `src/lib/video/utils.ts` - Utility functions
- `src/hooks/useVideoPlayer.ts` - State management hook
