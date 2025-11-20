"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { SearchFilters, SearchSource } from "@/types/search";

interface SearchMetadataProps {
  /** Total number of results found */
  total: number;

  /** Query execution time in milliseconds */
  queryTimeMs: number;

  /** Source system that provided results */
  source: SearchSource;

  /** Applied filters (if any) */
  filters?: SearchFilters;

  /** Custom CSS class name */
  className?: string;
}

/**
 * Search Metadata Component
 *
 * Displays search result metadata including:
 * - Total result count
 * - Query execution time
 * - Source system (Vertex AI, BigQuery, Hybrid)
 * - Applied filters as badges
 * - Relevance indicator
 *
 * Features:
 * - Color-coded source badges
 * - Filter visualization
 * - Performance metrics
 * - Responsive layout
 * - Accessibility support
 *
 * @example
 * ```tsx
 * <SearchMetadata
 *   total={47}
 *   queryTimeMs={78}
 *   source="vertex-ai"
 *   filters={{ potSizeMin: 100, tags: ["BLUFF"] }}
 * />
 * ```
 */
export function SearchMetadata({
  total,
  queryTimeMs,
  source,
  filters,
  className
}: SearchMetadataProps) {
  /**
   * Get source badge configuration
   */
  const getSourceConfig = (src: SearchSource | string) => {
    const configs: Record<string, { label: string; color: string; description: string }> = {
      "vertex-ai": {
        label: "Vector Search",
        color: "bg-poker-chip-purple/10 text-poker-chip-purple border-poker-chip-purple/20",
        description: "Powered by Vertex AI semantic search"
      },
      bigquery: {
        label: "Keyword Search",
        color: "bg-poker-chip-green/10 text-poker-chip-green border-poker-chip-green/20",
        description: "Powered by BigQuery full-text search"
      },
      hybrid: {
        label: "Hybrid Search",
        color: "bg-poker-chip-red/10 text-poker-chip-red border-poker-chip-red/20",
        description: "Combined vector and keyword search"
      },
      mock: {
        label: "Mock Data",
        color: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        description: "Using mock data for development"
      },
      unknown: {
        label: "Search",
        color: "bg-gray-500/10 text-gray-500 border-gray-500/20",
        description: "Search results"
      }
    };

    return src in configs ? configs[src] : configs.unknown;
  };

  const sourceConfig = getSourceConfig(source);

  /**
   * Extract filter labels for display
   */
  const filterLabels: string[] = [];

  if (filters) {
    if (filters.potSizeMin !== undefined || filters.potSizeMax !== undefined) {
      const min = filters.potSizeMin ?? 0;
      const max = filters.potSizeMax ?? "∞";
      filterLabels.push(`Pot: ${min}-${max}bb`);
    }

    if (filters.tags && filters.tags.length > 0) {
      filterLabels.push(`Tags: ${filters.tags.join(", ")}`);
    }

    if (filters.tournament && filters.tournament.length > 0) {
      filterLabels.push(`Tournament: ${filters.tournament.join(", ")}`);
    }

    if (filters.heroName) {
      filterLabels.push(`Hero: ${filters.heroName}`);
    }

    if (filters.villainName) {
      filterLabels.push(`Villain: ${filters.villainName}`);
    }

    if (filters.position && filters.position.length > 0) {
      filterLabels.push(`Position: ${filters.position.join(", ")}`);
    }

    if (filters.streetMin) {
      filterLabels.push(`From: ${filters.streetMin}`);
    }

    if (filters.resultFilter && filters.resultFilter.length > 0) {
      filterLabels.push(`Result: ${filters.resultFilter.join(", ")}`);
    }
  }

  /**
   * Format query time with appropriate unit
   */
  const formatQueryTime = (ms: number): string => {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div
      className={cn(
        "w-full space-y-4 px-4 py-6 rounded-lg",
        "bg-card border border-border",
        "animate-fadeIn",
        className
      )}
      role="region"
      aria-label="Search results information"
    >
      {/* Primary metadata row */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Result count and query time */}
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">
            Found{" "}
            <span className="text-poker-chip-green font-bold">
              {total.toLocaleString()}
            </span>
            {total === 1 ? " result" : " results"}
          </h2>
          <p className="text-sm text-muted-foreground">
            Query time: <span className="font-mono font-semibold">{formatQueryTime(queryTimeMs)}</span>
          </p>
        </div>

        {/* Source badge */}
        <Badge
          className={cn(
            "h-fit border",
            sourceConfig.color
          )}
          title={sourceConfig.description}
        >
          {sourceConfig.label}
        </Badge>
      </div>

      {/* Applied filters section */}
      {filterLabels.length > 0 && (
        <div className="pt-4 border-t border-border">
          <p className="text-xs font-semibold text-muted-foreground mb-3">
            Applied Filters
          </p>
          <div className="flex flex-wrap gap-2">
            {filterLabels.map((label, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="text-xs font-normal"
              >
                {label}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Performance indicator */}
      <div className="pt-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          {queryTimeMs < 100 && "⚡ Instant results"}
          {queryTimeMs >= 100 && queryTimeMs < 500 && "✓ Fast results"}
          {queryTimeMs >= 500 && "○ Standard results"}
        </p>
      </div>
    </div>
  );
}
