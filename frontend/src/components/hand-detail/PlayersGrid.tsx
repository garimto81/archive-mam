'use client';

import React from 'react';
import { OpenHandHistory, Player } from '@/types/openHandHistory';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { User, Crown, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface PlayersGridProps {
  hand: OpenHandHistory;
  className?: string;
}

/**
 * PlayersGrid Component
 *
 * Displays all players in the hand with:
 * - Player name and avatar (initials)
 * - Starting stack (in BB)
 * - Position indicator (BTN, SB, BB, etc.)
 * - Result indicator (WIN, LOSS, SPLIT)
 * - Hero highlighting
 *
 * @param hand - OpenHandHistory object
 */
export function PlayersGrid({ hand, className }: PlayersGridProps) {
  const bigBlind = hand.big_blind_amount;

  // Calculate results for each player
  const playerResults = hand.players.map((player) => {
    const totalWon = hand.pots.reduce((sum, pot) => {
      const win = pot.player_wins.find((w) => w.player_id === player.id);
      return sum + (win?.amount || 0);
    }, 0);

    // Calculate total invested (all actions with amount)
    const totalInvested = hand.rounds.reduce((sum, round) => {
      return (
        sum +
        round.actions
          .filter((action) => action.player_id === player.id && action.amount)
          .reduce((actionSum, action) => actionSum + (action.amount || 0), 0)
      );
    }, 0);

    const net = totalWon - totalInvested;

    return {
      player,
      totalWon,
      totalInvested,
      net,
      result: net > 0 ? 'WIN' : net < 0 ? 'LOSS' : 'SPLIT',
    };
  });

  // Determine position labels
  const getPositionLabel = (player: Player): string => {
    const seatDiff = (player.seat - hand.dealer_seat + hand.table_size) % hand.table_size;

    if (seatDiff === 0) return 'BTN';
    if (seatDiff === 1) return 'SB';
    if (seatDiff === 2) return 'BB';
    if (seatDiff === hand.table_size - 1) return 'CO';
    if (seatDiff === hand.table_size - 2) return 'HJ';
    if (seatDiff === 3) return 'UTG';
    if (seatDiff === 4) return 'UTG+1';
    return 'MP';
  };

  // Get initials for avatar
  const getInitials = (name: string): string => {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return parts[0][0] + parts[1][0];
    }
    return name.substring(0, 2);
  };

  return (
    <Card className={cn('p-6', className)} data-testid="players-grid">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Players</h2>

      <div className="space-y-3">
        {playerResults.map(({ player, net, result }) => {
          const isHero = player.id === hand.hero_player_id;
          const position = getPositionLabel(player);
          const stackInBB = player.starting_stack / bigBlind;

          return (
            <div
              key={player.id}
              className={cn(
                'flex items-center gap-4 p-4 rounded-lg border-2 transition-colors',
                isHero
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-white border-gray-200 hover:border-gray-300'
              )}
              data-testid={`player-${player.id}`}
            >
              {/* Avatar */}
              <div
                className={cn(
                  'w-12 h-12 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0',
                  isHero ? 'bg-blue-600' : 'bg-gray-500'
                )}
                aria-label={`${player.name} avatar`}
              >
                {isHero ? (
                  <Crown className="w-6 h-6" />
                ) : (
                  <span>{getInitials(player.name).toUpperCase()}</span>
                )}
              </div>

              {/* Player Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-bold text-gray-900 truncate">
                    {player.name}
                  </h3>
                  {isHero && (
                    <Badge variant="default" className="text-xs">
                      HERO
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {position}
                  </Badge>
                </div>

                <div className="flex items-center gap-3 text-xs text-gray-600">
                  <span>Stack: {stackInBB.toFixed(1)} BB</span>
                  <span>•</span>
                  <span className={cn(
                    'font-semibold',
                    net > 0 && 'text-green-600',
                    net < 0 && 'text-red-600',
                    net === 0 && 'text-gray-600'
                  )}>
                    {net > 0 && '+'}
                    {(net / bigBlind).toFixed(1)} BB
                  </span>
                </div>
              </div>

              {/* Result Badge */}
              <div className="flex-shrink-0">
                {result === 'WIN' && (
                  <div className="flex items-center gap-1 text-green-600">
                    <TrendingUp className="w-5 h-5" />
                    <span className="text-xs font-bold">WIN</span>
                  </div>
                )}
                {result === 'LOSS' && (
                  <div className="flex items-center gap-1 text-red-600">
                    <TrendingDown className="w-5 h-5" />
                    <span className="text-xs font-bold">LOSS</span>
                  </div>
                )}
                {result === 'SPLIT' && (
                  <div className="flex items-center gap-1 text-gray-600">
                    <Minus className="w-5 h-5" />
                    <span className="text-xs font-bold">SPLIT</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-600">
          <span className="font-medium">{hand.players.length} players</span>
          {' • '}
          <span>Dealer: Seat {hand.dealer_seat}</span>
        </div>
      </div>
    </Card>
  );
}
