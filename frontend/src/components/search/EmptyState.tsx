"use client";

import React from "react";
import { Search, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  /** The search query that returned no results */
  query: string;
  /** Suggestions for user (e.g., "Try different keywords") */
  suggestions?: string[];
  /** Whether any filters are active */
  hasActiveFilters?: boolean;
  /** Callback when user wants to clear filters */
  onClearFilters?: () => void;
  /** Callback when user clicks an example search */
  onExampleSearch?: (example: string) => void;
  /** Custom CSS class */
  className?: string;
}

/** Example searches to suggest to users */
const EXAMPLE_SEARCHES = [
  "river call bluff",
  "hero fold hero call",
  "high pot all-in",
  "final table heads up",
];

/**
 * Empty State Component
 *
 * Displays when no search results are found. Provides:
 * - Clear messaging about the search
 * - Suggestions for improving search
 * - Example searches to try
 * - Option to clear filters
 * - Helpful icons and visual hierarchy
 *
 * Features:
 * - Centered layout with max-width
 * - Accessible button interactions
 * - Keyboard navigable
 * - Responsive design
 *
 * @example
 * ```tsx
 * {results.length === 0 ? (
 *   <EmptyState
 *     query="some query"
 *     hasActiveFilters={filters.length > 0}
 *     onClearFilters={resetFilters}
 *     onExampleSearch={search}
 *   />
 * ) : (
 *   <ResultsGrid results={results} />
 * )}
 * ```
 */
export function EmptyState({
  query,
  suggestions,
  hasActiveFilters = false,
  onClearFilters,
  onExampleSearch,
  className
}: EmptyStateProps) {
  const defaultSuggestions = [
    "Try using different keywords",
    "Check your spelling or try synonyms",
    hasActiveFilters ? "Try removing some filters" : "Try adjusting your search criteria",
    "Try searching for well-known players or tournaments"
  ];

  const displaySuggestions = suggestions || defaultSuggestions;

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-4",
        "sm:py-16 sm:px-6",
        className
      )}
      role="status"
      aria-live="polite"
    >
      {/* Icon */}
      <div className="mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted">
          <Search className="w-8 h-8 text-muted-foreground" aria-hidden="true" />
        </div>
      </div>

      {/* Main Message */}
      <h2 className="text-2xl font-bold text-center text-foreground mb-2">
        No results found
      </h2>

      {/* Query Display */}
      <p className="text-base text-muted-foreground text-center mb-6">
        We couldn't find any poker hands matching{" "}
        <span className="inline-block font-semibold text-foreground">
          "{query}"
        </span>
      </p>

      {/* Suggestions Section */}
      <div className="w-full max-w-md mb-8">
        <div className="flex items-start gap-3 p-4 rounded-lg bg-card border border-input">
          <AlertCircle
            className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5"
            aria-hidden="true"
          />
          <div className="space-y-2">
            <p className="text-sm font-semibold text-foreground">
              Suggestions:
            </p>
            <ul className="space-y-1">
              {displaySuggestions.map((suggestion, i) => (
                <li
                  key={`suggestion-${i}`}
                  className="text-sm text-muted-foreground flex items-start gap-2"
                >
                  <span className="text-muted-foreground mt-0.5">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Clear Filters Button */}
      {hasActiveFilters && onClearFilters && (
        <Button
          onClick={onClearFilters}
          variant="outline"
          className="mb-8"
          aria-label="Clear all filters and try again"
        >
          Clear Filters and Try Again
        </Button>
      )}

      {/* Example Searches */}
      <div className="w-full max-w-md">
        <p className="text-sm font-semibold text-foreground text-center mb-4">
          Or try searching for:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {EXAMPLE_SEARCHES.map((example, i) => (
            <button
              key={`example-${i}`}
              onClick={() => onExampleSearch?.(example)}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium",
                "transition-all duration-200",
                "bg-secondary text-secondary-foreground",
                "hover:bg-secondary/80 hover:shadow-sm",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                "dark:hover:bg-secondary/60"
              )}
              type="button"
              aria-label={`Search for ${example}`}
            >
              <span className="truncate">{example}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Help Text */}
      <p className="text-xs text-muted-foreground text-center mt-8 max-w-sm">
        Need help? Try the <span className="font-semibold">keyboard shortcuts</span> (press{" "}
        <span className="inline-block px-1.5 py-0.5 rounded bg-muted text-foreground font-mono text-xs">?</span>
        ) or check out our search guide.
      </p>
    </div>
  );
}

export type { EmptyStateProps };
