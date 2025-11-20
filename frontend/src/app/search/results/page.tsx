"use client";

import { useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { cn } from "@/lib/utils";
import type { SearchFilters } from "@/types/search";
import type { Street, HandResult } from "@/types/hand";
import { FeatureErrorBoundary } from "@/components/ErrorBoundary";
import {
  safeGetParam,
  safeGetAllParams,
  validateSearchQuery,
  validatePlayerName,
  validateTag,
  validateTournamentId,
  validateDateString,
  validateNumber,
} from "@/lib/validation/input";

/**
 * Parse filters from URL search parameters
 *
 * Converts URL query parameters into SearchFilters object.
 * Handles arrays (tags, tournaments, etc) and numeric ranges.
 *
 * @param searchParams - Next.js SearchParams object
 * @returns Parsed SearchFilters object
 *
 * @example
 * // URL: /search/results?q=bluff&tag=BLUFF&tag=RIVER&potMin=100&potMax=500
 * const filters = parseFiltersFromUrl(searchParams);
 * // Returns: { tags: ["BLUFF", "RIVER"], potSizeMin: 100, potSizeMax: 500 }
 */
function parseFiltersFromUrl(searchParams: URLSearchParams): SearchFilters | undefined {
  const filters: Partial<SearchFilters> = {};
  let hasFilters = false;

  // Pot size range (validated as positive numbers)
  const potMin = safeGetParam(searchParams, "potMin", (v) =>
    validateNumber(v, { min: 0, max: 10000 })
  );
  if (potMin !== null) {
    filters.potSizeMin = potMin;
    hasFilters = true;
  }

  const potMax = safeGetParam(searchParams, "potMax", (v) =>
    validateNumber(v, { min: 0, max: 10000 })
  );
  if (potMax !== null) {
    filters.potSizeMax = potMax;
    hasFilters = true;
  }

  // Tags (validated uppercase + underscore only)
  const tags = safeGetAllParams(searchParams, "tag", validateTag);
  if (tags.length > 0) {
    filters.tags = tags as readonly string[];
    hasFilters = true;
  }

  // Tournament IDs (validated alphanumeric)
  const tournaments = safeGetAllParams(searchParams, "tournament", validateTournamentId);
  if (tournaments.length > 0) {
    filters.tournament = tournaments as readonly string[];
    hasFilters = true;
  }

  // Position (validated from allowed list)
  const positions = safeGetAllParams(searchParams, "position", (v) => {
    const validPositions = ["BTN", "CO", "MP", "EP", "SB", "BB"];
    if (!validPositions.includes(v)) {
      throw new Error("Invalid position");
    }
    return v;
  });
  if (positions.length > 0) {
    filters.position = positions as readonly string[];
    hasFilters = true;
  }

  // Street minimum (validated from enum)
  const streetMin = safeGetParam(searchParams, "streetMin", (v) => {
    const validStreets: Street[] = ["PREFLOP", "FLOP", "TURN", "RIVER"];
    if (!validStreets.includes(v as Street)) {
      throw new Error("Invalid street");
    }
    return v as Street;
  });
  if (streetMin !== null) {
    filters.streetMin = streetMin;
    hasFilters = true;
  }

  // Result filter (validated from enum)
  const results = safeGetAllParams(searchParams, "result", (v) => {
    const validResults: HandResult[] = ["WIN", "LOSS", "CHOP"];
    if (!validResults.includes(v as HandResult)) {
      throw new Error("Invalid result");
    }
    return v as HandResult;
  });
  if (results.length > 0) {
    filters.resultFilter = results as readonly HandResult[];
    hasFilters = true;
  }

  // Hero name (validated player name format)
  const heroName = safeGetParam(searchParams, "heroName", validatePlayerName);
  if (heroName !== null) {
    filters.heroName = heroName;
    hasFilters = true;
  }

  // Villain name (validated player name format)
  const villainName = safeGetParam(searchParams, "villainName", validatePlayerName);
  if (villainName !== null) {
    filters.villainName = villainName;
    hasFilters = true;
  }

  // Date range (validated ISO 8601 format)
  const dateFrom = safeGetParam(searchParams, "dateFrom", validateDateString);
  if (dateFrom !== null) {
    filters.dateFrom = dateFrom;
    hasFilters = true;
  }

  const dateTo = safeGetParam(searchParams, "dateTo", validateDateString);
  if (dateTo !== null) {
    filters.dateTo = dateTo;
    hasFilters = true;
  }

  return hasFilters ? filters : undefined;
}

/**
 * Search Results Page
 *
 * Main search results display page with filters and pagination.
 * Handles URL-based search state for shareable results.
 *
 * Features:
 * - URL-based search state (shareable results)
 * - Query parameter parsing for filters
 * - Search bar for new queries
 * - Results grid with pagination
 * - Responsive layout
 * - Back navigation
 *
 * @route /search/results?q={query}&tag={tag}&potMin={min}&potMax={max}
 *
 * @example URL patterns:
 * - /search/results?q=river+bluff
 * - /search/results?q=river+bluff&tag=BLUFF&tag=HERO_CALL&potMin=100&potMax=500
 * - /search/results?q=phil+ivey&tournament=WSOP_2024_MAIN
 */
export default function SearchResultsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Validate and sanitize search query from URL
  const rawQuery = searchParams.get("q") || "";
  const query = safeGetParam(searchParams, "q", validateSearchQuery) || "";
  const filters = parseFiltersFromUrl(searchParams);

  /**
   * Handle new search submission
   */
  const handleSearch = useCallback((newQuery: string) => {
    // Navigate to results page with new query
    const params = new URLSearchParams();
    params.set("q", newQuery);

    // Preserve current filters (optional - can be reset instead)
    if (filters) {
      if (filters.potSizeMin) params.set("potMin", filters.potSizeMin.toString());
      if (filters.potSizeMax) params.set("potMax", filters.potSizeMax.toString());
      if (filters.tags) filters.tags.forEach(tag => params.append("tag", tag));
      if (filters.tournament) filters.tournament.forEach(t => params.append("tournament", t));
      if (filters.position) filters.position.forEach(p => params.append("position", p));
      if (filters.streetMin) params.set("streetMin", filters.streetMin);
      if (filters.resultFilter) filters.resultFilter.forEach(r => params.append("result", r));
      if (filters.heroName) params.set("heroName", filters.heroName);
      if (filters.villainName) params.set("villainName", filters.villainName);
      if (filters.dateFrom) params.set("dateFrom", filters.dateFrom);
      if (filters.dateTo) params.set("dateTo", filters.dateTo);
    }

    router.push(`/search/results?${params.toString()}`);
  }, [filters, router]);

  /**
   * Handle hand click navigation
   */
  const handleHandClick = useCallback((handId: string) => {
    router.push(`/hands/${handId}`);
  }, [router]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Header Section */}
      <div className="container mx-auto px-4 py-8 sticky top-0 z-40 bg-background/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-6xl mx-auto">
          {/* Title */}
          <h1 className="text-2xl md:text-3xl font-bold mb-6 text-foreground">
            Search Results
          </h1>

          {/* Search Bar */}
          <div className="mb-4">
            <SearchBar
              initialQuery={query}
              onSearch={handleSearch}
              enableAutocomplete={true}
              placeholder="Search poker hands, players, tags..."
            />
          </div>

          {/* Current Query Display */}
          {query && (
            <div className="text-sm text-muted-foreground">
              Searching for: <span className="font-semibold text-foreground">"{query}"</span>
            </div>
          )}
        </div>
      </div>

      {/* Results Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {query ? (
            <FeatureErrorBoundary featureName="Search Results">
              <SearchResults
                query={query}
                filters={filters}
                onHandClick={handleHandClick}
              />
            </FeatureErrorBoundary>
          ) : (
            // Empty state when no query
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold text-foreground mb-3">
                No search query provided
              </h2>
              <p className="text-muted-foreground mb-6">
                Use the search bar above to find poker hands, players, and strategies.
              </p>
              <button
                onClick={() => router.push("/search")}
                className={cn(
                  "px-6 py-2 rounded-lg",
                  "bg-poker-chip-green hover:bg-poker-chip-green/90",
                  "text-white font-semibold",
                  "transition-colors duration-200"
                )}
              >
                Back to Search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-auto border-t border-border">
        <div className="max-w-6xl mx-auto text-center text-sm text-muted-foreground">
          <p>
            Powered by Vertex AI Vector Search • Built with Next.js 15 & TypeScript
          </p>
        </div>
      </footer>
    </main>
  );
}
