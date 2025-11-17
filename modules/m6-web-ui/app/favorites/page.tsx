/**
 * Favorites Page
 * Display user's favorite poker hands
 */

'use client';

import * as React from 'react';
import { HandCard } from '@/components/HandCard';
import { Button } from '@/components/ui/button';
import { bffApi } from '@/lib/api-client';
import { FavoritesResponse, HandSummary } from '@/lib/types';
import { Loader2, Heart, AlertCircle } from 'lucide-react';

export default function FavoritesPage() {
  const [favorites, setFavorites] = React.useState<HandSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Fetch favorites
  React.useEffect(() => {
    const fetchFavorites = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = (await bffApi.favorites.list()) as FavoritesResponse;
        setFavorites(response.favorites || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load favorites');
      } finally {
        setLoading(false);
      }
    };

    fetchFavorites();
  }, []);

  // Handle favorite toggle
  const handleFavoriteToggle = async (handId: string, isFavorite: boolean) => {
    try {
      if (isFavorite) {
        await bffApi.favorites.add(handId);
        // Refresh list
        const response = (await bffApi.favorites.list()) as FavoritesResponse;
        setFavorites(response.favorites || []);
      } else {
        await bffApi.favorites.remove(handId);
        // Remove from local state
        setFavorites((prev) => prev.filter((h) => h.hand_id !== handId));
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
      throw error;
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Loading favorites...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="flex items-center justify-center py-12">
          <div className="text-center max-w-md">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to Load Favorites</h3>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => window.location.reload()}>Try Again</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Heart className="h-8 w-8" />
          My Favorites
        </h1>
        <p className="text-muted-foreground">
          {favorites.length} hand{favorites.length !== 1 ? 's' : ''} saved
        </p>
      </div>

      {/* Empty state */}
      {favorites.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center max-w-md">
            <Heart className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No favorites yet</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Start exploring and save your favorite poker hands
            </p>
            <Button onClick={() => (window.location.href = '/search')}>Start Searching</Button>
          </div>
        </div>
      )}

      {/* Favorites grid */}
      {favorites.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {favorites.map((hand) => (
            <HandCard key={hand.hand_id} hand={hand} onFavoriteToggle={handleFavoriteToggle} />
          ))}
        </div>
      )}
    </div>
  );
}
