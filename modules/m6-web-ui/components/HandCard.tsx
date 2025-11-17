/**
 * HandCard Component
 * Displays a poker hand search result with preview and metadata
 *
 * Usage:
 * <HandCard hand={handSummary} onFavoriteToggle={toggleFavorite} />
 */

'use client';

import * as React from 'react';
import Link from 'next/link';
import { Heart, Play, Users, DollarSign, Calendar } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { HandSummary } from '@/lib/types';
import { formatCurrency, truncate } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface HandCardProps {
  hand: HandSummary;
  onFavoriteToggle?: (handId: string, isFavorite: boolean) => void;
  showRelevanceScore?: boolean;
}

export function HandCard({ hand, onFavoriteToggle, showRelevanceScore = false }: HandCardProps) {
  const [isFavorite, setIsFavorite] = React.useState(hand.is_favorite || false);
  const [isTogglingFavorite, setIsTogglingFavorite] = React.useState(false);

  const handleFavoriteClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (isTogglingFavorite) return;

    setIsTogglingFavorite(true);
    const newFavoriteState = !isFavorite;
    setIsFavorite(newFavoriteState);

    try {
      await onFavoriteToggle?.(hand.hand_id, newFavoriteState);
    } catch (error) {
      // Revert on error
      setIsFavorite(!newFavoriteState);
      console.error('Failed to toggle favorite:', error);
    } finally {
      setIsTogglingFavorite(false);
    }
  };

  return (
    <Link href={`/hand/${hand.hand_id}`} className="block">
      <Card className="hover:shadow-lg transition-shadow cursor-pointer group">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg line-clamp-2 group-hover:text-primary transition-colors">
                {hand.summary}
              </CardTitle>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="secondary" className="text-xs">
                  {hand.event_name}
                </Badge>
                {showRelevanceScore && hand.relevance_score !== undefined && (
                  <Badge variant="outline" className="text-xs">
                    Score: {(hand.relevance_score * 100).toFixed(0)}%
                  </Badge>
                )}
              </div>
            </div>

            {/* Favorite button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleFavoriteClick}
              disabled={isTogglingFavorite}
              className="shrink-0"
              aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart
                className={cn(
                  'h-5 w-5 transition-colors',
                  isFavorite ? 'fill-red-500 text-red-500' : 'text-muted-foreground'
                )}
              />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pb-3">
          {/* Video preview thumbnail */}
          {hand.proxy_url && (
            <div className="relative aspect-video bg-muted rounded-md overflow-hidden mb-3">
              <div className="absolute inset-0 flex items-center justify-center">
                <Play className="h-12 w-12 text-white opacity-80 group-hover:opacity-100 transition-opacity" />
              </div>
              {/* In production, this would be a video thumbnail */}
              <div className="absolute inset-0 bg-gradient-to-br from-slate-800 to-slate-900" />
            </div>
          )}

          {/* Hand metadata */}
          <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
            {hand.players && hand.players.length > 0 && (
              <div className="flex items-center gap-1.5">
                <Users className="h-4 w-4" />
                <span className="truncate">{hand.players.slice(0, 2).join(', ')}</span>
                {hand.players.length > 2 && <span>+{hand.players.length - 2}</span>}
              </div>
            )}

            {hand.pot_size_usd && (
              <div className="flex items-center gap-1.5">
                <DollarSign className="h-4 w-4" />
                <span>{formatCurrency(hand.pot_size_usd)}</span>
              </div>
            )}

            {hand.timestamp_start && (
              <div className="flex items-center gap-1.5 col-span-2">
                <Calendar className="h-4 w-4" />
                <span>{new Date(hand.timestamp_start).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </CardContent>

        <CardFooter className="pt-0">
          <Button variant="outline" size="sm" className="w-full" asChild>
            <span>View Details</span>
          </Button>
        </CardFooter>
      </Card>
    </Link>
  );
}
