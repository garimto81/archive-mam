'use client';

import React, { useState } from 'react';
import { OpenHandHistory, Round, PlayerAction } from '@/types/openHandHistory';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  ChevronDown,
  ChevronUp,
  ArrowRight,
  CheckCircle2,
  XCircle,
  DollarSign,
  TrendingUp,
  Eye,
  EyeOff,
} from 'lucide-react';

interface ActionTimelineProps {
  hand: OpenHandHistory;
  className?: string;
}

/**
 * ActionTimeline Component
 *
 * Displays street-by-street breakdown of hand actions:
 * - Preflop, Flop, Turn, River, Showdown
 * - Each action with player, type, and amount
 * - Board cards display with card icons
 * - Pot size after each street
 * - Collapsible sections
 *
 * @param hand - OpenHandHistory object
 */
export function ActionTimeline({ hand, className }: ActionTimelineProps) {
  const [expandedStreets, setExpandedStreets] = useState<Set<string>>(
    new Set(['Preflop', 'Showdown'])
  );

  const toggleStreet = (street: string) => {
    setExpandedStreets((prev) => {
      const next = new Set(prev);
      if (next.has(street)) {
        next.delete(street);
      } else {
        next.add(street);
      }
      return next;
    });
  };

  // Get player name by ID
  const getPlayerName = (playerId: string): string => {
    const player = hand.players.find((p) => p.id === playerId);
    return player?.name || 'Unknown';
  };

  // Calculate running pot total
  const calculatePotAtRound = (roundIndex: number): number => {
    return hand.rounds.slice(0, roundIndex + 1).reduce((total, round) => {
      return (
        total +
        round.actions.reduce((sum, action) => {
          return sum + (action.amount || 0);
        }, 0)
      );
    }, 0);
  };

  // Format card display (e.g., "As" -> "A♠")
  const formatCard = (card: string): { rank: string; suit: string; color: string } => {
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

    return {
      rank,
      suit: suitSymbols[suit] || suit,
      color: suitColors[suit] || 'text-gray-900',
    };
  };

  // Get action icon
  const getActionIcon = (action: PlayerAction) => {
    switch (action.action) {
      case 'Fold':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'Check':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'Bet':
      case 'Raise':
      case 'Call':
        return <TrendingUp className="w-4 h-4 text-blue-500" />;
      case 'Shows Cards':
        return <Eye className="w-4 h-4 text-purple-500" />;
      case 'Mucks Cards':
        return <EyeOff className="w-4 h-4 text-gray-500" />;
      default:
        return <ArrowRight className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <Card className={cn('p-6', className)} data-testid="action-timeline">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Action Timeline</h2>

      <div className="space-y-4">
        {hand.rounds.map((round, roundIndex) => {
          const isExpanded = expandedStreets.has(round.street);
          const potAtRound = calculatePotAtRound(roundIndex);
          const hasCards = round.cards && round.cards.length > 0;

          return (
            <div
              key={round.id}
              className="border border-gray-200 rounded-lg overflow-hidden"
              data-testid={`round-${round.street}`}
            >
              {/* Street Header */}
              <button
                onClick={() => toggleStreet(round.street)}
                className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <h3 className="text-lg font-bold text-gray-900">{round.street}</h3>

                  {/* Board Cards */}
                  {hasCards && (
                    <div className="flex gap-1">
                      {round.cards!.map((card, idx) => {
                        const { rank, suit, color } = formatCard(card);
                        return (
                          <div
                            key={idx}
                            className="w-8 h-12 bg-white border-2 border-gray-300 rounded flex flex-col items-center justify-center shadow-sm"
                          >
                            <span className="text-xs font-bold">{rank}</span>
                            <span className={cn('text-lg leading-none', color)}>{suit}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Pot Size */}
                  <Badge variant="secondary" className="gap-1">
                    <DollarSign className="w-3 h-3" />
                    Pot: {potAtRound.toLocaleString()}
                  </Badge>
                </div>

                {isExpanded ? (
                  <ChevronUp className="w-5 h-5 text-gray-600" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-600" />
                )}
              </button>

              {/* Actions */}
              {isExpanded && (
                <div className="p-4 space-y-2 bg-white">
                  {round.actions.map((action, actionIndex) => (
                    <div
                      key={actionIndex}
                      className="flex items-center gap-3 p-3 rounded-md hover:bg-gray-50 transition-colors"
                      data-testid={`action-${roundIndex}-${actionIndex}`}
                    >
                      {/* Action Number */}
                      <span className="text-xs font-mono text-gray-400 w-6">
                        {action.action_number}
                      </span>

                      {/* Action Icon */}
                      <div className="flex-shrink-0">{getActionIcon(action)}</div>

                      {/* Player Name */}
                      <span className="font-semibold text-sm text-gray-900 min-w-[120px]">
                        {action.player_id ? getPlayerName(action.player_id) : 'Site'}
                      </span>

                      {/* Action */}
                      <span className="text-sm text-gray-700">{action.action}</span>

                      {/* Amount */}
                      {action.amount && (
                        <span className="text-sm font-semibold text-blue-600">
                          {action.amount.toLocaleString()}
                        </span>
                      )}

                      {/* All-in Badge */}
                      {action.is_allin && (
                        <Badge variant="destructive" className="text-xs">
                          ALL-IN
                        </Badge>
                      )}

                      {/* Cards */}
                      {action.cards && action.cards.length > 0 && (
                        <div className="flex gap-1 ml-auto">
                          {action.cards.map((card, idx) => {
                            const { rank, suit, color } = formatCard(card);
                            return (
                              <div
                                key={idx}
                                className="w-6 h-9 bg-white border border-gray-300 rounded flex flex-col items-center justify-center text-xs"
                              >
                                <span className="font-bold">{rank}</span>
                                <span className={cn('text-sm leading-none', color)}>
                                  {suit}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Expand/Collapse All */}
      <div className="mt-4 flex justify-center">
        <button
          onClick={() => {
            if (expandedStreets.size === hand.rounds.length) {
              setExpandedStreets(new Set());
            } else {
              setExpandedStreets(new Set(hand.rounds.map((r) => r.street)));
            }
          }}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          {expandedStreets.size === hand.rounds.length ? 'Collapse All' : 'Expand All'}
        </button>
      </div>
    </Card>
  );
}
