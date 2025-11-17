/**
 * Search Results Page
 * Display search results with filters and pagination
 */

'use client';

import * as React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { SearchBar } from '@/components/SearchBar';
import { HandCard } from '@/components/HandCard';
import { Button } from '@/components/ui/button';
import { bffApi } from '@/lib/api-client';
import { SearchResponse, HandSummary, SearchFilters } from '@/lib/types';
import { Loader2, AlertCircle } from 'lucide-react';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuery = searchParams.get('q') || '';

  const [query, setQuery] = React.useState(initialQuery);
  const [results, setResults] = React.useState<HandSummary[]>([]);
  const [totalResults, setTotalResults] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [filters, setFilters] = React.useState<SearchFilters>({});

  // Execute search
  const executeSearch = React.useCallback(async (searchQuery: string, searchFilters: SearchFilters = {}) => {
    if (searchQuery.trim().length < 2) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = (await bffApi.search.search({
        query: searchQuery,
        limit: 20,
        filters: searchFilters,
        include_proxy: true,
      })) as SearchResponse;

      setResults(response.results || []);
      setTotalResults(response.total_results || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  }, []);

  // Search on mount if query exists
  React.useEffect(() => {
    if (initialQuery) {
      executeSearch(initialQuery, filters);
    }
  }, [initialQuery, filters, executeSearch]);

  // Handle new search
  const handleSearch = (newQuery: string) => {
    setQuery(newQuery);
    router.push(`/search?q=${encodeURIComponent(newQuery)}`);
    executeSearch(newQuery, filters);
  };

  // Handle favorite toggle
  const handleFavoriteToggle = async (handId: string, isFavorite: boolean) => {
    try {
      if (isFavorite) {
        await bffApi.favorites.add(handId);
      } else {
        await bffApi.favorites.remove(handId);
      }

      // Update local state
      setResults(prev =>
        prev.map(hand =>
          hand.hand_id === handId ? { ...hand, is_favorite: isFavorite } : hand
        )
      );
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      throw error;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Search bar */}
      <div className="mb-8">
        <SearchBar onSearch={handleSearch} defaultValue={query} />
      </div>

      {/* Results count */}
      {!loading && !error && totalResults > 0 && (
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">
            Found <span className="font-semibold text-foreground">{totalResults}</span> results
            {query && (
              <>
                {' '}
                for "<span className="font-semibold text-foreground">{query}</span>"
              </>
            )}
          </p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Searching...</span>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center max-w-md">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Search Failed</h3>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => executeSearch(query, filters)}>Try Again</Button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && totalResults === 0 && query && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center max-w-md">
            <h3 className="text-lg font-semibold mb-2">No results found</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Try different keywords or check your spelling
            </p>
          </div>
        </div>
      )}

      {/* Results grid */}
      {!loading && !error && results.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((hand) => (
            <HandCard
              key={hand.hand_id}
              hand={hand}
              onFavoriteToggle={handleFavoriteToggle}
              showRelevanceScore
            />
          ))}
        </div>
      )}

      {/* Pagination placeholder */}
      {!loading && !error && results.length > 0 && totalResults > results.length && (
        <div className="mt-8 flex justify-center">
          <Button variant="outline">Load More</Button>
        </div>
      )}
    </div>
  );
}
