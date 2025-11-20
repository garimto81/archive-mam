"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { HandCard } from "./HandCard";
import type { SearchResultItem } from "@/types/search";

interface ResultsGridProps {
  /** Array of search result items to display */
  results: readonly SearchResultItem[];

  /** Callback when a hand is clicked */
  onHandClick?: (handId: string) => void;

  /** Whether grid is in loading state */
  isLoading?: boolean;

  /** Custom CSS class name */
  className?: string;
}

/**
 * Results Grid Component
 *
 * Displays search results in a responsive CSS grid layout.
 * Grid columns adjust based on viewport:
 * - Mobile (sm): 1 column
 * - Tablet (md): 2 columns
 * - Desktop (lg): 3 columns
 * - Large screens (xl): 3 columns
 *
 * Features:
 * - Responsive grid layout
 * - Smooth animations
 * - Hand cards with thumbnails and metadata
 * - Click handlers for navigation
 * - Loading states
 * - Empty state handling
 *
 * @example
 * ```tsx
 * <ResultsGrid
 *   results={searchResults}
 *   onHandClick={(handId) => router.push(`/hands/${handId}`)}
 * />
 * ```
 */
export function ResultsGrid({
  results,
  onHandClick,
  isLoading = false,
  className
}: ResultsGridProps) {
  return (
    <div
      className={cn(
        "w-full",
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
        "gap-6",
        "animate-fadeIn",
        className
      )}
      role="grid"
      aria-label={`${results.length} search results`}
      aria-busy={isLoading}
    >
      {results.map((result, index) => (
        <div
          key={result.handId}
          role="gridcell"
          className="animate-slideUp"
          style={{
            animationDelay: `${index * 50}ms`
          }}
        >
          <HandCard
            result={result}
            onClick={() => onHandClick?.(result.handId)}
          />
        </div>
      ))}
    </div>
  );
}
