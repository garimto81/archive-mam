"use client";

import React, { useState, useEffect } from "react";
import { FilterSection } from "./FilterSection";
import { ActiveFilters } from "./ActiveFilters";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { countActiveFilters } from "@/lib/filters/utils";
import type { SearchFilters } from "@/types/search";
import { X, ChevronDown, Filter } from "lucide-react";

/**
 * Props for FilterPanel component
 */
interface FilterPanelProps {
  /** Current filter state */
  filters: SearchFilters;

  /** Callback when filters change */
  onFiltersChange: (filters: SearchFilters) => void;

  /** Callback to clear all filters */
  onClearFilters: () => void;

  /** Disable filter interactions */
  disabled?: boolean;

  /** Display variant: sidebar (desktop) or drawer (mobile) */
  variant?: "sidebar" | "drawer" | "inline";

  /** Custom CSS class name */
  className?: string;
}

/**
 * Filter Panel Component
 *
 * Main container for search filters with responsive design.
 * Displays as a sticky sidebar on desktop (≥768px) or collapsible drawer on mobile (<768px).
 *
 * Features:
 * - Responsive layout (sidebar on desktop, drawer on mobile)
 * - Active filter count badge
 * - Clear all filters button
 * - Collapsible filter sections
 * - Active filter chips display
 * - Smooth transitions and animations
 *
 * @example
 * ```tsx
 * <FilterPanel
 *   filters={filters}
 *   onFiltersChange={setFilters}
 *   onClearFilters={() => setFilters({})}
 *   variant="sidebar"
 * />
 * ```
 */
export function FilterPanel({
  filters,
  onFiltersChange,
  onClearFilters,
  disabled = false,
  variant = "sidebar",
  className
}: FilterPanelProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const activeCount = countActiveFilters(filters);

  // Detect mobile breakpoint
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Auto-close drawer on filter change (mobile)
  const handleFiltersChange = (newFilters: SearchFilters) => {
    onFiltersChange(newFilters);
    // Keep drawer open for continued filtering
    // setIsDrawerOpen(false);
  };

  // Content shared between sidebar and drawer
  const filterContent = (
    <div className="space-y-6">
      {/* Active Filters Display */}
      {activeCount > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Active Filters ({activeCount})</h3>
            <button
              onClick={onClearFilters}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
              disabled={disabled}
            >
              Clear All
            </button>
          </div>
          <ActiveFilters
            filters={filters}
            onRemoveFilter={(key) => {
              const newFilters = { ...filters };
              delete newFilters[key];
              handleFiltersChange(newFilters);
            }}
            onClearAll={onClearFilters}
          />
        </div>
      )}

      {/* Pot Size Filter */}
      <FilterSection
        title="Pot Size (BB)"
        defaultOpen={true}
        badge={filters.potSizeMin || filters.potSizeMax ? 1 : undefined}
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Minimum</label>
            <input
              type="number"
              placeholder="0"
              value={filters.potSizeMin ?? ""}
              onChange={(e) =>
                handleFiltersChange({
                  ...filters,
                  potSizeMin: e.target.value ? Number(e.target.value) : undefined
                })
              }
              disabled={disabled}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Maximum</label>
            <input
              type="number"
              placeholder="No limit"
              value={filters.potSizeMax ?? ""}
              onChange={(e) =>
                handleFiltersChange({
                  ...filters,
                  potSizeMax: e.target.value ? Number(e.target.value) : undefined
                })
              }
              disabled={disabled}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </FilterSection>

      {/* Street Filter */}
      <FilterSection
        title="Street"
        defaultOpen={false}
        badge={filters.streetMin ? 1 : undefined}
      >
        <div className="space-y-2">
          {["PREFLOP", "FLOP", "TURN", "RIVER"].map((street) => (
            <label key={street} className="flex items-center gap-3">
              <input
                type="radio"
                name="street"
                value={street}
                checked={filters.streetMin === street}
                onChange={(e) =>
                  handleFiltersChange({
                    ...filters,
                    streetMin: e.target.checked ? (e.target.value as any) : undefined
                  })
                }
                disabled={disabled}
                className="w-4 h-4 cursor-pointer disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">{street}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Result Filter */}
      <FilterSection
        title="Result"
        defaultOpen={false}
        badge={filters.resultFilter ? filters.resultFilter.length : undefined}
      >
        <div className="space-y-2">
          {["WIN", "LOSE", "SPLIT"].map((result) => (
            <label key={result} className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={filters.resultFilter?.includes(result as any) ?? false}
                onChange={(e) => {
                  const current = filters.resultFilter ?? [];
                  const newResults = e.target.checked
                    ? [...current, result as any]
                    : current.filter((r) => r !== result);
                  handleFiltersChange({
                    ...filters,
                    resultFilter: newResults.length > 0 ? newResults : undefined
                  });
                }}
                disabled={disabled}
                className="w-4 h-4 cursor-pointer disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">{result}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Tags Filter */}
      <FilterSection
        title="Tags"
        defaultOpen={false}
        badge={filters.tags ? filters.tags.length : undefined}
      >
        <div className="space-y-2">
          {[
            "HERO_CALL",
            "BLUFF",
            "VALUE_BET",
            "RIVER_DECISION",
            "TURN_DECISION",
            "FLOP_DECISION",
            "HIGH_STAKES",
            "ALL_IN",
            "SLOW_PLAY",
            "CHECK_RAISE"
          ].map((tag) => (
            <label key={tag} className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={filters.tags?.includes(tag) ?? false}
                onChange={(e) => {
                  const current = filters.tags ?? [];
                  const newTags = e.target.checked
                    ? [...current, tag]
                    : current.filter((t) => t !== tag);
                  handleFiltersChange({
                    ...filters,
                    tags: newTags.length > 0 ? newTags : undefined
                  });
                }}
                disabled={disabled}
                className="w-4 h-4 cursor-pointer disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">{tag}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Tournament Filter */}
      <FilterSection
        title="Tournament"
        defaultOpen={false}
        badge={filters.tournament ? filters.tournament.length : undefined}
      >
        <input
          type="text"
          placeholder="Enter tournament ID"
          defaultValue={filters.tournament?.join(", ") ?? ""}
          onChange={(e) => {
            const tournaments = e.target.value
              .split(",")
              .map((t) => t.trim())
              .filter(Boolean);
            handleFiltersChange({
              ...filters,
              tournament: tournaments.length > 0 ? tournaments : undefined
            });
          }}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
      </FilterSection>

      {/* Position Filter */}
      <FilterSection
        title="Position"
        defaultOpen={false}
        badge={filters.position ? filters.position.length : undefined}
      >
        <div className="space-y-2">
          {["BTN", "SB", "BB", "UTG", "MP", "CO"].map((pos) => (
            <label key={pos} className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={filters.position?.includes(pos) ?? false}
                onChange={(e) => {
                  const current = filters.position ?? [];
                  const newPositions = e.target.checked
                    ? [...current, pos]
                    : current.filter((p) => p !== pos);
                  handleFiltersChange({
                    ...filters,
                    position: newPositions.length > 0 ? newPositions : undefined
                  });
                }}
                disabled={disabled}
                className="w-4 h-4 cursor-pointer disabled:cursor-not-allowed"
              />
              <span className="text-sm text-gray-700">{pos}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {/* Hero Name Filter */}
      <FilterSection
        title="Hero Name"
        defaultOpen={false}
        badge={filters.heroName ? 1 : undefined}
      >
        <input
          type="text"
          placeholder="Enter hero name"
          value={filters.heroName ?? ""}
          onChange={(e) =>
            handleFiltersChange({
              ...filters,
              heroName: e.target.value || undefined
            })
          }
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
      </FilterSection>

      {/* Date Range Filter */}
      <FilterSection
        title="Date Range"
        defaultOpen={false}
        badge={filters.dateFrom || filters.dateTo ? 1 : undefined}
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">From</label>
            <input
              type="date"
              value={filters.dateFrom ?? ""}
              onChange={(e) =>
                handleFiltersChange({
                  ...filters,
                  dateFrom: e.target.value || undefined
                })
              }
              disabled={disabled}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">To</label>
            <input
              type="date"
              value={filters.dateTo ?? ""}
              onChange={(e) =>
                handleFiltersChange({
                  ...filters,
                  dateTo: e.target.value || undefined
                })
              }
              disabled={disabled}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </FilterSection>
    </div>
  );

  // Mobile drawer variant
  if (isMobile || variant === "drawer") {
    return (
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <SheetTrigger asChild>
          <button className={cn(
            "relative inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors",
            className
          )}>
            <Filter className="w-4 h-4" />
            Filters
            {activeCount > 0 && (
              <Badge variant="secondary" className="ml-2">
                {activeCount}
              </Badge>
            )}
          </button>
        </SheetTrigger>
        <SheetContent side="left" className="w-full max-w-sm overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Filters</SheetTitle>
          </SheetHeader>
          <div className="mt-6">
            {filterContent}
          </div>
        </SheetContent>
      </Sheet>
    );
  }

  // Desktop sidebar variant
  return (
    <div className={cn(
      "hidden md:block w-full max-w-xs",
      className
    )}>
      <div className="sticky top-24 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="flex items-center gap-2 font-semibold text-gray-900 hover:text-gray-700"
          >
            <span>Filters</span>
            {activeCount > 0 && (
              <Badge variant="secondary">{activeCount}</Badge>
            )}
            <ChevronDown className={cn(
              "w-4 h-4 transition-transform",
              isCollapsed && "transform rotate-180"
            )} />
          </button>
          {activeCount > 0 && (
            <button
              onClick={onClearFilters}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={disabled}
            >
              Clear
            </button>
          )}
        </div>

        {/* Divider */}
        <div className="h-px bg-gray-200" />

        {/* Filter Content */}
        {!isCollapsed && (
          <div className="transition-all duration-200 ease-out">
            {filterContent}
          </div>
        )}
      </div>
    </div>
  );
}
