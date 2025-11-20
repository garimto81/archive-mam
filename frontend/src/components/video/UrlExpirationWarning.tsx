/**
 * Video URL Expiration Warning Component
 *
 * @description
 * Visual warning when video URL is expiring soon.
 * Displays countdown timer and optional refresh button.
 *
 * @author Claude Code
 * @version 1.0.0
 */

import React, { useState, useEffect } from "react";
import { AlertTriangle, RefreshCw, X } from "lucide-react";
import { formatTimeRemaining } from "@/lib/video/url-validator";

/**
 * Props for UrlExpirationWarning component
 */
export interface UrlExpirationWarningProps {
  /** Seconds until URL expires */
  readonly timeUntilExpiration: number;

  /** Callback when refresh button is clicked */
  readonly onRefresh: () => void;

  /** Callback to dismiss warning */
  readonly onDismiss?: () => void;

  /** Whether auto-refresh is enabled (shows different message) */
  readonly autoRefresh?: boolean;

  /** Threshold in seconds (default: 300 = 5 minutes) */
  readonly thresholdSeconds?: number;

  /** Custom CSS class for styling */
  readonly className?: string;

  /** Whether refresh is in progress */
  readonly isRefreshing?: boolean;
}

/**
 * Warning banner for video URL expiration
 *
 * Shows when video URL has less than 5 minutes remaining.
 * Displays countdown timer and manual refresh button.
 *
 * @example
 * ```typescript
 * function VideoPlayer() {
 *   const { videoMetadata, timeUntilExpiration, refresh } = useVideoUrl({ handId });
 *
 *   if (timeUntilExpiration && timeUntilExpiration < 300) {
 *     return (
 *       <>
 *         <UrlExpirationWarning
 *           timeUntilExpiration={timeUntilExpiration}
 *           onRefresh={refresh}
 *         />
 *         <video src={videoMetadata?.videoUrl} />
 *       </>
 *     );
 *   }
 *
 *   return <video src={videoMetadata?.videoUrl} />;
 * }
 * ```
 */
export function UrlExpirationWarning({
  timeUntilExpiration,
  onRefresh,
  onDismiss,
  autoRefresh = false,
  thresholdSeconds = 300,
  className = "",
  isRefreshing = false
}: UrlExpirationWarningProps): React.ReactElement | null {
  const [displayTime, setDisplayTime] = useState(timeUntilExpiration);
  const [isDismissed, setIsDismissed] = useState(false);

  // Update display time every second
  useEffect(() => {
    setDisplayTime(timeUntilExpiration);
  }, [timeUntilExpiration]);

  // Auto-update countdown
  useEffect(() => {
    if (displayTime <= 0 || isDismissed) return;

    const timer = setInterval(() => {
      setDisplayTime(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [displayTime, isDismissed]);

  // Don't show if dismissed or not expiring soon
  if (isDismissed || timeUntilExpiration >= thresholdSeconds) {
    return null;
  }

  // Determine warning level based on time remaining
  const isUrgent = timeUntilExpiration < 60; // Less than 1 minute
  const bgColor = isUrgent ? "bg-red-50" : "bg-yellow-50";
  const borderColor = isUrgent ? "border-red-200" : "border-yellow-200";
  const textColor = isUrgent ? "text-red-800" : "text-yellow-800";
  const iconColor = isUrgent ? "text-red-500" : "text-yellow-500";
  const buttonColor = isUrgent
    ? "bg-red-100 hover:bg-red-200 text-red-900"
    : "bg-yellow-100 hover:bg-yellow-200 text-yellow-900";

  const handleRefresh = () => {
    onRefresh();
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  return (
    <div
      className={`${bgColor} ${borderColor} border rounded-md p-4 flex items-start gap-3 ${className}`}
      role="alert"
      aria-live="polite"
      aria-label="URL expiration warning"
    >
      {/* Icon */}
      <div className="flex-shrink-0 mt-0.5">
        <AlertTriangle className={`w-5 h-5 ${iconColor}`} aria-hidden="true" />
      </div>

      {/* Content */}
      <div className="flex-grow">
        <div className={`font-medium ${textColor}`}>
          {isUrgent ? "Video URL expiring urgently" : "Video URL expires soon"}
        </div>
        <div className={`text-sm mt-1 ${textColor} opacity-90`}>
          {autoRefresh ? (
            <>
              URL will auto-refresh in{" "}
              <span className="font-semibold">
                {formatTimeRemaining(displayTime)}
              </span>
            </>
          ) : (
            <>
              URL expires in{" "}
              <span className="font-semibold">
                {formatTimeRemaining(displayTime)}
              </span>
              . Refresh to extend availability.
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex-shrink-0 flex gap-2">
        {!autoRefresh && (
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`${buttonColor} px-3 py-1 rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1`}
            aria-label="Refresh video URL"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
            Refresh
          </button>
        )}

        <button
          onClick={handleDismiss}
          className={`${buttonColor} px-2 py-1 rounded transition-colors`}
          aria-label="Dismiss warning"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

/**
 * Props for UrlExpirationWarningContainer component
 */
export interface UrlExpirationWarningContainerProps {
  /** Seconds until URL expires */
  readonly timeUntilExpiration: number | null;

  /** Callback when refresh button is clicked */
  readonly onRefresh: () => void;

  /** Whether auto-refresh is enabled */
  readonly autoRefresh?: boolean;

  /** Threshold in seconds */
  readonly thresholdSeconds?: number;

  /** Whether refresh is in progress */
  readonly isRefreshing?: boolean;

  /** Custom CSS class */
  readonly className?: string;
}

/**
 * Container component that automatically shows/hides warning
 *
 * Handles the case where timeUntilExpiration might be null.
 *
 * @example
 * ```typescript
 * <UrlExpirationWarningContainer
 *   timeUntilExpiration={timeRemaining}
 *   onRefresh={() => refresh()}
 *   autoRefresh={true}
 * />
 * ```
 */
export function UrlExpirationWarningContainer({
  timeUntilExpiration,
  onRefresh,
  autoRefresh = false,
  thresholdSeconds = 300,
  isRefreshing = false,
  className = ""
}: UrlExpirationWarningContainerProps): React.ReactElement | null {
  // Don't show if no time info available or if time is sufficient
  if (
    timeUntilExpiration === null ||
    timeUntilExpiration >= thresholdSeconds ||
    timeUntilExpiration <= 0
  ) {
    return null;
  }

  return (
    <UrlExpirationWarning
      timeUntilExpiration={timeUntilExpiration}
      onRefresh={onRefresh}
      autoRefresh={autoRefresh}
      thresholdSeconds={thresholdSeconds}
      isRefreshing={isRefreshing}
      className={className}
    />
  );
}
