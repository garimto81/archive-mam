"use client";

import React, { useState, useRef, useCallback } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { AutocompleteDropdown } from "./AutocompleteDropdown";
import { useAutocomplete, useKeyboardNavigation, useClickOutside } from "@/hooks";
import { cn } from "@/lib/utils";
import { validateSearchQuery, ValidationError } from "@/lib/validation/input";

interface SearchBarProps {
  initialQuery?: string;
  onSearch?: (query: string) => void;
  enableAutocomplete?: boolean;
  placeholder?: string;
  className?: string;
}

/**
 * Main Search Bar Component
 *
 * Complete search bar with autocomplete functionality.
 * Integrates all search features including suggestions, keyboard navigation,
 * and accessibility.
 *
 * Features:
 * - Real-time autocomplete suggestions
 * - Keyboard navigation (↑↓ to navigate, Enter to select, Esc to close)
 * - Click outside to close dropdown
 * - Loading states
 * - Clear button
 * - Touch-friendly interface
 * - Full ARIA support
 *
 * @example
 * ```tsx
 * <SearchBar
 *   initialQuery=""
 *   onSearch={(query) => router.push(`/search?q=${query}`)}
 *   enableAutocomplete={true}
 *   placeholder="Search poker hands, players, tags..."
 * />
 * ```
 */
export function SearchBar({
  initialQuery = "",
  onSearch,
  enableAutocomplete = true,
  placeholder = "Search poker hands, players, tags...",
  className
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Autocomplete hook
  const {
    suggestions,
    isLoading,
    error,
    source,
    responseTimeMs
  } = useAutocomplete(query, { enabled: enableAutocomplete });

  // Keyboard navigation
  const {
    selectedIndex,
    setSelectedIndex,
    handleKeyDown: handleKeyboardNavigation
  } = useKeyboardNavigation({
    items: suggestions,
    onSelect: (suggestion) => {
      setQuery(suggestion.text);
      setIsDropdownOpen(false);
      if (onSearch) {
        onSearch(suggestion.text);
      }
    },
    onClose: () => setIsDropdownOpen(false)
  });

  // Click outside to close
  useClickOutside(dropdownRef, () => setIsDropdownOpen(false));

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const rawQuery = e.target.value;

    try {
      // Validate and sanitize user input
      const validatedQuery = validateSearchQuery(rawQuery);
      setQuery(validatedQuery);

      if (validatedQuery.length >= 2 && enableAutocomplete) {
        setIsDropdownOpen(true);
      } else {
        setIsDropdownOpen(false);
      }

      setSelectedIndex(-1);
    } catch (error) {
      if (error instanceof ValidationError) {
        // Log validation error but continue with raw input (UX decision)
        // Could also show error toast to user
        console.warn('[Search] Validation error:', error.message);
        setQuery(rawQuery.slice(0, 500)); // Truncate to max length
        setIsDropdownOpen(false);
      }
    }
  }, [enableAutocomplete, setSelectedIndex]);

  const handleInputFocus = useCallback(() => {
    if (query.length >= 2 && suggestions.length > 0 && enableAutocomplete) {
      setIsDropdownOpen(true);
    }
  }, [query, suggestions, enableAutocomplete]);

  const handleClear = useCallback(() => {
    setQuery("");
    setIsDropdownOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  }, [setSelectedIndex]);

  const handleSearchSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();

    if (selectedIndex >= 0 && suggestions[selectedIndex]) {
      onSearch?.(suggestions[selectedIndex].text);
    } else if (query.trim()) {
      onSearch?.(query);
    }

    setIsDropdownOpen(false);
  }, [query, selectedIndex, suggestions, onSearch]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    handleKeyboardNavigation(e);

    if (e.key === "Enter" && !isDropdownOpen) {
      handleSearchSubmit(e as any);
    }
  }, [handleKeyboardNavigation, handleSearchSubmit, isDropdownOpen]);

  return (
    <div className={cn("relative w-full max-w-2xl mx-auto", className)} data-testid="search-container">
      <form onSubmit={handleSearchSubmit} role="search">
        <div className="relative">
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />

          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            data-testid="search-input"
            className={cn(
              "pl-12 pr-12 h-12 text-base rounded-lg",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            )}
            aria-label="Search poker hands, players, and tags"
            aria-autocomplete="list"
            aria-controls={isDropdownOpen ? "autocomplete-dropdown" : undefined}
            aria-expanded={isDropdownOpen}
            aria-activedescendant={
              selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined
            }
            autoComplete="off"
            spellCheck={false}
          />

          {isLoading && (
            <Loader2
              className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-muted-foreground"
              aria-label="Loading suggestions"
            />
          )}

          {!isLoading && query && (
            <button
              type="button"
              onClick={handleClear}
              className={cn(
                "absolute right-4 top-1/2 -translate-y-1/2",
                "w-6 h-6 flex items-center justify-center",
                "rounded-full hover:bg-muted transition-colors"
              )}
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="sr-only" role="status" aria-live="polite" aria-atomic="true">
          {isLoading && "Loading suggestions..."}
          {!isLoading && suggestions.length > 0 && `${suggestions.length} suggestions found`}
        </div>
      </form>

      {isDropdownOpen && enableAutocomplete && (
        <AutocompleteDropdown
          ref={dropdownRef}
          id="autocomplete-dropdown"
          query={query}
          suggestions={suggestions}
          selectedIndex={selectedIndex}
          onSelectSuggestion={(suggestion, index) => {
            setQuery(suggestion.text);
            setIsDropdownOpen(false);
            onSearch?.(suggestion.text);
          }}
          onMouseEnterItem={setSelectedIndex}
          isLoading={isLoading}
          error={error}
          source={source}
          responseTimeMs={responseTimeMs}
        />
      )}
    </div>
  );
}
