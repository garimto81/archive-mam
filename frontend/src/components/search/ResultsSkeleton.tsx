"use client";

import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface ResultsSkeletonProps {
  /** Number of skeleton cards to display (default: 9) */
  count?: number;
  /** Custom CSS class */
  className?: string;
}

/**
 * Results Loading Skeleton Component
 *
 * Displays placeholder skeleton cards while search results are loading.
 * Animated shimmer effect with layout matching HandCard dimensions.
 *
 * Features:
 * - Responsive grid (1/2/3 columns based on screen size)
 * - Animated pulse effect
 * - Accessible (aria-busy)
 * - Matches HandCard layout exactly
 *
 * @example
 * ```tsx
 * {isLoading ? (
 *   <ResultsSkeleton count={9} />
 * ) : (
 *   <ResultsGrid results={results} />
 * )}
 * ```
 */
export function ResultsSkeleton({
  count = 9,
  className
}: ResultsSkeletonProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3",
        className
      )}
      role="status"
      aria-busy="true"
      aria-label="Loading results"
    >
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={`skeleton-${i}`} />
      ))}
    </div>
  );
}

/**
 * Individual Skeleton Card Component
 *
 * Matches the layout of HandCard with placeholder elements.
 */
function SkeletonCard() {
  return (
    <div
      className={cn(
        "rounded-lg border border-input bg-card overflow-hidden",
        "transition-all hover:shadow-md animate-pulse"
      )}
    >
      {/* Thumbnail Skeleton */}
      <div className="relative w-full aspect-video bg-accent rounded-t-lg">
        <Skeleton className="w-full h-full rounded-none" />

        {/* Video Badge Overlay */}
        <div className="absolute top-2 left-2">
          <Skeleton className="w-8 h-6 rounded" />
        </div>

        {/* Relevance Score Badge */}
        <div className="absolute top-2 right-2">
          <Skeleton className="w-12 h-6 rounded" />
        </div>
      </div>

      {/* Content Container */}
      <div className="p-4 space-y-3">
        {/* Hero vs Villain */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-8" />
          </div>
          <div className="flex items-center justify-between gap-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-8" />
          </div>
        </div>

        {/* Divider */}
        <div className="border-b border-input" />

        {/* Metadata Row */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
          </div>
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 pt-2">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-14 rounded-full" />
        </div>
      </div>
    </div>
  );
}

export type { ResultsSkeletonProps };
