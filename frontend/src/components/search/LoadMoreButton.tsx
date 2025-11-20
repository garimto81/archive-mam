"use client";

import React from "react";
import { Loader2, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface LoadMoreButtonProps {
  /** Callback when user clicks to load more results */
  onClick: () => void;
  /** Whether results are currently loading */
  loading?: boolean;
  /** Disable the button */
  disabled?: boolean;
  /** Number of additional results available */
  remainingCount?: number;
  /** Custom text to display (e.g., "Load more") */
  text?: string;
  /** Custom CSS class */
  className?: string;
}

/**
 * Load More Button Component
 *
 * Manual pagination button for loading additional results.
 * Useful for infinite scroll fallback or manual load patterns.
 *
 * Features:
 * - Loading spinner animation
 * - Shows remaining result count
 * - Disabled during load
 * - Keyboard accessible
 * - Accessible loading state announcement
 *
 * @example
 * ```tsx
 * <LoadMoreButton
 *   onClick={() => setPage(p => p + 1)}
 *   loading={isLoading}
 *   remainingCount={remaining}
 *   disabled={!hasMore}
 * />
 * ```
 */
export function LoadMoreButton({
  onClick,
  loading = false,
  disabled = false,
  remainingCount,
  text = "Load More",
  className
}: LoadMoreButtonProps) {
  return (
    <div className="flex justify-center py-8">
      <Button
        onClick={onClick}
        disabled={disabled || loading}
        variant="outline"
        size="lg"
        className={cn(
          "gap-2 transition-all duration-200",
          loading && "opacity-75",
          className
        )}
        aria-label={
          loading
            ? "Loading more results"
            : remainingCount
            ? `${text} (${remainingCount} remaining)`
            : text
        }
        aria-busy={loading}
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            <span>Loading...</span>
          </>
        ) : (
          <>
            <span>
              {text}
              {remainingCount && ` (${remainingCount} remaining)`}
            </span>
            <ChevronDown className="w-4 h-4" aria-hidden="true" />
          </>
        )}
      </Button>

      {/* Screen reader announcement */}
      <span className="sr-only" role="status" aria-live="polite">
        {loading ? "Loading more results..." : ""}
      </span>
    </div>
  );
}

export type { LoadMoreButtonProps };
