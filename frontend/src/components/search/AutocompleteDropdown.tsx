"use client";

import React, { forwardRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SuggestionItem } from "./SuggestionItem";
import { SourceBadge } from "./SourceBadge";
import { KeyboardHints } from "./KeyboardHints";
import { ErrorDisplay } from "./ErrorDisplay";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Suggestion, AutocompleteSource, AutocompleteError } from "@/types";

interface AutocompleteDropdownProps {
  id: string;
  query: string;
  suggestions: Suggestion[];
  selectedIndex: number;
  onSelectSuggestion: (suggestion: Suggestion, index: number) => void;
  onMouseEnterItem: (index: number) => void;
  isLoading: boolean;
  error: AutocompleteError | null;
  source: AutocompleteSource;
  responseTimeMs: number;
}

/**
 * Autocomplete Dropdown Component
 *
 * Main dropdown container for autocomplete suggestions.
 * Handles loading states, errors, empty states, and suggestion display.
 *
 * Features:
 * - Smooth animations (Framer Motion)
 * - Loading skeletons
 * - Error handling with retry
 * - Empty state messaging
 * - Source attribution
 * - Keyboard hints
 * - Accessibility (ARIA, roles)
 *
 * @example
 * ```tsx
 * <AutocompleteDropdown
 *   id="autocomplete-dropdown"
 *   query="jung"
 *   suggestions={suggestions}
 *   selectedIndex={0}
 *   onSelectSuggestion={(suggestion) => handleSelect(suggestion)}
 *   onMouseEnterItem={(index) => setSelectedIndex(index)}
 *   isLoading={false}
 *   error={null}
 *   source="vertex_ai"
 *   responseTimeMs={45}
 * />
 * ```
 */
export const AutocompleteDropdown = forwardRef<HTMLDivElement, AutocompleteDropdownProps>(
  ({
    id,
    query,
    suggestions,
    selectedIndex,
    onSelectSuggestion,
    onMouseEnterItem,
    isLoading,
    error,
    source,
    responseTimeMs
  }, ref) => {
    // Error 표시
    if (error) {
      return (
        <motion.div
          ref={ref}
          id={id}
          initial={{ opacity: 0, y: -10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.95 }}
          transition={{ duration: 0.15 }}
          className="absolute top-full mt-2 w-full bg-popover border border-border rounded-lg shadow-lg z-50"
        >
          <ErrorDisplay error={error} />
        </motion.div>
      );
    }

    // Loading skeleton
    if (isLoading) {
      return (
        <motion.div
          ref={ref}
          id={id}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-full mt-2 w-full bg-popover border border-border rounded-lg shadow-lg z-50 p-2"
        >
          <div className="space-y-2" role="status" aria-label="Loading suggestions">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-3 px-3 py-2">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-4 w-full max-w-[200px]" />
              </div>
            ))}
          </div>
        </motion.div>
      );
    }

    // No results
    if (suggestions.length === 0) {
      return (
        <motion.div
          ref={ref}
          id={id}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-full mt-2 w-full bg-popover border border-border rounded-lg shadow-lg z-50 p-6 text-center"
        >
          <p className="text-sm text-muted-foreground">
            No suggestions found for &quot;<strong>{query}</strong>&quot;
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Try checking your spelling or using player names
          </p>
        </motion.div>
      );
    }

    // Suggestions list
    return (
      <motion.div
        ref={ref}
        id={id}
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.15 }}
        className="absolute top-full mt-2 w-full bg-popover border border-border rounded-lg shadow-lg z-50 overflow-hidden"
      >
        <ScrollArea className="max-h-[400px]">
          <div
            role="listbox"
            aria-label="Search suggestions"
            className="p-2 space-y-1"
          >
            {suggestions.map((suggestion, index) => (
              <SuggestionItem
                key={index}
                id={`suggestion-${index}`}
                suggestion={suggestion}
                query={query}
                isSelected={index === selectedIndex}
                onClick={() => onSelectSuggestion(suggestion, index)}
                onMouseEnter={() => onMouseEnterItem(index)}
              />
            ))}
          </div>
        </ScrollArea>

        <div className="border-t border-border p-2 flex items-center justify-between">
          <SourceBadge source={source} responseTimeMs={responseTimeMs} />
          <KeyboardHints />
        </div>
      </motion.div>
    );
  }
);

AutocompleteDropdown.displayName = "AutocompleteDropdown";
