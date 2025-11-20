'use client';

import React from 'react';
import { OpenHandHistory } from '@/types/openHandHistory';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Trophy, DollarSign, Coins } from 'lucide-react';

interface PotDistributionProps {
  hand: OpenHandHistory;
  className?: string;
}

/**
 * PotDistribution Component
 *
 * Displays pot distribution information:
 * - Main pot and side pots
 * - Winner(s) per pot
 * - Amount won per player
 * - Winning hand description
 * - Rake and jackpot contributions
 *
 * @param hand - OpenHandHistory object
 */
export function PotDistribution({ hand, className }: PotDistributionProps) {
  const bigBlind = hand.big_blind_amount;

  // Get player name by ID
  const getPlayerName = (playerId: string): string => {
    const player = hand.players.find((p) => p.id === playerId);
    return player?.name || 'Unknown';
  };

  // Calculate total pot (all pots combined)
  const totalPot = hand.pots.reduce((sum, pot) => sum + pot.amount, 0);
  const totalRake = hand.pots.reduce((sum, pot) => sum + pot.rake, 0);
  const totalJackpot = hand.pots.reduce((sum, pot) => sum + pot.jackpot, 0);

  return (
    <Card className={cn('p-6', className)} data-testid="pot-distribution">
      <div className="flex items-center gap-2 mb-4">
        <Coins className="w-5 h-5 text-yellow-600" />
        <h2 className="text-xl font-bold text-gray-900">Pot Distribution</h2>
      </div>

      <div className="space-y-4">
        {/* Total Pot Summary */}
        <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border-2 border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Total Pot</span>
            <span className="text-2xl font-bold text-gray-900">
              {totalPot.toLocaleString()}
            </span>
          </div>
          <div className="text-xs text-gray-600">
            {(totalPot / bigBlind).toFixed(1)} BB
          </div>
        </div>

        {/* Individual Pots */}
        {hand.pots.map((pot) => (
          <div
            key={pot.number}
            className="border border-gray-200 rounded-lg p-4"
            data-testid={`pot-${pot.number}`}
          >
            {/* Pot Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Badge variant={pot.number === 1 ? 'default' : 'secondary'}>
                  {pot.number === 1 ? 'Main Pot' : `Side Pot ${pot.number - 1}`}
                </Badge>
                <span className="text-lg font-bold text-gray-900">
                  {pot.amount.toLocaleString()}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {(pot.amount / bigBlind).toFixed(1)} BB
              </span>
            </div>

            {/* Winners */}
            <div className="space-y-2">
              {pot.player_wins.map((win, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-md"
                  data-testid={`winner-${pot.number}-${idx}`}
                >
                  {/* Trophy Icon */}
                  <Trophy className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />

                  {/* Winner Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-gray-900">
                        {getPlayerName(win.player_id)}
                      </span>
                      {win.player_id === hand.hero_player_id && (
                        <Badge variant="default" className="text-xs">
                          HERO
                        </Badge>
                      )}
                    </div>

                    {/* Amount Won */}
                    <div className="flex items-center gap-2 mb-1">
                      <DollarSign className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-semibold text-green-700">
                        Won {win.amount.toLocaleString()}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({(win.amount / bigBlind).toFixed(1)} BB)
                      </span>
                    </div>

                    {/* Winning Hand */}
                    {win.hand && (
                      <p className="text-sm text-gray-700 font-medium">{win.hand}</p>
                    )}

                    {/* Winning Cards */}
                    {win.cards && win.cards.length > 0 && (
                      <div className="flex gap-1 mt-2">
                        {win.cards.map((card, cardIdx) => {
                          const rank = card.slice(0, -1);
                          const suit = card.slice(-1);
                          const suitSymbols: Record<string, string> = {
                            s: '♠',
                            h: '♥',
                            d: '♦',
                            c: '♣',
                          };
                          const suitColors: Record<string, string> = {
                            s: 'text-gray-900',
                            h: 'text-red-600',
                            d: 'text-blue-600',
                            c: 'text-green-700',
                          };

                          return (
                            <div
                              key={cardIdx}
                              className="w-7 h-10 bg-white border border-gray-300 rounded flex flex-col items-center justify-center text-xs"
                            >
                              <span className="font-bold">{rank}</span>
                              <span className={cn('text-sm', suitColors[suit])}>
                                {suitSymbols[suit]}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Rake/Jackpot */}
            {(pot.rake > 0 || pot.jackpot > 0) && (
              <div className="mt-3 pt-3 border-t border-gray-200 space-y-1">
                {pot.rake > 0 && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">Rake</span>
                    <span className="font-semibold text-gray-700">
                      {pot.rake.toLocaleString()}
                    </span>
                  </div>
                )}
                {pot.jackpot > 0 && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">Jackpot</span>
                    <span className="font-semibold text-gray-700">
                      {pot.jackpot.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Total Deductions */}
        {(totalRake > 0 || totalJackpot > 0) && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Deductions</h3>
            <div className="space-y-1">
              {totalRake > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Total Rake</span>
                  <span className="font-semibold text-gray-900">
                    {totalRake.toLocaleString()}
                  </span>
                </div>
              )}
              {totalJackpot > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Total Jackpot</span>
                  <span className="font-semibold text-gray-900">
                    {totalJackpot.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
