"use client";

import React, { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PaginationMeta } from "@/types/search";
import { cn } from "@/lib/utils";

interface PaginationProps {
  /** Pagination metadata from search response */
  meta: PaginationMeta;
  /** Callback when user clicks a page number */
  onPageChange: (page: number) => void;
  /** Callback to load next page */
  onNextPage: () => void;
  /** Callback to load previous page */
  onPrevPage: () => void;
  /** Disable pagination controls */
  disabled?: boolean;
  /** Custom CSS class */
  className?: string;
}

/**
 * Pagination Controls Component
 *
 * Displays pagination controls for search results with:
 * - Previous/Next buttons
 * - Page number selection (max 5 visible)
 * - Results count indicator
 * - Full keyboard and screen reader accessibility
 *
 * @example
 * ```tsx
 * const [currentPage, setCurrentPage] = useState(1);
 * const { data: results } = useFetchSearch(query, currentPage);
 *
 * <Pagination
 *   meta={results.pagination}
 *   onPageChange={setCurrentPage}
 *   onNextPage={() => setCurrentPage(p => p + 1)}
 *   onPrevPage={() => setCurrentPage(p => p - 1)}
 * />
 * ```
 */
export function Pagination({
  meta,
  onPageChange,
  onNextPage,
  onPrevPage,
  disabled = false,
  className
}: PaginationProps) {
  // Calculate which page numbers to display
  // Show max 5 page numbers: 1 2 3 4 5, or ... patterns
  const pageNumbers = useMemo(() => {
    const maxDisplay = 5;
    const pages: (number | string)[] = [];

    if (meta.totalPages <= maxDisplay) {
      // Show all pages if less than max
      for (let i = 1; i <= meta.totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show: 1, 2, ..., current-1, current, current+1, ..., last-1, last
      const current = meta.currentPage;
      const total = meta.totalPages;

      pages.push(1);

      if (current > 3) {
        pages.push("...");
      }

      const start = Math.max(2, current - 1);
      const end = Math.min(total - 1, current + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (current < total - 2) {
        pages.push("...");
      }

      pages.push(total);
    }

    return pages;
  }, [meta.currentPage, meta.totalPages]);

  // Calculate result range display
  const startResult = (meta.currentPage - 1) * meta.pageSize + 1;
  const endResult = Math.min(meta.currentPage * meta.pageSize, meta.totalResults);

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-center justify-between gap-4 py-6 px-4 rounded-lg border bg-card",
        "sm:gap-6 sm:py-8",
        disabled && "opacity-50 pointer-events-none",
        className
      )}
      role="navigation"
      aria-label="Pagination Navigation"
    >
      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        Showing <span className="font-semibold text-foreground">{startResult}</span>
        {" "}to{" "}
        <span className="font-semibold text-foreground">{endResult}</span>
        {" "}of{" "}
        <span className="font-semibold text-foreground">{meta.totalResults}</span>
        {" "}results
      </div>

      {/* Page Navigation */}
      <div className="flex items-center gap-2">
        {/* Previous Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={onPrevPage}
          disabled={disabled || !meta.hasPrev}
          aria-label="Previous page"
          title="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline ml-1">Previous</span>
        </Button>

        {/* Page Numbers */}
        <div
          className="flex items-center gap-1"
          role="group"
          aria-label="Page selection"
        >
          {pageNumbers.map((page, index) => (
            <React.Fragment key={`page-${index}`}>
              {page === "..." ? (
                <span
                  className="px-2 py-1 text-muted-foreground"
                  aria-hidden="true"
                >
                  ...
                </span>
              ) : (
                <Button
                  variant={page === meta.currentPage ? "default" : "outline"}
                  size="sm"
                  onClick={() => onPageChange(page as number)}
                  disabled={disabled || page === meta.currentPage}
                  className={cn(
                    "min-w-10 h-10",
                    page === meta.currentPage &&
                      "pointer-events-none bg-primary text-primary-foreground"
                  )}
                  aria-label={`Go to page ${page}`}
                  aria-current={page === meta.currentPage ? "page" : undefined}
                >
                  {page}
                </Button>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Next Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={onNextPage}
          disabled={disabled || !meta.hasNext}
          aria-label="Next page"
          title="Next page"
        >
          <span className="hidden sm:inline mr-1">Next</span>
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Page Info */}
      <div className="text-sm text-muted-foreground hidden md:block">
        Page <span className="font-semibold text-foreground">{meta.currentPage}</span>
        {" "}of{" "}
        <span className="font-semibold text-foreground">{meta.totalPages}</span>
      </div>
    </div>
  );
}

export type { PaginationProps };
