# GCS Signed URL Management

Complete system for managing GCS Signed URL expiration with automatic refresh, validation, and monitoring.

## Overview

This module provides utilities for handling GCS Signed URLs in video streaming applications:

- **URL Validation**: Check format, expiration, and validity
- **Expiration Detection**: Identify expired or soon-to-expire URLs
- **Auto-Refresh**: Automatically refresh URLs before expiration
- **Time Tracking**: Monitor time remaining until expiration
- **Error Handling**: Comprehensive error management

## Files

### URL Validator (`url-validator.ts`)

Core utilities for URL validation and expiration management.

**Key Functions:**

```typescript
// Check if URL is expired
isUrlExpired(url: string): boolean

// Get seconds until URL expires
getTimeUntilExpiration(url: string): number | null

// Check if URL is expiring soon
isUrlExpiringSoon(url: string, thresholdSeconds?: number): boolean

// Validate GCS Signed URL format
isValidGcsSignedUrl(url: string): boolean

// Extract expiration from URL
getUrlExpiration(url: string): Date | null

// Format time remaining as human-readable string
formatTimeRemaining(seconds: number): string

// Get bucket name from URL
getBucketName(url: string): string | null

// Get object path from URL
getObjectPath(url: string): string | null

// Compare URLs for equality
isSameResource(url1: string, url2: string): boolean

// Comprehensive validation
validateGcsSignedUrl(url: string, expirationThreshold?: number): UrlValidationResult
```

**GCS Signed URL Formats Supported:**

1. **Standard Format:**
   ```
   https://storage.googleapis.com/bucket/path/file.mp4?Expires=1234567890&Signature=...
   ```

2. **X-Goog-Credential Format:**
   ```
   https://storage.googleapis.com/bucket/path/file.mp4?X-Goog-Expires=3600&X-Goog-Date=20250118T143000Z&X-Goog-Signature=...
   ```

3. **Virtual-hosted Format:**
   ```
   https://bucket.storage.googleapis.com/path/file.mp4?Expires=1234567890&Signature=...
   ```

### API Client (`../api/video.ts`)

Enhanced video URL fetching with expiration management.

**Key Functions:**

```typescript
// Fetch video URL from API
fetchVideoUrl(handId: string, options?: VideoApiOptions): Promise<VideoMetadata>

// Refresh URL if expired or expiring soon
refreshVideoUrlIfNeeded(
  handId: string,
  currentUrl: string,
  options?: VideoApiOptions
): Promise<VideoMetadata | null>

// Fetch multiple videos in parallel
fetchVideoUrlsBatch(handIds: string[], options?: VideoApiOptions): Promise<Map<string, VideoMetadata>>

// Batch fetch with error details
fetchVideoUrlsBatchWithErrors(
  handIds: string[],
  options?: VideoApiOptions
): Promise<PromiseSettledResult<VideoMetadata>[]>

// Background prefetch
prefetchVideoUrl(handId: string): void

// Cache management
getCachedVideoUrl(handId: string): VideoMetadata | null
clearVideoCache(): void
clearVideoFromCache(handId: string): boolean
isVideoCached(handId: string): boolean

// Time tracking
getVideoUrlTimeRemaining(handId: string): number | null
getFormattedExpirationTime(handId: string): string | null

// Formatting
formatVideoDuration(seconds: number): string
getPlaybackRange(metadata: VideoMetadata): string
```

**Features:**

- 5-minute cache TTL (configurable)
- Automatic validation before caching
- Expiration buffer (1 minute) prevents edge cases
- Retry logic with exponential backoff
- Comprehensive error handling
- Development logging

## Usage Examples

### Basic Video Fetching

```typescript
import { fetchVideoUrl } from "@/lib/api/video";

async function loadVideo(handId: string) {
  try {
    const metadata = await fetchVideoUrl(handId);
    console.log("Video URL:", metadata.videoUrl);
    console.log("Expires at:", metadata.expiresAt);
  } catch (error) {
    console.error("Failed to load video:", error);
  }
}
```

### Checking URL Expiration

```typescript
import { isUrlExpired, isUrlExpiringSoon, getTimeUntilExpiration } from "@/lib/video/url-validator";

const url = "https://storage.googleapis.com/bucket/video.mp4?Expires=...";

// Check if expired
if (isUrlExpired(url)) {
  console.log("URL is expired");
}

// Check if expiring soon (< 5 minutes)
if (isUrlExpiringSoon(url, 300)) {
  console.log("URL expiring soon");
}

// Get time remaining
const remaining = getTimeUntilExpiration(url);
if (remaining) {
  console.log(`URL expires in ${remaining} seconds`);
}
```

### Batch Operations

```typescript
import { fetchVideoUrlsBatch } from "@/lib/api/video";

async function loadSearchResults(handIds: string[]) {
  const videoMap = await fetchVideoUrlsBatch(handIds);

  videoMap.forEach((metadata, handId) => {
    console.log(`${handId}: ${metadata.videoUrl}`);
  });
}
```

### Using with React Hook

```typescript
import { useVideoUrl } from "@/hooks/useVideoUrl";

function VideoPlayer({ handId }: { handId: string }) {
  const {
    videoMetadata,
    isLoading,
    error,
    timeUntilExpiration,
    formattedTimeRemaining,
    refresh,
    forceRefresh
  } = useVideoUrl({
    handId,
    autoRefresh: true,
    refreshThreshold: 300
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!videoMetadata) return <div>No video</div>;

  return (
    <>
      <video src={videoMetadata.videoUrl} controls />
      <p>Expires in {formattedTimeRemaining}</p>
      <button onClick={refresh}>Refresh URL</button>
    </>
  );
}
```

### URL Expiration Warning Component

```typescript
import { UrlExpirationWarning } from "@/components/video";

function VideoDisplay({ timeRemaining, onRefresh }: Props) {
  return (
    <>
      <UrlExpirationWarning
        timeUntilExpiration={timeRemaining}
        onRefresh={onRefresh}
        autoRefresh={true}
      />
      <video src={videoUrl} />
    </>
  );
}
```

## Auto-Refresh Logic

The hook automatically refreshes URLs when they expire or are expiring soon:

1. **Initial Load:** Fetches URL on mount
2. **Time Tracking:** Updates remaining time every second
3. **Expiration Check:** Every minute, checks if URL crossed refresh threshold
4. **Auto-Refresh:** If threshold crossed, fetches fresh URL
5. **State Update:** Updates component state with new URL

### Refresh Thresholds

- **Default:** 300 seconds (5 minutes)
- **Configurable:** Pass `refreshThreshold` option
- **Recommendation:** 5-10 minutes for optimal UX

## Caching Strategy

### Cache Invalidation

Cached URLs are considered invalid if:

1. URL has expired (current time >= expiration time)
2. URL is expiring soon (< 5 minutes remaining)
3. Cache entry is older than 5 minutes (TTL)

### Best Practices

```typescript
// Bypass cache to force fresh URL
const fresh = await fetchVideoUrl(handId, { bypassCache: true });

// Clear cache when needed
clearVideoCache(); // Clear all
clearVideoFromCache(handId); // Clear specific

// Check cache before fetching
const cached = getCachedVideoUrl(handId);
if (cached) {
  // Use cached URL
} else {
  // Fetch new URL
}
```

## Error Handling

### Error Types

All functions throw typed errors:

```typescript
import { ValidationError, NotFoundError, NetworkError, TimeoutError, RateLimitError } from "@/types/errors";

try {
  const metadata = await fetchVideoUrl(handId);
} catch (error) {
  if (error instanceof ValidationError) {
    // Invalid hand ID or URL format
  } else if (error instanceof NotFoundError) {
    // Video not found
  } else if (error instanceof NetworkError) {
    // Network error
  } else if (error instanceof TimeoutError) {
    // Request timeout
  } else if (error instanceof RateLimitError) {
    // Rate limit exceeded
  }
}
```

### Retry Logic

```typescript
import { useVideoUrl } from "@/hooks/useVideoUrl";

function VideoPlayer({ handId }: Props) {
  const { error, retry } = useVideoUrl({ handId });

  if (error) {
    return (
      <div>
        <p>Error: {error.message}</p>
        <button onClick={retry}>Retry</button>
      </div>
    );
  }
}
```

## Performance Considerations

### Caching

- **Cache TTL:** 5 minutes (configurable)
- **Expiration Buffer:** 1 minute before actual expiration
- **Check Frequency:** Every second for time remaining, every minute for expiration

### Network

- **Retry Logic:** Exponential backoff (100ms, 200ms, 400ms...)
- **Timeout:** 5 seconds (configurable)
- **Parallel Requests:** Use batch functions for multiple videos

### Memory

- **Cache Size:** Typically <100KB for 100 cached videos
- **Cleanup:** Automatic on component unmount, manual via `clearVideoCache()`

## Security Considerations

### Signed URLs

- Generated server-side with limited expiration (typically 1 hour)
- Include signature preventing tampering
- Validate format and expiration before use
- Never log complete URLs in production

### Development

- Enabled detailed logging with `NODE_ENV === "development"`
- Logs include hand IDs but truncated URLs
- Remove logs in production builds

## Testing

### Unit Tests

```typescript
import { isUrlExpired, getTimeUntilExpiration } from "@/lib/video/url-validator";

describe("URL Validator", () => {
  test("detects expired URLs", () => {
    const pastDate = Math.floor(Date.now() / 1000) - 3600;
    const url = `https://storage.googleapis.com/bucket/file?Expires=${pastDate}`;
    expect(isUrlExpired(url)).toBe(true);
  });

  test("calculates time remaining", () => {
    const futureTime = Math.floor(Date.now() / 1000) + 3600;
    const url = `https://storage.googleapis.com/bucket/file?Expires=${futureTime}`;
    const remaining = getTimeUntilExpiration(url);
    expect(remaining).toBeGreaterThan(3590);
    expect(remaining).toBeLessThanOrEqual(3600);
  });
});
```

### Integration Tests

```typescript
describe("Video API with expiration", () => {
  test("refreshes expired URL", async () => {
    const metadata = await fetchVideoUrl("hand_123");
    const refreshed = await refreshVideoUrlIfNeeded(
      "hand_123",
      "expired_url?Expires=0"
    );
    expect(refreshed).not.toBeNull();
    expect(refreshed?.expiresAt).not.toBe(metadata.expiresAt);
  });

  test("batches multiple video fetches", async () => {
    const map = await fetchVideoUrlsBatch(["hand_1", "hand_2", "hand_3"]);
    expect(map.size).toBe(3);
    expect(map.has("hand_1")).toBe(true);
  });
});
```

## Troubleshooting

### Common Issues

**"Invalid GCS Signed URL format"**
- Ensure URL includes required parameters (Expires or X-Goog-Date)
- Check URL hasn't been modified or truncated
- Verify signature is present

**"URL has expired"**
- Server generated URL that was already expired
- System clock out of sync with GCP
- Check server's time synchronization

**"Rate limit exceeded"**
- Too many requests in short time
- Use exponential backoff (built-in)
- Implement request batching

**"Network error"**
- Check internet connection
- Verify API endpoint URL
- Check CORS configuration
- Review network logs in browser

## Examples

Complete examples available in:
- `components/video/VideoPlayerWithExpiration.example.tsx` - React integration examples
- `hooks/useVideoUrl.ts` - Hook implementation details
- `lib/api/video.ts` - API client documentation

## API Reference

See the JSDoc comments in each file for detailed API documentation:

- `lib/video/url-validator.ts` - URL validation functions
- `lib/api/video.ts` - Video API client
- `hooks/useVideoUrl.ts` - React hook
- `components/video/UrlExpirationWarning.tsx` - Warning component

## Related

- [GCS Signed URLs Documentation](https://cloud.google.com/storage/docs/access-control/signed-urls)
- [Video Types](../types/video.ts)
- [API Types](../types/api.ts)
