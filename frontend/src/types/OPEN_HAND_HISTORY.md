# Open Hand History TypeScript Type Definitions

Complete TypeScript type definitions for the [Open Hand History specification](https://hh-specs.handhistory.org).

## Overview

This directory contains comprehensive type definitions for the Open Hand History (OHH) format, an industry-standard specification for documenting online poker hand histories. These types provide:

- **Strict type safety** - No `any` types, full compile-time validation
- **Advanced TypeScript patterns** - Conditional types, mapped types, type guards
- **Comprehensive documentation** - JSDoc comments for all types and interfaces
- **Utility types** - Helper types for common transformations and filters

## Files

### Core Type Definitions

| File | Description | Key Types |
|------|-------------|-----------|
| `gameTypes.ts` | Game-related types | `GameVariant`, `BetType`, `Street`, `BetLimit`, `TableInfo` |
| `playerTypes.ts` | Player and action types | `Player`, `PlayerAction`, `ActionType`, `Round`, `Pot` |
| `openHandHistory.ts` | Main specification interface | `OpenHandHistory`, `SearchResult`, `HandStatistics` |
| `index.ts` | Re-exports all types | All types available from single import |

### Type Categories

#### 1. Game Types (`gameTypes.ts`)

```typescript
// Game variants
type GameVariant = 'Holdem' | 'Omaha' | 'OmahaHiLo' | 'Stud' | 'StudHiLo' | 'Draw';

// Betting structures
type BetType = 'NL' | 'PL' | 'FL';

// Betting rounds
type Street = 'Preflop' | 'Flop' | 'Turn' | 'River' | 'Showdown';

// Betting constraints
interface BetLimit {
  bet_type: BetType;
  bet_cap: number | null;
}
```

#### 2. Player & Action Types (`playerTypes.ts`)

```typescript
// All possible player actions
type ActionType =
  | 'Dealt Cards' | 'Shows Cards' | 'Mucks Cards'
  | 'Post Ante' | 'Post SB' | 'Post BB' | 'Fold' | 'Check'
  | 'Bet' | 'Raise' | 'Call'
  | 'Added Chips' | 'Sits Down' | 'Stands Up';

// Player information
interface Player {
  id: string;
  seat: number;
  name: string;
  starting_stack: number;
  is_sitting_out: boolean;
}

// Player action with type safety
interface PlayerAction {
  action_number: number;
  player_id?: string;
  action: ActionType;
  amount?: number;
  is_allin: boolean;
  cards?: Card[];
}
```

#### 3. Main Interface (`openHandHistory.ts`)

```typescript
interface OpenHandHistory {
  // Version & Identifiers
  spec_version: string;
  game_number: string;
  site_name: string;

  // Game Configuration
  game_type: GameVariant;
  bet_limit: BetLimit;
  table_size: number;

  // Blinds
  small_blind_amount: number;
  big_blind_amount: number;

  // Players & Actions
  players: Player[];
  rounds: Round[];
  pots: Pot[];

  // Optional Fields
  flags?: GameFlags;
  tournament_info?: TournamentInfo;
}
```

## Usage Examples

### Basic Import

```typescript
import {
  OpenHandHistory,
  Player,
  PlayerAction,
  ActionType,
  Street,
  GameVariant,
} from '@/types';
```

### Type Guards

```typescript
import { isOpenHandHistory, isActionType, isGameVariant } from '@/types';

// Validate hand history structure
if (isOpenHandHistory(data)) {
  console.log('Valid hand history:', data.game_number);
}

// Validate action type
if (isActionType('Bet')) {
  // Type-safe action handling
}
```

### Working with Actions

```typescript
import { PlayerAction, ActionType, isBettingAction } from '@/types';

function processAction(action: PlayerAction) {
  if (isBettingAction(action.action)) {
    // Type narrowing: amount is available
    console.log('Bet amount:', action.amount);
  }
}
```

### Conditional Types

```typescript
import { TypedPlayerAction, ActionWithAmount } from '@/types';

// Type-safe action creation with conditional requirements
const betAction: TypedPlayerAction<'Bet'> = {
  action_number: 1,
  player_id: 'player1',
  action: 'Bet',
  amount: 100, // Required for 'Bet' action
  is_allin: false,
};

// This would cause a compile error (amount required):
// const betAction: TypedPlayerAction<'Bet'> = {
//   action: 'Bet',
//   is_allin: false,
// };
```

### Utility Types

```typescript
import {
  OpenHandHistory,
  HeroPlayer,
  RoundsByStreet,
  ActionsByType,
  AllActions,
} from '@/types';

type Hand = OpenHandHistory;

// Extract hero player type
type Hero = HeroPlayer<Hand>;

// Get all preflop rounds
type PreflopRounds = RoundsByStreet<Hand, 'Preflop'>;

// Get all bet actions
type BetActions = ActionsByType<Hand, 'Bet'>;

// Get all actions from any round
type Actions = AllActions<Hand>;
```

### Filtering and Querying

```typescript
import { HandHistoryFilter, HandHistoryQuery } from '@/types';

const filter: HandHistoryFilter = {
  game_type: ['Holdem', 'Omaha'],
  bet_type: 'NL',
  min_pot: 100,
  player_name: 'Phil Ivey',
  date_from: '2023-01-01',
};

const query: HandHistoryQuery = {
  filter,
  sort: { field: 'pot_size', direction: 'desc' },
  pagination: { limit: 20, offset: 0 },
};
```

### Calculating Statistics

```typescript
import { OpenHandHistory, HandStatistics } from '@/types';

function calculateHandStats(hand: OpenHandHistory): HandStatistics {
  const totalPot = hand.pots.reduce((sum, pot) => sum + pot.amount, 0);
  const totalRake = hand.pots.reduce((sum, pot) => sum + pot.rake, 0);

  const playersToFlop = hand.rounds
    .filter(r => r.street === 'Flop')
    .flatMap(r => r.actions.map(a => a.player_id))
    .filter((id, idx, arr) => arr.indexOf(id) === idx)
    .length;

  return {
    total_pot: totalPot,
    total_rake: totalRake,
    players_dealt: hand.players.length,
    players_to_flop: playersToFlop,
    players_to_showdown: hand.rounds.some(r => r.street === 'Showdown')
      ? hand.rounds.filter(r => r.street === 'Showdown')[0].actions.length
      : 0,
    rounds_count: hand.rounds.length,
    actions_count: hand.rounds.reduce((sum, r) => sum + r.actions.length, 0),
    winners: hand.pots.flatMap(p => p.player_wins.map(w => w.player_id)),
  };
}
```

### Immutable Hand History

```typescript
import { ReadonlyHandHistory } from '@/types';

function analyzeHand(hand: ReadonlyHandHistory) {
  // TypeScript prevents mutations
  // hand.players.push(...) // Compile error!
  // hand.rounds[0].actions = [] // Compile error!

  // Read operations work fine
  console.log('Players:', hand.players.length);
  console.log('Rounds:', hand.rounds.length);
}
```

### Validation

```typescript
import { OpenHandHistory, ValidationResult, OHHValidationError } from '@/types';

function validateHandHistory(data: unknown): ValidationResult {
  const errors: OHHValidationError[] = [];

  if (!data || typeof data !== 'object') {
    return {
      valid: false,
      errors: [{ field: 'root', message: 'Data must be an object' }],
    };
  }

  const hand = data as Partial<OpenHandHistory>;

  if (!hand.game_number) {
    errors.push({
      field: 'game_number',
      message: 'Game number is required',
      expected: 'string',
      received: hand.game_number,
    });
  }

  if (!Array.isArray(hand.players)) {
    errors.push({
      field: 'players',
      message: 'Players must be an array',
      expected: 'Player[]',
      received: hand.players,
    });
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return { valid: true, data: hand as OpenHandHistory };
}
```

## Advanced Patterns

### Generic Type Constraints

```typescript
import { Player, PlayerAction, ActionType } from '@/types';

// Generic function with type constraints
function filterActionsByType<T extends ActionType>(
  actions: PlayerAction[],
  actionType: T
): Array<PlayerAction & { action: T }> {
  return actions.filter(a => a.action === actionType) as Array<
    PlayerAction & { action: T }
  >;
}

// Usage with type inference
const betActions = filterActionsByType(allActions, 'Bet');
// Type: Array<PlayerAction & { action: 'Bet' }>
```

### Mapped Types

```typescript
import { OpenHandHistory, OHHPlayer, PlayerStats } from '@/types';

// Create stats map for all players
type PlayerStatsMap = Record<OHHPlayer['id'], PlayerStats>;

function createPlayerStatsMap(hand: OpenHandHistory): PlayerStatsMap {
  return hand.players.reduce((map, player) => {
    map[player.id] = calculatePlayerStats(hand, player.id);
    return map;
  }, {} as PlayerStatsMap);
}
```

### Discriminated Unions

```typescript
import { ActionType, PlayerAction } from '@/types';

type ActionResult =
  | { success: true; action: PlayerAction }
  | { success: false; error: string; action?: undefined };

function executeAction(action: PlayerAction): ActionResult {
  try {
    // Execute action logic
    return { success: true, action };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}
```

## Type Safety Benefits

### Compile-Time Error Detection

```typescript
import { OpenHandHistory } from '@/types';

const hand: OpenHandHistory = {
  spec_version: '1.0.0',
  game_number: 'hand123',
  // TypeScript error: Missing required fields
  // game_type, bet_limit, table_size, etc.
};
```

### Invalid State Prevention

```typescript
import { BetType, GameVariant } from '@/types';

// TypeScript prevents invalid values
const betType: BetType = 'NL'; // ✓ Valid
const invalidBet: BetType = 'LIMIT'; // ✗ Compile error

const gameType: GameVariant = 'Holdem'; // ✓ Valid
const invalidGame: GameVariant = 'Poker'; // ✗ Compile error
```

### Autocomplete & IntelliSense

All types include comprehensive JSDoc comments, providing excellent IDE support:

```typescript
import { OpenHandHistory } from '@/types';

const hand: OpenHandHistory = {
  // IDE shows all available fields with descriptions
  spec_version: '', // Hover: "Open Hand History specification version"
  game_type: '', // Autocomplete suggests: 'Holdem' | 'Omaha' | ...
};
```

## Extending Types

### Custom Fields

```typescript
import { OpenHandHistory } from '@/types';

// Add custom metadata to hand history
interface ExtendedHandHistory extends OpenHandHistory {
  metadata: {
    analyzed_at: string;
    analyzer_version: string;
    custom_tags: string[];
  };
}
```

### Custom Utility Types

```typescript
import { OpenHandHistory, PlayerAction } from '@/types';

// Create custom utility for specific use case
type NonEmptyArray<T> = [T, ...T[]];

type HandWithActions = OpenHandHistory & {
  rounds: Array<{
    street: string;
    actions: NonEmptyArray<PlayerAction>; // Ensure at least one action
  }>;
};
```

## Testing

```typescript
import { describe, it, expect } from 'vitest';
import { isOpenHandHistory, isActionType } from '@/types';

describe('Type Guards', () => {
  it('should validate hand history structure', () => {
    const validHand = {
      spec_version: '1.0.0',
      game_number: 'hand123',
      game_type: 'Holdem',
      table_size: 9,
      players: [],
      rounds: [],
      pots: [],
    };

    expect(isOpenHandHistory(validHand)).toBe(true);
  });

  it('should validate action types', () => {
    expect(isActionType('Bet')).toBe(true);
    expect(isActionType('InvalidAction')).toBe(false);
  });
});
```

## References

- [Open Hand History Specification](https://hh-specs.handhistory.org)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [TypeScript Advanced Types](https://www.typescriptlang.org/docs/handbook/2/types-from-types.html)

## Contributing

When adding new types or modifying existing ones:

1. Maintain strict type safety (no `any` types)
2. Add comprehensive JSDoc comments
3. Create type guards for runtime validation
4. Update this README with usage examples
5. Ensure backward compatibility when possible

## License

These type definitions follow the Open Hand History specification license.
