'use client';

import React, { useCallback, useState } from 'react';
import { Card } from '@/components/ui/card';
import { SearchResultItem } from '@/types/search';
import { HandThumbnail } from './HandThumbnail';
import { HandMetadata } from './HandMetadata';
import { HandTags } from './HandTags';
import { cn } from '@/lib/utils';

export interface HandCardProps {
  hand: SearchResultItem;
  onClick?: (handId: string) => void;
  priority?: boolean;
  className?: string;
}

/**
 * HandCard Component
 *
 * Accessible poker hand search result card with:
 * - Video thumbnail with duration badge
 * - Hand metadata (pot, players, result)
 * - Tag chips with color coding
 * - Keyboard navigation (Enter/Space to activate)
 * - Screen reader support (ARIA labels, role="button")
 * - Focus visible styles for accessibility
 * - Mobile responsive layout
 *
 * WCAG 2.1 AA Compliance:
 * - Color contrast: 4.5:1 for text on background
 * - Focus indicators: Visible with :focus-visible
 * - Keyboard accessible: Tab navigation + Enter/Space activation
 * - ARIA labels: aria-label describes card content
 * - Semantic HTML: Uses role="button" for keyboard interaction
 *
 * @param hand - SearchResultItem to display
 * @param onClick - Callback when card is activated
 * @param priority - Whether to prioritize image loading (for above-fold cards)
 * @param className - Additional CSS classes
 */
export function HandCard({
  hand,
  onClick,
  priority = false,
  className
}: HandCardProps) {
  const [isFocused, setIsFocused] = useState(false);
  const isClickable = !!onClick;

  const handleClick = useCallback(() => {
    if (isClickable) {
      onClick?.(hand.handId);
    }
  }, [hand.handId, onClick, isClickable]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        handleClick();
      }
    },
    [isClickable, handleClick]
  );

  const handleFocus = useCallback(() => {
    setIsFocused(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsFocused(false);
  }, []);

  // Create descriptive label for screen readers and accessibility
  const ariaLabel = `
    Poker hand: ${hand.hero_name} vs ${hand.villain_name || 'Opponent'}.
    Pot: ${hand.pot_bb} BB.
    ${hand.result ? `Result: ${hand.result}.` : ''}
    Score: ${Math.round(hand.score * 100)}% match.
    ${isClickable ? 'Press Enter or Space to view details.' : ''}
  `.trim().replace(/\s+/g, ' ');

  return (
    <Card
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onFocus={handleFocus}
      onBlur={handleBlur}
      aria-label={ariaLabel}
      aria-pressed={undefined}
      className={cn(
        'flex flex-col gap-3 p-4 transition-all duration-200 ease-out',
        // Base styles
        'bg-white dark:bg-slate-950',
        'border-2 border-slate-200 dark:border-slate-800',
        'rounded-lg shadow-sm',
        // Hover state
        isClickable && [
          'cursor-pointer',
          'hover:border-poker-chip-green hover:shadow-md',
          'hover:bg-slate-50 dark:hover:bg-slate-900/50'
        ],
        // Focus visible (keyboard navigation)
        isFocused && isClickable && [
          'outline-none',
          'border-poker-chip-green',
          'ring-2 ring-poker-chip-green/50',
          'shadow-lg'
        ],
        // Responsive
        'w-full',
        // Additional classes
        className
      )}
    >
      {/* Video Thumbnail Section */}
      <div className="relative overflow-hidden rounded-md">
        <HandThumbnail
          thumbnailUrl={hand.thumbnail_url}
          handId={hand.handId}
          priority={priority}
        />
      </div>

      {/* Hand Metadata Section */}
      <div className="flex flex-col gap-2">
        <HandMetadata
          potBB={hand.pot_bb}
          heroName={hand.hero_name}
          villainName={hand.villain_name}
          result={hand.result}
        />

        {/* Relevance Score Badge */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
            Relevance: {Math.round(hand.score * 100)}%
          </span>
          {hand.result && (
            <span
              className={cn(
                'text-xs font-bold px-2 py-1 rounded-full',
                hand.result === 'WIN' && 'bg-poker-chip-green/20 text-poker-chip-green',
                hand.result === 'LOSE' && 'bg-poker-chip-red/20 text-poker-chip-red',
                hand.result === 'SPLIT' && 'bg-poker-chip-yellow/20 text-poker-chip-yellow'
              )}
            >
              {hand.result}
            </span>
          )}
        </div>
      </div>

      {/* Tags Section */}
      <div className="pt-1 border-t border-slate-200 dark:border-slate-800">
        <HandTags tags={Array.from(hand.tags)} maxVisible={3} />
      </div>
    </Card>
  );
}

export default HandCard;
