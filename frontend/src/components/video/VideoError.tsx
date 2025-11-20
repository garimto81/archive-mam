/**
 * VideoError Component
 *
 * Displays video playback errors with user-friendly messages
 * and action buttons for recovery.
 */

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import type { VideoPlaybackError } from "@/types/video";
import { getErrorMessage } from "@/lib/video/utils";

/**
 * Props for VideoError component
 */
export interface VideoErrorProps {
  /** Video error object */
  error: VideoPlaybackError;

  /** Callback when retry button is clicked */
  onRetry?: () => void;

  /** Callback to request a new video URL (for expired URLs) */
  onRequestNewUrl?: () => void;

  /** Custom error message to override default */
  customMessage?: string;

  /** CSS class name for styling */
  className?: string;
}

/**
 * VideoError Component
 *
 * Displays comprehensive error information with:
 * - Error icon and message
 * - User-friendly explanation
 * - Retry and refresh buttons
 * - Contact support link
 *
 * @example
 * ```typescript
 * <VideoError
 *   error={{
 *     code: "URL_EXPIRED",
 *     message: "The video URL has expired"
 *   }}
 *   onRetry={() => location.reload()}
 *   onRequestNewUrl={() => refreshUrl()}
 * />
 * ```
 */
export const VideoError = React.forwardRef<
  HTMLDivElement,
  VideoErrorProps
>(
  (
    {
      error,
      onRetry,
      onRequestNewUrl,
      customMessage,
      className = "",
    },
    ref
  ) => {
    const message = customMessage || getErrorMessage(error.code, error.details);

    const isUrlExpired = error.code === "URL_EXPIRED";

    return (
      <div
        ref={ref}
        className={`relative flex flex-col items-center justify-center gap-4 rounded-lg border border-red-500/30 bg-red-50 p-8 dark:bg-red-950/20 dark:border-red-500/50 ${className}`}
      >
        {/* Error Icon */}
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
          <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
        </div>

        {/* Error Message */}
        <div className="text-center">
          <h3 className="mb-2 text-lg font-semibold text-red-900 dark:text-red-200">
            {getErrorTitle(error.code)}
          </h3>
          <p className="text-sm text-red-700 dark:text-red-300">{message}</p>

          {/* Detailed Error Info */}
          {error.details && (
            <details className="mt-3 text-xs text-red-600 dark:text-red-400">
              <summary className="cursor-pointer font-medium hover:underline">
                Details
              </summary>
              <pre className="mt-2 overflow-x-auto rounded bg-black/10 p-2 font-mono">
                {error.details}
              </pre>
            </details>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 justify-center">
          {/* Retry Button */}
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 hover:bg-red-700 px-4 py-2 font-medium text-white transition-colors dark:bg-red-700 dark:hover:bg-red-600"
              aria-label="Retry loading video"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Retry</span>
            </button>
          )}

          {/* Request New URL Button (for expired URLs) */}
          {isUrlExpired && onRequestNewUrl && (
            <button
              onClick={onRequestNewUrl}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 px-4 py-2 font-medium text-white transition-colors dark:bg-blue-700 dark:hover:bg-blue-600"
              aria-label="Get new video URL"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Get New Link</span>
            </button>
          )}

          {/* Reload Page Button */}
          {!onRetry && !onRequestNewUrl && (
            <button
              onClick={() => location.reload()}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 hover:bg-red-700 px-4 py-2 font-medium text-white transition-colors dark:bg-red-700 dark:hover:bg-red-600"
              aria-label="Reload page"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Reload Page</span>
            </button>
          )}
        </div>

        {/* Help Section */}
        <div className="w-full border-t border-red-200 pt-4 dark:border-red-800">
          <p className="mb-2 text-xs font-medium text-red-800 dark:text-red-300">
            Still having issues?
          </p>
          <ul className="space-y-1 text-xs text-red-700 dark:text-red-400">
            <li>
              • Check your internet connection and try again
            </li>
            <li>
              • Try refreshing the page to get a new video link
            </li>
            <li>
              • Try a different browser or clear your cache
            </li>
            <li>
              • If the problem persists,{" "}
              <a
                href="mailto:support@example.com"
                className="font-medium underline hover:no-underline"
              >
                contact support
              </a>
            </li>
          </ul>
        </div>

        {/* Error Code Display */}
        <div className="rounded bg-black/5 px-3 py-2 font-mono text-xs text-red-600 dark:bg-black/30 dark:text-red-400">
          Error Code: {error.code}
        </div>
      </div>
    );
  }
);

VideoError.displayName = "VideoError";

/**
 * Get human-readable error title based on error code
 */
function getErrorTitle(code: string): string {
  const titles: Record<string, string> = {
    UNSUPPORTED_FORMAT: "Unsupported Video Format",
    NETWORK_ERROR: "Network Connection Error",
    DECODE_ERROR: "Video Playback Error",
    URL_EXPIRED: "Video Link Expired",
    NOT_FOUND: "Video Not Found",
    UNKNOWN: "Playback Error",
  };

  return titles[code] ?? "Playback Error";
}
