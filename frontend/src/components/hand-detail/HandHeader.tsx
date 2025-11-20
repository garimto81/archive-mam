'use client';

import React from 'react';
import { OpenHandHistory } from '@/types/openHandHistory';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, MapPin, Trophy, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HandHeaderProps {
  hand: OpenHandHistory;
  className?: string;
}

/**
 * HandHeader Component
 *
 * Displays game information at the top of hand detail page:
 * - Tournament/game name
 * - Game type (NL Hold'em, PLO, etc.)
 * - Stakes (blinds)
 * - Date and location
 * - Tags
 *
 * @param hand - OpenHandHistory object
 */
export function HandHeader({ hand, className }: HandHeaderProps) {
  const formattedDate = new Date(hand.start_date_utc).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const gameTypeLabel = `${hand.bet_limit.bet_type} ${hand.game_type}`;
  const stakesLabel = `${hand.currency} ${hand.small_blind_amount}/${hand.big_blind_amount}${
    hand.ante_amount ? ` (${hand.ante_amount})` : ''
  }`;

  // Extract tags from hand (if available in future extensions)
  const tags = [
    hand.flags?.run_it_twice && 'RUN_IT_TWICE',
    hand.flags?.anonymous && 'ANONYMOUS',
    hand.flags?.fast && 'FAST_FOLD',
  ].filter(Boolean) as string[];

  return (
    <Card
      className={cn('p-6 bg-gradient-to-br from-slate-50 to-white border-2', className)}
      data-testid="hand-header"
    >
      <div className="space-y-4">
        {/* Title */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            {hand.tournament_info?.name || hand.table_name}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Hand #{hand.game_number}</p>
        </div>

        {/* Game Info Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Game Type */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
              <Trophy className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Game Type</p>
              <p className="text-sm font-semibold text-gray-900">{gameTypeLabel}</p>
            </div>
          </div>

          {/* Stakes */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Stakes</p>
              <p className="text-sm font-semibold text-gray-900">{stakesLabel}</p>
            </div>
          </div>

          {/* Date */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
              <Calendar className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Date</p>
              <p className="text-sm font-semibold text-gray-900">{formattedDate}</p>
            </div>
          </div>

          {/* Location/Site */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
              <MapPin className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Site</p>
              <p className="text-sm font-semibold text-gray-900">{hand.site_name}</p>
            </div>
          </div>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200">
            <span className="text-xs font-medium text-gray-500">Tags:</span>
            {tags.map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="text-xs"
                data-testid={`tag-${tag}`}
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Tournament Info */}
        {hand.tournament_info && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            {hand.tournament_info.buyin && (
              <div>
                <p className="text-xs text-gray-500">Buy-in</p>
                <p className="text-sm font-semibold text-gray-900">
                  {hand.currency} {hand.tournament_info.buyin.toLocaleString()}
                </p>
              </div>
            )}
            {hand.tournament_info.level && (
              <div>
                <p className="text-xs text-gray-500">Level</p>
                <p className="text-sm font-semibold text-gray-900">
                  {hand.tournament_info.level}
                </p>
              </div>
            )}
            <div>
              <p className="text-xs text-gray-500">Table Size</p>
              <p className="text-sm font-semibold text-gray-900">
                {hand.players.length}/{hand.table_size} players
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
