'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { X, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CardSelectorProps {
  value: string[];
  onChange: (cards: string[]) => void;
  maxCards?: number;
  label?: string;
  type?: 'hero' | 'villain';
}

const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUITS = [
  { symbol: '♠', name: 'Spade', color: 'text-gray-900', bg: 'bg-gray-100 hover:bg-gray-200' },
  { symbol: '♥', name: 'Heart', color: 'text-red-600', bg: 'bg-red-50 hover:bg-red-100' },
  { symbol: '♦', name: 'Diamond', color: 'text-blue-600', bg: 'bg-blue-50 hover:bg-blue-100' },
  { symbol: '♣', name: 'Club', color: 'text-green-700', bg: 'bg-green-50 hover:bg-green-100' },
];

const SUIT_SYMBOLS: Record<string, string> = {
  S: '♠',
  H: '♥',
  D: '♦',
  C: '♣',
};

const SUIT_NAMES: Record<string, string> = {
  S: 'Spade',
  H: 'Heart',
  D: 'Diamond',
  C: 'Club',
};

export function CardSelector({
  value,
  onChange,
  maxCards = 2,
  label = 'Select Cards',
  type = 'hero',
}: CardSelectorProps) {
  const [searchRank, setSearchRank] = useState('');
  const [searchSuit, setSearchSuit] = useState('');
  const [focusedCard, setFocusedCard] = useState<string | null>(null);

  const cards = useMemo(() => {
    const result: { rank: string; suit: string; symbol: string; code: string }[] = [];
    for (const rank of RANKS) {
      for (const suitKey of Object.keys(SUIT_SYMBOLS) as Array<keyof typeof SUIT_SYMBOLS>) {
        const symbol = SUIT_SYMBOLS[suitKey];
        const suitName = SUIT_NAMES[suitKey];
        const code = `${rank}${suitKey}`;
        if (symbol && suitName) {
          result.push({ rank, suit: suitName, symbol, code });
        }
      }
    }
    return result;
  }, []);

  const filteredCards = useMemo(() => {
    return cards.filter((card) => {
      const matchesRank = !searchRank || card.rank.toLowerCase().includes(searchRank.toLowerCase());
      const matchesSuit = !searchSuit || card.suit.toLowerCase().includes(searchSuit.toLowerCase());
      return matchesRank && matchesSuit;
    });
  }, [cards, searchRank, searchSuit]);

  const handleCardToggle = useCallback(
    (rank: string, suitKey: string) => {
      const cardCode = `${rank}${suitKey}`;
      const newValue = value.includes(cardCode)
        ? value.filter((c) => c !== cardCode)
        : value.length < maxCards
          ? [...value, cardCode]
          : value;
      onChange(newValue);
    },
    [value, onChange, maxCards],
  );

  const handleClear = useCallback(() => {
    onChange([]);
    setFocusedCard(null);
  }, [onChange]);

  const handleKeyDown = useCallback(
    (
      e: React.KeyboardEvent<HTMLButtonElement>,
      rank: string,
      suitKey: string,
    ) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleCardToggle(rank, suitKey);
      }
    },
    [handleCardToggle],
  );

  const typeColor = type === 'hero' ? 'border-blue-500' : 'border-red-500';
  const typeBg = type === 'hero' ? 'bg-blue-50' : 'bg-red-50';

  return (
    <div className="space-y-4">
      {/* Label */}
      <div className="flex items-center justify-between">
        <label
          className="block text-sm font-semibold text-gray-900"
          id="card-selector-label"
        >
          {label}
          {maxCards && (
            <span className="ml-2 text-xs font-normal text-gray-500">
              ({value.length}/{maxCards})
            </span>
          )}
        </label>
        {value.length > 0 && (
          <button
            onClick={handleClear}
            className="inline-flex items-center gap-1 px-2 py-1 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
            aria-label="Clear all selected cards"
            title="Clear selection"
          >
            <RotateCcw className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Selected Cards Display */}
      {value.length > 0 && (
        <div
          className={cn(
            'flex flex-wrap gap-2 p-3 rounded-lg border-2 border-dashed',
            typeColor,
            typeBg,
          )}
          role="region"
          aria-label="Selected cards"
        >
          {value.map((card) => {
            const rank = card.slice(0, -1);
            const suitKey = card.slice(-1);
            const suit = SUIT_NAMES[suitKey] || suitKey;
            const symbol = SUIT_SYMBOLS[suitKey] || suitKey;

            return (
              <div
                key={card}
                className="flex items-center gap-2 px-3 py-1 bg-white rounded-full border border-gray-200 shadow-sm"
              >
                <span className="font-semibold text-gray-900">
                  {rank}
                  <span className="ml-0.5">{symbol}</span>
                </span>
                <button
                  onClick={() => {
                    const newValue = value.filter((c) => c !== card);
                    onChange(newValue);
                  }}
                  className="p-0.5 hover:bg-gray-100 rounded transition-colors"
                  aria-label={`Remove ${rank} of ${suit}`}
                  title={`Remove ${rank}${symbol}`}
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Search Filters */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <label htmlFor="search-rank" className="block text-xs font-medium text-gray-700 mb-1">
            Rank
          </label>
          <input
            id="search-rank"
            type="text"
            value={searchRank}
            onChange={(e) => setSearchRank(e.target.value)}
            placeholder="e.g., A, K, Q"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Filter cards by rank"
          />
        </div>
        <div className="col-span-3">
          <label htmlFor="search-suit" className="block text-xs font-medium text-gray-700 mb-1">
            Suit
          </label>
          <div className="flex gap-2">
            {SUITS.map((suit) => (
              <button
                key={suit.symbol}
                onClick={() => {
                  const isActive = searchSuit === suit.name;
                  setSearchSuit(isActive ? '' : suit.name);
                }}
                className={cn(
                  'px-3 py-2 text-sm font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                  searchSuit === suit.name
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
                )}
                aria-label={`Filter by ${suit.name}s`}
                aria-pressed={searchSuit === suit.name}
              >
                {suit.symbol}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Card Grid */}
      <div
        className="overflow-y-auto max-h-72"
        role="region"
        aria-label="Card selection grid"
      >
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2 p-2 bg-gray-50 rounded-lg border border-gray-200">
          {filteredCards.map(({ rank, suit, symbol, code }) => {
            const suitKey = code.slice(-1);
            const isSelected = value.includes(code);
            const isDisabled = !isSelected && value.length >= maxCards;
            const suitInfo = SUITS.find((s) => s.name === suit);

            return (
              <button
                key={code}
                onFocus={() => setFocusedCard(code)}
                onBlur={() => setFocusedCard(null)}
                onClick={() => handleCardToggle(rank, suitKey)}
                onKeyDown={(e) => handleKeyDown(e, rank, suitKey)}
                disabled={isDisabled}
                className={cn(
                  'aspect-square flex flex-col items-center justify-center p-2 rounded-lg font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
                  isSelected
                    ? 'bg-blue-500 text-white ring-2 ring-blue-700 shadow-md'
                    : isDisabled
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed opacity-50'
                      : suitInfo
                        ? `${suitInfo.bg} text-gray-900 hover:shadow-md active:scale-95`
                        : 'bg-gray-100 hover:bg-gray-200',
                )}
                aria-label={`${rank} of ${suit}${isSelected ? ', selected' : ''}`}
                aria-pressed={isSelected}
                title={`${rank}${symbol}`}
              >
                <span>{rank}</span>
                <span className={cn('text-lg leading-none', suitInfo?.color)}>
                  {symbol}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Help Text */}
      <p className="text-xs text-gray-500">
        Select up to {maxCards} card{maxCards > 1 ? 's' : ''} • Use arrow keys to navigate •
        Press Enter to select
      </p>
    </div>
  );
}
