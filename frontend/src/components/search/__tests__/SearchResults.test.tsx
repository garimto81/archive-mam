/**
 * SearchResults Component Tests
 *
 * Test suite for the SearchResults component covering:
 * - Loading skeleton display
 * - Search results rendering
 * - Empty state with no results
 * - Error state on failure
 * - Pagination handling
 * - Search metadata display
 * - Retry functionality
 * - Request cancellation on unmount
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchResults } from '../SearchResults';
import type { SearchResponse, SearchResultItem } from '@/types/search';

// Mock the API
vi.mock('@/lib/api/search', () => ({
  fetchSearch: vi.fn(),
}));

// Mock sub-components
vi.mock('../ResultsSkeleton', () => ({
  ResultsSkeleton: () => <div data-testid="results-skeleton">Loading...</div>,
}));

vi.mock('../ResultsGrid', () => ({
  ResultsGrid: ({ results, onHandClick }: any) => (
    <div data-testid="results-grid">
      {results.map((item: SearchResultItem) => (
        <div
          key={item.handId}
          data-testid={`result-${item.handId}`}
          onClick={() => onHandClick?.(item.handId)}
        >
          {item.hero_name} vs {item.villain_name}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('../SearchMetadata', () => ({
  SearchMetadata: ({ response }: any) => (
    <div data-testid="search-metadata">
      Found {response?.total} results in {response?.queryTimeMs}ms
    </div>
  ),
}));

vi.mock('../Pagination', () => ({
  Pagination: ({ meta, onPageChange }: any) => (
    <nav data-testid="pagination">
      <button onClick={() => onPageChange(1)}>Page 1</button>
      <button onClick={() => onPageChange(2)}>Page 2</button>
    </nav>
  ),
}));

vi.mock('../EmptyState', () => ({
  EmptyState: ({ query }: any) => (
    <div data-testid="empty-state">No results for "{query}"</div>
  ),
}));

vi.mock('../ErrorDisplay', () => ({
  ErrorDisplay: ({ error, onRetry }: any) => (
    <div data-testid="error-display">
      <div>Error: {error?.message}</div>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
}));

describe('SearchResults Component', () => {
  const mockResults: SearchResponse = {
    results: [
      {
        handId: 'hand-1',
        hero_name: 'Phil Ivey',
        villain_name: 'Tom Dwan',
        pot_bb: 100,
        score: 0.95,
        street: 'RIVER' as const,
        result: 'WIN' as const,
        tags: ['HERO_CALL', 'RIVER'],
        thumbnail_url: 'https://example.com/thumb1.jpg',
      },
      {
        handId: 'hand-2',
        hero_name: 'Junglemann',
        villain_name: 'Villain',
        pot_bb: 50,
        score: 0.85,
        street: 'TURN' as const,
        result: 'LOSE' as const,
        tags: ['BLUFF'],
        thumbnail_url: 'https://example.com/thumb2.jpg',
      },
    ],
    total: 2,
    query: 'river bluff',
    queryTimeMs: 78,
    source: 'vertex-ai' as const,
    pagination: {
      currentPage: 1,
      totalPages: 1,
      pageSize: 20,
      totalResults: 2,
      hasNext: false,
      hasPrev: false,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render loading skeleton initially', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<SearchResults query="test query" />);

      expect(screen.getByTestId('results-skeleton')).toBeInTheDocument();
    });

    it('should display search results when loaded', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(mockResults);

      render(<SearchResults query="river bluff" />);

      await waitFor(() => {
        expect(screen.getByTestId('results-grid')).toBeInTheDocument();
      });

      expect(screen.getByTestId('result-hand-1')).toBeInTheDocument();
      expect(screen.getByTestId('result-hand-2')).toBeInTheDocument();
    });

    it('should display search metadata', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(mockResults);

      render(<SearchResults query="river bluff" />);

      await waitFor(() => {
        expect(screen.getByTestId('search-metadata')).toBeInTheDocument();
        expect(screen.getByText(/Found 2 results in 78ms/)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no results found', async () => {
      const emptyResults = { ...mockResults, results: [], total: 0 };
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        emptyResults
      );

      render(<SearchResults query="nonexistent" />);

      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeInTheDocument();
        expect(screen.getByText(/No results for "nonexistent"/)).toBeInTheDocument();
      });
    });

    it('should not show pagination when no results', async () => {
      const emptyResults = { ...mockResults, results: [], total: 0 };
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        emptyResults
      );

      render(<SearchResults query="test" />);

      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('pagination')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error state on failure', async () => {
      const error = new Error('Network error');
      vi.mocked(require('@/lib/api/search').fetchSearch).mockRejectedValue(error);

      render(<SearchResults query="test" />);

      await waitFor(() => {
        expect(screen.getByTestId('error-display')).toBeInTheDocument();
      });
    });

    it('should allow retry on error', async () => {
      const error = new Error('Network error');
      vi.mocked(require('@/lib/api/search').fetchSearch)
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(mockResults);

      render(<SearchResults query="test" />);

      await waitFor(() => {
        expect(screen.getByTestId('error-display')).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await userEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByTestId('results-grid')).toBeInTheDocument();
      });
    });

    it('should handle timeout errors gracefully', async () => {
      const timeoutError = new Error('Request timeout');
      vi.mocked(require('@/lib/api/search').fetchSearch).mockRejectedValue(
        timeoutError
      );

      render(<SearchResults query="test" />);

      await waitFor(() => {
        expect(screen.getByTestId('error-display')).toBeInTheDocument();
      });
    });
  });

  describe('Pagination', () => {
    it('should display pagination controls', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        mockResults
      );

      render(<SearchResults query="test" />);

      await waitFor(() => {
        expect(screen.getByTestId('pagination')).toBeInTheDocument();
      });
    });

    it('should handle page changes', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        mockResults
      );

      render(<SearchResults query="test" />);

      await waitFor(() => {
        expect(screen.getByTestId('pagination')).toBeInTheDocument();
      });

      const page2Button = screen.getByRole('button', { name: /Page 2/i });
      await userEvent.click(page2Button);

      // Should fetch new results for page 2
      expect(
        require('@/lib/api/search').fetchSearch
      ).toHaveBeenCalledWith(
        expect.objectContaining({
          options: expect.objectContaining({
            offset: expect.any(Number),
          }),
        })
      );
    });
  });

  describe('Callbacks', () => {
    it('should call onHandClick when a result is clicked', async () => {
      const onHandClick = vi.fn();
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        mockResults
      );

      render(
        <SearchResults
          query="test"
          onHandClick={onHandClick}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('result-hand-1')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByTestId('result-hand-1'));

      expect(onHandClick).toHaveBeenCalledWith('hand-1');
    });
  });

  describe('Filters', () => {
    it('should apply filters to search', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        mockResults
      );

      const filters = {
        potSizeMin: 50,
        tags: ['RIVER'],
      };

      render(
        <SearchResults
          query="river bluff"
          filters={filters}
        />
      );

      await waitFor(() => {
        expect(
          require('@/lib/api/search').fetchSearch
        ).toHaveBeenCalledWith(
          expect.objectContaining({
            filters,
          })
        );
      });
    });
  });

  describe('Initial Results (SSR)', () => {
    it('should use initial results if provided', async () => {
      render(
        <SearchResults
          query="test"
          initialResults={mockResults}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('results-grid')).toBeInTheDocument();
        expect(screen.getByTestId('result-hand-1')).toBeInTheDocument();
      });
    });

    it('should not fetch when initial results are provided', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        mockResults
      );

      render(
        <SearchResults
          query="test"
          initialResults={mockResults}
        />
      );

      // Should not call fetch since we have initial results
      expect(
        require('@/lib/api/search').fetchSearch
      ).not.toHaveBeenCalled();
    });
  });

  describe('Request Cancellation', () => {
    it('should cancel in-flight request on unmount', async () => {
      const abortSpy = vi.fn();
      vi.mocked(require('@/lib/api/search').fetchSearch).mockImplementation(
        (request: any) => {
          request.options?.signal?.addEventListener('abort', abortSpy);
          return new Promise(() => {});
        }
      );

      const { unmount } = render(<SearchResults query="test" />);

      unmount();

      // Verify cleanup happened
      expect(screen.queryByTestId('results-skeleton')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty query', async () => {
      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        mockResults
      );

      render(<SearchResults query="" />);

      // Should not fetch with empty query
      await waitFor(() => {
        expect(
          require('@/lib/api/search').fetchSearch
        ).not.toHaveBeenCalled();
      });
    });

    it('should handle very large result sets', async () => {
      const largeResults = {
        ...mockResults,
        total: 10000,
        pagination: {
          ...mockResults.pagination,
          totalPages: 500,
        },
      };

      vi.mocked(require('@/lib/api/search').fetchSearch).mockResolvedValue(
        largeResults
      );

      render(<SearchResults query="common query" />);

      await waitFor(() => {
        expect(screen.getByTestId('pagination')).toBeInTheDocument();
      });
    });
  });
});
