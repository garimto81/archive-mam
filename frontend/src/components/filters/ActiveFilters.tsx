"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { formatFilterValue } from "@/lib/filters/utils";
import { X } from "lucide-react";
import type { SearchFilters } from "@/types/search";

/**
 * Props for ActiveFilters component
 */
interface ActiveFiltersProps {
  /** Current filters */
  filters: SearchFilters;

  /** Callback when removing individual filter */
  onRemoveFilter: (key: keyof SearchFilters) => void;

  /** Callback to clear all filters */
  onClearAll: () => void;

  /** Custom CSS class name */
  className?: string;
}

/**
 * Active Filters Display Component
 *
 * Shows active filters as removable chips/badges.
 * Displays human-readable filter values and allows individual removal.
 *
 * Features:
 * - Displays active filters as chips
 * - X icon to remove individual filters
 * - "Clear all" button
 * - Formatted filter values (e.g., "Pot: 100-500 BB")
 * - Responsive layout
 * - Keyboard accessible buttons
 *
 * @example
 * ```tsx
 * <ActiveFilters
 *   filters={{ potSizeMin: 100, potSizeMax: 500, tags: ["BLUFF"] }}
 *   onRemoveFilter={(key) => setFilters({ ...filters, [key]: undefined })}
 *   onClearAll={() => setFilters({})}
 * />
 * ```
 */
export function ActiveFilters({
  filters,
  onRemoveFilter,
  onClearAll,
  className
}: ActiveFiltersProps) {
  // Get active filter entries
  const activeFilterEntries = Object.entries(filters).filter(
    ([, value]) => value !== undefined && value !== null && value !== ""
  ) as [keyof SearchFilters, any][];

  // No active filters
  if (activeFilterEntries.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Filter Chips */}
      <div className="flex flex-wrap gap-2">
        {activeFilterEntries.map(([key, value]) => {
          const label = formatFilterValue(key, value);

          return (
            <div
              key={key}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-full group hover:bg-blue-100 transition-colors"
            >
              <span className="text-sm text-blue-700">{label}</span>
              <button
                onClick={() => onRemoveFilter(key)}
                className="inline-flex items-center justify-center w-4 h-4 rounded-full text-blue-500 hover:bg-blue-200 hover:text-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                title={`Remove ${label}`}
                aria-label={`Remove filter: ${label}`}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Clear All Button */}
      {activeFilterEntries.length > 1 && (
        <button
          onClick={onClearAll}
          className="text-xs text-gray-600 hover:text-gray-900 font-medium underline transition-colors"
        >
          Clear all ({activeFilterEntries.length})
        </button>
      )}
    </div>
  );
}
