/**
 * SearchBar Component
 * Autocomplete-enabled search input for poker hands
 *
 * Usage:
 * <SearchBar onSearch={(query) => handleSearch(query)} />
 */

'use client';

import * as React from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { bffApi } from '@/lib/api-client';
import { AutocompleteResponse } from '@/lib/types';
import { debounce } from '@/lib/utils';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  defaultValue?: string;
  autoFocus?: boolean;
}

export function SearchBar({
  onSearch,
  placeholder = 'Search poker hands... (e.g., "Tom Dwan bluff", "AA vs KK all-in")',
  defaultValue = '',
  autoFocus = false,
}: SearchBarProps) {
  const [query, setQuery] = React.useState(defaultValue);
  const [suggestions, setSuggestions] = React.useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  // Debounced autocomplete fetch
  const fetchSuggestions = React.useMemo(
    () =>
      debounce(async (q: string) => {
        if (q.length < 2) {
          setSuggestions([]);
          return;
        }

        setLoading(true);
        try {
          const data = await bffApi.search.autocomplete(q, 10);
          const response = data as AutocompleteResponse;
          setSuggestions(response.suggestions || []);
        } catch (error) {
          console.error('Autocomplete error:', error);
          setSuggestions([]);
        } finally {
          setLoading(false);
        }
      }, 300),
    []
  );

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    fetchSuggestions(value);
    setShowSuggestions(true);
  };

  // Handle search submit
  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (query.trim().length >= 2) {
      onSearch(query.trim());
      setShowSuggestions(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    onSearch(suggestion);
    setShowSuggestions(false);
  };

  // Close suggestions on outside click
  React.useEffect(() => {
    const handleClickOutside = () => setShowSuggestions(false);
    if (showSuggestions) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showSuggestions]);

  return (
    <div className="relative w-full max-w-3xl">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            value={query}
            onChange={handleChange}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className="pl-10 pr-24 h-12 text-base"
            aria-label="Search poker hands"
            aria-autocomplete="list"
            aria-controls="search-suggestions"
          />
          <Button
            type="submit"
            size="sm"
            className="absolute right-2 top-1/2 -translate-y-1/2"
            disabled={query.trim().length < 2}
          >
            Search
          </Button>
        </div>
      </form>

      {/* Autocomplete suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          id="search-suggestions"
          className="absolute z-50 mt-2 w-full rounded-md border bg-popover p-1 shadow-md"
          role="listbox"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full rounded-sm px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
              role="option"
              aria-selected={false}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Loading indicator */}
      {loading && showSuggestions && (
        <div className="absolute right-14 top-1/2 -translate-y-1/2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      )}
    </div>
  );
}
