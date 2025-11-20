"use client";

/**
 * Status Badge Component
 *
 * Displays analysis status with icon and color coding
 * Reference: MediaFlow status tracking patterns
 */

import React from "react";
import { CheckCircle, Loader2, Clock, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Analysis status types
 */
export type AnalysisStatus = "completed" | "processing" | "pending" | "failed";

export interface StatusBadgeProps {
  /** Analysis status */
  readonly status: AnalysisStatus;

  /** Progress percentage (0-100) for processing status */
  readonly progress?: number;

  /** Error message for failed status */
  readonly error?: string;

  /** Custom CSS class name */
  className?: string;

  /** Show label text */
  showLabel?: boolean;

  /** Compact mode (icon only) */
  compact?: boolean;
}

/**
 * Get icon component for status
 */
function getStatusIcon(status: AnalysisStatus) {
  switch (status) {
    case "completed":
      return CheckCircle;
    case "processing":
      return Loader2;
    case "pending":
      return Clock;
    case "failed":
      return XCircle;
    default:
      return Clock;
  }
}

/**
 * Get status color classes (WCAG 2.1 AA compliant)
 */
function getStatusColor(status: AnalysisStatus): string {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-800 border-green-200";
    case "processing":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "pending":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "failed":
      return "bg-red-100 text-red-800 border-red-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

/**
 * Get status label text (Korean)
 */
function getStatusLabel(status: AnalysisStatus, progress?: number): string {
  switch (status) {
    case "completed":
      return "완료";
    case "processing":
      return progress !== undefined ? `분석 중 ${progress}%` : "분석 중";
    case "pending":
      return "대기";
    case "failed":
      return "실패";
    default:
      return "불명";
  }
}

/**
 * StatusBadge Component
 *
 * Displays hand analysis status with appropriate icon and styling.
 *
 * Features:
 * - Color-coded status badges
 * - Icon representation
 * - Progress percentage for processing
 * - Error tooltip for failures
 * - Accessibility support (aria-label, role)
 * - Compact mode for grid layouts
 *
 * @example
 * ```tsx
 * <StatusBadge status="completed" />
 * <StatusBadge status="processing" progress={45} />
 * <StatusBadge status="failed" error="Analysis timeout" />
 * ```
 */
export function StatusBadge({
  status,
  progress,
  error,
  className,
  showLabel = true,
  compact = false,
}: StatusBadgeProps) {
  const Icon = getStatusIcon(status);
  const colorClasses = getStatusColor(status);
  const label = getStatusLabel(status, progress);

  // Determine aria-label based on status (Korean)
  const getAriaLabel = (): string => {
    switch (status) {
      case "completed":
        return "분석 완료";
      case "processing":
        return "분석 진행 중";
      case "pending":
        return "분석 대기 중";
      case "failed":
        return "분석 실패";
      default:
        return "상태 불명";
    }
  };

  const badge = (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-xs font-medium transition-colors",
        colorClasses,
        compact && "px-1.5 py-0.5",
        className
      )}
      role="status"
      aria-label={getAriaLabel()}
      title={status === "failed" && error ? error : undefined}
      tabIndex={status === "failed" && error ? 0 : undefined}
    >
      <Icon
        className={cn(
          "w-3.5 h-3.5 flex-shrink-0",
          status === "processing" && "animate-spin"
        )}
        aria-hidden="true"
      />
      {showLabel && !compact && <span>{label}</span>}
    </div>
  );

  // Wrap with tooltip if error exists
  if (error && status === "failed") {
    return (
      <div className="group relative inline-block">
        {badge}
        <div className="absolute z-10 invisible group-hover:visible bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded shadow-lg whitespace-nowrap pointer-events-none">
          <div className="font-semibold mb-1">Error:</div>
          <div className="text-gray-300">{error}</div>
          {/* Tooltip arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-800"></div>
        </div>
      </div>
    );
  }

  return badge;
}

/**
 * Status Badge Variants for specific use cases
 */

export function CompletedBadge({ className }: { className?: string }) {
  return <StatusBadge status="completed" className={className} />;
}

export function ProcessingBadge({
  progress,
  className,
}: {
  progress?: number;
  className?: string;
}) {
  return (
    <StatusBadge
      status="processing"
      progress={progress}
      className={className}
    />
  );
}

export function PendingBadge({ className }: { className?: string }) {
  return <StatusBadge status="pending" className={className} />;
}

export function FailedBadge({
  error,
  className,
}: {
  error?: string;
  className?: string;
}) {
  return <StatusBadge status="failed" error={error} className={className} />;
}

export default StatusBadge;
