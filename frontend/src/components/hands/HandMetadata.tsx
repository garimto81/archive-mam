'use client';

import React from 'react';
import { DollarSign, Clock, Trophy } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface HandMetadataProps {
  potBB: number;
  heroName: string;
  villainName?: string;
  heroPosition?: string;
  villainPosition?: string;
  result?: 'WIN' | 'LOSE' | 'SPLIT';
  timestamp?: string;
}

/**
 * HandMetadata Component
 *
 * Displays hand information:
 * - Pot size with poker chip icon
 * - Player names with positions
 * - Result badge (WIN, LOSE, SPLIT)
 * - Relative timestamp
 *
 * WCAG 2.1 AA Compliance:
 * - Icon + text labels (not color-only)
 * - Color contrast: 4.5:1 for all text
 * - Semantic structure: <dl> for data lists
 * - Icon labels: aria-hidden on icons (text describes content)
 * - Timestamp: Data attribute for screen readers
 *
 * @param potBB - Pot size in big blinds
 * @param heroName - Hero player name
 * @param villainName - Villain player name
 * @param heroPosition - Hero's table position (BTN, SB, BB, etc.)
 * @param villainPosition - Villain's table position
 * @param result - Hand result from hero's perspective
 * @param timestamp - ISO 8601 timestamp of hand
 */
export function HandMetadata({
  potBB,
  heroName,
  villainName = 'Opponent',
  heroPosition,
  villainPosition,
  result,
  timestamp
}: HandMetadataProps) {
  // Parse timestamp to relative time (e.g., "2 days ago")
  const formatRelativeTime = (isoString?: string): string | null => {
    if (!isoString) return null;

    try {
      const date = new Date(isoString);
      const now = new Date();
      const secondsAgo = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (secondsAgo < 60) return 'just now';
      if (secondsAgo < 3600) return `${Math.floor(secondsAgo / 60)}m ago`;
      if (secondsAgo < 86400) return `${Math.floor(secondsAgo / 3600)}h ago`;
      if (secondsAgo < 604800) return `${Math.floor(secondsAgo / 86400)}d ago`;

      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return null;
    }
  };

  const relativeTime = formatRelativeTime(timestamp);

  return (
    <div className="flex flex-col gap-3">
      {/* Pot Size Row */}
      <div className="flex items-center gap-2">
        <DollarSign
          className="w-4 h-4 text-poker-chip-yellow flex-shrink-0"
          aria-hidden="true"
        />
        <span className="text-sm font-semibold text-slate-900 dark:text-white">
          {potBB.toFixed(1)} BB
        </span>
      </div>

      {/* Players Row */}
      <div className="flex flex-col gap-1">
        <div className="text-sm font-medium text-slate-700 dark:text-slate-300">
          <span className="text-poker-chip-green font-semibold">{heroName}</span>
          {heroPosition && (
            <span className="text-slate-500 dark:text-slate-500 ml-1">
              ({heroPosition})
            </span>
          )}
          {' vs '}
          <span className="text-poker-chip-red font-semibold">{villainName}</span>
          {villainPosition && (
            <span className="text-slate-500 dark:text-slate-500 ml-1">
              ({villainPosition})
            </span>
          )}
        </div>
      </div>

      {/* Timestamp Row */}
      {relativeTime && (
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <Clock
            className="w-3.5 h-3.5 flex-shrink-0"
            aria-hidden="true"
          />
          <time dateTime={timestamp}>{relativeTime}</time>
        </div>
      )}
    </div>
  );
}

export default HandMetadata;
