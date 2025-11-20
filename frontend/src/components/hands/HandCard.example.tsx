/**
 * HandCard Component Usage Examples
 *
 * This file demonstrates real-world usage patterns for the HandCard component
 * in various contexts (search results, favorites, recommendations, etc.)
 */

import { HandCard } from './HandCard';
import { SearchResultItem } from '@/types/search';

/**
 * Example 1: Basic Search Results Grid
 */
export function SearchResultsExample() {
  const mockResults: SearchResultItem[] = [
    {
      handId: 'wsop_2024_main_event_hand_3421',
      score: 0.92,
      hero_name: 'Junglemann',
      villain_name: 'Phil Ivey',
      street: 'RIVER',
      pot_bb: 145.5,
      result: 'WIN',
      tags: ['HERO_CALL', 'RIVER_DECISION', 'HIGH_STAKES'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/wsop_2024_hand_3421.jpg',
    },
    {
      handId: 'mpp_2024_day2_hand_142',
      score: 0.87,
      hero_name: 'Daniel Negreanu',
      villain_name: 'Doug Polk',
      street: 'TURN',
      pot_bb: 87.25,
      result: 'WIN',
      tags: ['BLUFF', 'TURN_DECISION', 'ALL_IN'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/mpp_2024_hand_142.jpg',
    }
  ];

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold mb-6">Search Results</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockResults.map((hand, index) => (
          <HandCard
            key={hand.handId}
            hand={hand}
            onClick={(id) => {/* Navigate to hand: ${id} */}}
            priority={index < 6}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Example 2: In a Modal/Drawer
 *
 * Use Case: Quick preview when user hovers or clicks on a result
 */
export function ModalHandCardExample() {
  const hand: SearchResultItem = {
    handId: 'wsop_2024_main_event_hand_3421',
    score: 0.92,
    hero_name: 'Junglemann',
    villain_name: 'Phil Ivey',
    street: 'RIVER',
    pot_bb: 145.5,
    result: 'WIN',
    tags: ['HERO_CALL', 'RIVER_DECISION'],
    thumbnail_url: 'gs://poker-videos-prod/thumbnails/wsop_2024_hand_3421.jpg',
  };

  return (
    <div className="w-full max-w-sm">
      <HandCard
        hand={hand}
        onClick={() => {/* Open full hand details */}}
        priority={true}
      />
    </div>
  );
}

/**
 * Example 3: Favorites List
 *
 * Use Case: Display user's saved favorite hands
 */
export function FavoritesListExample() {
  const favorites: SearchResultItem[] = [
    {
      handId: 'wsop_2024_main_event_hand_3421',
      score: 1.0,
      hero_name: 'Junglemann',
      villain_name: 'Phil Ivey',
      street: 'RIVER',
      pot_bb: 145.5,
      result: 'WIN',
      tags: ['HERO_CALL', 'RIVER_DECISION'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/wsop_2024_hand_3421.jpg'
    }
  ];

  return (
    <div className="w-full">
      <h2 className="text-2xl font-bold mb-6">My Favorites</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {favorites.map((hand) => (
          <HandCard
            key={hand.handId}
            hand={hand}
            onClick={() => {/* Analyze hand */}}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Example 4: Recommendations Component
 *
 * Use Case: "Similar hands you might like" section
 */
export function RecommendationsExample() {
  const recommendations: SearchResultItem[] = [
    {
      handId: 'apl_2024_hand_567',
      score: 0.85,
      hero_name: 'Tom Dwan',
      villain_name: 'Ivey',
      street: 'RIVER',
      pot_bb: 220.0,
      result: 'WIN',
      tags: ['BLUFF', 'RIVER_DECISION'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/apl_2024_hand_567.jpg'
    }
  ];

  return (
    <section className="w-full py-8">
      <h3 className="text-xl font-bold mb-4">Similar Hands You Might Like</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {recommendations.map((hand) => (
          <HandCard
            key={hand.handId}
            hand={hand}
            onClick={() => {/* User clicked recommendation */}}
          />
        ))}
      </div>
    </section>
  );
}

/**
 * Example 5: Hand Comparison
 *
 * Use Case: Side-by-side comparison of two similar hands
 */
export function HandComparisonExample() {
  const hands: [SearchResultItem, SearchResultItem] = [
    {
      handId: 'hand_1',
      score: 0.92,
      hero_name: 'Junglemann',
      villain_name: 'Phil Ivey',
      street: 'RIVER',
      pot_bb: 145.5,
      result: 'WIN',
      tags: ['HERO_CALL', 'RIVER_DECISION'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/hand_1.jpg'
    },
    {
      handId: 'hand_2',
      score: 0.89,
      hero_name: 'Daniel Negreanu',
      villain_name: 'Ivey',
      street: 'RIVER',
      pot_bb: 120.0,
      result: 'LOSE',
      tags: ['RIVER_DECISION', 'VALUE_BET'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/hand_2.jpg'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 className="text-lg font-bold mb-4">Hand 1: WIN</h3>
        <HandCard hand={hands[0]} onClick={() => {/* Hand clicked */}} />
      </div>
      <div>
        <h3 className="text-lg font-bold mb-4">Hand 2: LOSE</h3>
        <HandCard hand={hands[1]} onClick={() => {/* Hand clicked */}} />
      </div>
    </div>
  );
}

/**
 * Example 6: Masonry Layout (Pinterest-style)
 *
 * Use Case: Display many hands with varying heights
 */
export function MasonryLayoutExample() {
  const manyHands: SearchResultItem[] = Array.from({ length: 20 }, (_, i) => ({
    handId: `hand_${i}`,
    score: Math.random(),
    hero_name: `Player ${i}`,
    villain_name: `Opponent ${i}`,
    street: ['PREFLOP', 'FLOP', 'TURN', 'RIVER'][Math.floor(Math.random() * 4)] as any,
    pot_bb: Math.random() * 500,
    result: ['WIN', 'LOSE', 'SPLIT'][Math.floor(Math.random() * 3)] as any,
    tags: ['HERO_CALL'],
    thumbnail_url: `gs://poker-videos-prod/thumbnails/hand_${i}.jpg`
  }));

  return (
    <div className="columns-1 sm:columns-2 lg:columns-3 gap-4">
      {manyHands.map((hand) => (
        <div key={hand.handId} className="break-inside-avoid mb-4">
          <HandCard
            hand={hand}
            onClick={() => {/* Clicked */}}
          />
        </div>
      ))}
    </div>
  );
}

/**
 * Example 7: With Custom Styling
 *
 * Use Case: Override styles for specific use case
 */
export function CustomStyleHandCardExample() {
  const hand: SearchResultItem = {
    handId: 'custom_hand',
    score: 0.95,
    hero_name: 'Pro Player',
    villain_name: 'Opponent',
    street: 'RIVER',
    pot_bb: 500.0,
    result: 'WIN',
    tags: ['HIGH_STAKES', 'RIVER_DECISION'],
    thumbnail_url: 'gs://poker-videos-prod/thumbnails/custom_hand.jpg'
  };

  return (
    <div className="w-80">
      <HandCard
        hand={hand}
        onClick={() => {/* Hand clicked */}}
        className="border-4 border-poker-chip-gold shadow-2xl hover:scale-105"
      />
    </div>
  );
}

/**
 * Example 8: Accessibility Testing
 *
 * Use Case: Test keyboard navigation and screen reader support
 *
 * Testing Instructions:
 * 1. Tab through the cards
 * 2. Verify focus indicator (green ring) appears
 * 3. Press Enter or Space to activate
 * 4. Screen reader should announce full card content
 */
export function AccessibilityTestingExample() {
  const testHands: SearchResultItem[] = [
    {
      handId: 'a11y_test_1',
      score: 0.9,
      hero_name: 'Test Hero',
      villain_name: 'Test Villain',
      street: 'RIVER',
      pot_bb: 100,
      result: 'WIN',
      tags: ['HERO_CALL'],
      thumbnail_url: 'gs://poker-videos-prod/thumbnails/test.jpg'
    }
  ];

  return (
    <div className="p-8 bg-gray-100">
      <h2 className="text-2xl font-bold mb-4">
        Accessibility Testing
      </h2>
      <div className="space-y-4">
        <div className="bg-white p-4 rounded">
          <h3 className="font-bold mb-2">Tab Navigation Test</h3>
          <p>Press Tab to focus the card below and verify green focus ring appears</p>
        </div>
        <HandCard
          hand={testHands[0]!}
          onClick={(id) => {/* Activated */}}
        />
        <div className="bg-white p-4 rounded">
          <h3 className="font-bold mb-2">Screen Reader Test</h3>
          <p>Enable your screen reader and navigate to the card above</p>
          <p>You should hear the full hand description</p>
        </div>
      </div>
    </div>
  );
}
