"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { SearchMetadata } from "./SearchMetadata";
import { ResultsGrid } from "./ResultsGrid";
import { ErrorDisplay } from "./ErrorDisplay";
import { ResultsSkeleton } from "./ResultsSkeleton";
import { EmptyState } from "./EmptyState";
import { Pagination } from "./Pagination";
import { ArchiveTreeView } from "@/components/archive/ArchiveTreeView";
import { cn } from "@/lib/utils";
import { fetchSearch } from "@/lib/api/search";
import { generateMockSearchResponse } from "@/lib/mock/mockData";
import { searchHandsByFilters } from "@/lib/api/firestore";
import { adaptFirestoreHandToSearchResult } from "@/lib/adapters/firestoreAdapter";
import type { SearchResponse, SearchFilters } from "@/types/search";
import type { AutocompleteError } from "@/types";
import type { FirestoreHand } from "@/types/firestore";

// Use mock data when Firestore is not configured
// Set NEXT_PUBLIC_ENABLE_MOCK_DATA=false in .env.local when Firebase is configured
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_ENABLE_MOCK_DATA === "true";

/**
 * Convert Firestore hands to SearchResponse format
 *
 * @param hands - Array of Firestore hands
 * @param query - Original search query
 * @param filters - Applied filters
 * @param page - Current page number
 * @param pageSize - Results per page
 * @returns SearchResponse formatted for display
 */
function convertFirestoreToSearchResponse(
  hands: FirestoreHand[],
  query: string,
  filters: SearchFilters | undefined,
  page: number,
  pageSize: number = 20
): SearchResponse {
  const startTime = Date.now();

  // Convert each hand to SearchResultItem
  const results = hands.map((hand) => adaptFirestoreHandToSearchResult(hand));

  const endTime = Date.now();
  const total = hands.length;
  const totalPages = Math.ceil(total / pageSize);

  return {
    results,
    total,
    query,
    filters,
    pagination: {
      currentPage: page,
      totalPages: totalPages || 1,
      pageSize,
      totalResults: total,
      hasNext: page < totalPages,
      hasPrev: page > 1,
    },
    queryTimeMs: endTime - startTime,
    source: "bigquery", // Firestore data originally from BigQuery ETL
  };
}

interface SearchResultsProps {
  /** Natural language search query */
  query: string;

  /** Optional search filters */
  filters?: SearchFilters;

  /** Initial results (for SSR or server component data) */
  initialResults?: SearchResponse;

  /** Callback when a hand is clicked */
  onHandClick?: (handId: string) => void;

  /** Custom CSS class name */
  className?: string;
}

/**
 * Search Results Container Component
 *
 * Manages search state, fetches results, handles pagination,
 * and displays results in a responsive grid.
 *
 * Features:
 * - Automatic search execution
 * - Loading states with skeleton UI
 * - Error handling with retry
 * - Pagination with page navigation
 * - Request cancellation on unmount
 * - Search metadata display
 * - Empty state handling
 * - Responsive layout
 *
 * @example
 * ```tsx
 * <SearchResults
 *   query="river bluff"
 *   filters={{ potSizeMin: 100, tags: ["BLUFF"] }}
 *   onHandClick={(handId) => router.push(`/hands/${handId}`)}
 * />
 * ```
 */
export function SearchResults({
  query,
  filters,
  initialResults,
  onHandClick,
  className
}: SearchResultsProps) {
  // State management
  const [results, setResults] = useState<SearchResponse | null>(initialResults ?? null);
  const [isLoading, setIsLoading] = useState(!initialResults && !!query);
  const [error, setError] = useState<AutocompleteError | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Refs for cleanup
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Fetch search results
   */
  const executeSearch = useCallback(async (page: number = 1) => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    if (!query.trim()) {
      setResults(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let response: SearchResponse;

      if (USE_MOCK_DATA) {
        // Use mock data for development/testing
        response = await new Promise<SearchResponse>((resolve) => {
          setTimeout(() => {
            const mockResponse = generateMockSearchResponse(query, 20, (page - 1) * 20);
            resolve(mockResponse);
          }, 300);
        });
      } else {
        // Use Firestore for production data
        try {
          const firestoreHands = await searchHandsByFilters(filters || {});
          response = convertFirestoreToSearchResponse(
            firestoreHands,
            query,
            filters,
            page,
            20
          );
        } catch (firestoreError) {
          // Fallback to API search if Firestore fails
          console.warn('[SearchResults] Firestore search failed, falling back to API:', firestoreError);
          response = await fetchSearch(query, filters, {
            signal: controller.signal,
            enableCache: true,
            timeout: 10000,
          });
        }
      }

      // Only update if not cancelled
      if (!controller.signal.aborted) {
        setResults(response);
        setCurrentPage(page);
        setError(null);
      }
    } catch (err) {
      // Don't show error if request was cancelled
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }

      // Handle different error types
      const error = err as Error;
      let errorType: "network" | "timeout" | "validation" = "network";
      let errorMsg = error.message || "Failed to fetch search results";

      if (error.message.includes("timeout")) {
        errorType = "timeout";
        errorMsg = "Search request timed out. Please try again.";
      } else if (error.message.includes("validation")) {
        errorType = "validation";
        errorMsg = "Invalid search query or filters.";
      }

      setError({
        error: errorType,
        message: errorMsg,
        query: query
      });
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  }, [query, filters]);

  /**
   * Execute search on mount or when query changes
   */
  useEffect(() => {
    executeSearch(1);

    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [query, filters, executeSearch]);

  /**
   * Handle pagination
   */
  const handlePageChange = useCallback((newPage: number) => {
    executeSearch(newPage);
    // Scroll to top of results
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [executeSearch]);

  /**
   * Handle retry
   */
  const handleRetry = useCallback(() => {
    executeSearch(currentPage);
  }, [currentPage, executeSearch]);

  // Loading state
  if (isLoading && !results) {
    return (
      <div className={cn("w-full", className)}>
        <ResultsSkeleton count={20} />
      </div>
    );
  }

  // Error state
  if (error && !results) {
    return (
      <div className={cn("w-full", className)}>
        <ErrorDisplay error={error} onRetry={handleRetry} />
      </div>
    );
  }

  // No results state
  if (!results || results.results.length === 0) {
    return (
      <div className={cn("w-full", className)}>
        <EmptyState
          query={query}
          hasActiveFilters={!!filters && Object.keys(filters).length > 0}
        />
      </div>
    );
  }

  // Results state
  return (
    <div className={cn("w-full space-y-4", className)}>
      {/* Metadata section */}
      <SearchMetadata
        total={results.total}
        queryTimeMs={results.queryTimeMs}
        source={results.source}
        filters={results.filters}
      />

      {/* Main content: 3-column layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left sidebar: Archive tree */}
        <aside className="col-span-12 lg:col-span-3">
          <div className="sticky top-4">
            <ArchiveTreeView
              results={results.results}
              onHandSelect={(hand) => onHandClick?.(hand.handId)}
              showSearch={true}
              showControls={true}
              className="max-h-[calc(100vh-8rem)]"
            />
          </div>
        </aside>

        {/* Center: Results grid */}
        <main className="col-span-12 lg:col-span-9">
          <ResultsGrid
            results={results.results}
            onHandClick={onHandClick}
            isLoading={isLoading}
          />

          {/* Pagination */}
          {results.pagination && results.pagination.totalPages > 1 && (
            <div className="flex justify-center mt-12">
              <Pagination
                meta={results.pagination}
                onPageChange={handlePageChange}
                onNextPage={() => handlePageChange(Math.min(currentPage + 1, results.pagination.totalPages))}
                onPrevPage={() => handlePageChange(Math.max(currentPage - 1, 1))}
                disabled={isLoading}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
