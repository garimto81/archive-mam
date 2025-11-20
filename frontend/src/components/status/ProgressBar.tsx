"use client";

/**
 * Progress Bar Component
 *
 * Visual progress indicator for analysis status
 * Reference: MediaFlow progress bar patterns
 */

import React from "react";
import { cn } from "@/lib/utils";

/**
 * Progress bar variant types
 */
export type ProgressBarVariant = "completed" | "processing" | "failed" | "default";

export interface ProgressBarProps {
  /** Progress value (0-100) */
  readonly value: number;

  /** Maximum value (default 100) */
  readonly max?: number;

  /** Visual variant based on status */
  readonly variant?: ProgressBarVariant;

  /** Show percentage label */
  readonly showLabel?: boolean;

  /** Label position */
  readonly labelPosition?: "inside" | "outside" | "none";

  /** Size variant */
  readonly size?: "sm" | "md" | "lg";

  /** Custom CSS class name */
  className?: string;

  /** Animated progress (for processing state) */
  animated?: boolean;
}

/**
 * Get progress bar color classes based on variant
 */
function getVariantColor(variant: ProgressBarVariant): string {
  switch (variant) {
    case "completed":
      return "bg-green-500 dark:bg-green-400";
    case "processing":
      return "bg-blue-500 dark:bg-blue-400";
    case "failed":
      return "bg-red-500 dark:bg-red-400";
    case "default":
    default:
      return "bg-gray-500 dark:bg-gray-400";
  }
}

/**
 * Get progress bar size classes
 */
function getSizeClass(size: "sm" | "md" | "lg"): string {
  switch (size) {
    case "sm":
      return "h-1";
    case "md":
      return "h-2";
    case "lg":
      return "h-3";
    default:
      return "h-2";
  }
}

/**
 * ProgressBar Component
 *
 * Displays analysis progress with smooth animations and accessibility support.
 *
 * Features:
 * - Configurable value range (0-max)
 * - Status-based color variants
 * - Smooth transition animations
 * - Optional percentage label
 * - Size variants (sm, md, lg)
 * - Pulse animation for processing state
 * - Full accessibility (ARIA attributes)
 *
 * @example
 * ```tsx
 * // Basic progress
 * <ProgressBar value={45} variant="processing" />
 *
 * // With label
 * <ProgressBar value={75} variant="completed" showLabel />
 *
 * // Animated processing
 * <ProgressBar value={30} variant="processing" animated showLabel />
 *
 * // Small size
 * <ProgressBar value={60} size="sm" />
 * ```
 */
export function ProgressBar({
  value,
  max = 100,
  variant = "default",
  showLabel = false,
  labelPosition = "outside",
  size = "md",
  className,
  animated = false,
}: ProgressBarProps) {
  // Clamp value between 0 and max
  const clampedValue = Math.min(Math.max(value, 0), max);
  const percentage = Math.round((clampedValue / max) * 100);

  const colorClasses = getVariantColor(variant);
  const sizeClass = getSizeClass(size);

  const progressBar = (
    <div
      className={cn(
        "relative w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden",
        sizeClass,
        className
      )}
      role="progressbar"
      aria-valuenow={clampedValue}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={`Progress: ${percentage}%`}
    >
      {/* Progress fill */}
      <div
        className={cn(
          "h-full rounded-full transition-all duration-300 ease-out",
          colorClasses,
          animated && variant === "processing" && "animate-pulse"
        )}
        style={{ width: `${percentage}%` }}
      >
        {/* Inside label */}
        {showLabel && labelPosition === "inside" && percentage > 15 && (
          <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-white">
            {percentage}%
          </span>
        )}
      </div>

      {/* Indeterminate animation stripe (optional for unknown progress) */}
      {animated && variant === "processing" && percentage === 0 && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
      )}
    </div>
  );

  // Wrap with outside label if needed
  if (showLabel && labelPosition === "outside") {
    return (
      <div className="flex items-center gap-2">
        {progressBar}
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
          {percentage}%
        </span>
      </div>
    );
  }

  return progressBar;
}

/**
 * Progress Bar Variants for specific use cases
 */

export function CompletedProgressBar({
  value,
  showLabel = true,
  className,
}: {
  value: number;
  showLabel?: boolean;
  className?: string;
}) {
  return (
    <ProgressBar
      value={value}
      variant="completed"
      showLabel={showLabel}
      className={className}
    />
  );
}

export function ProcessingProgressBar({
  value,
  showLabel = true,
  animated = true,
  className,
}: {
  value: number;
  showLabel?: boolean;
  animated?: boolean;
  className?: string;
}) {
  return (
    <ProgressBar
      value={value}
      variant="processing"
      showLabel={showLabel}
      animated={animated}
      className={className}
    />
  );
}

export function FailedProgressBar({
  value,
  showLabel = false,
  className,
}: {
  value: number;
  showLabel?: boolean;
  className?: string;
}) {
  return (
    <ProgressBar
      value={value}
      variant="failed"
      showLabel={showLabel}
      className={className}
    />
  );
}

/**
 * Circular Progress variant (optional)
 */
export function CircularProgress({
  value,
  max = 100,
  size = 48,
  strokeWidth = 4,
  variant = "processing",
  showLabel = true,
  className,
}: {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  variant?: ProgressBarVariant;
  showLabel?: boolean;
  className?: string;
}) {
  const percentage = Math.round((Math.min(value, max) / max) * 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  const colorClasses = getVariantColor(variant);
  const strokeColor = colorClasses.includes("green")
    ? "#22c55e"
    : colorClasses.includes("blue")
    ? "#3b82f6"
    : colorClasses.includes("red")
    ? "#ef4444"
    : "#6b7280";

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-300 ease-out"
        />
      </svg>
      {showLabel && (
        <span className="absolute text-xs font-semibold text-gray-700 dark:text-gray-300">
          {percentage}%
        </span>
      )}
    </div>
  );
}

export default ProgressBar;
