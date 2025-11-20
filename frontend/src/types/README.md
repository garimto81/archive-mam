# Type Definitions

This directory contains all TypeScript type definitions for the poker archive search system.

## Overview

The type system is organized into seven main modules:

1. **search.ts** - Natural language search types (NEW)
2. **video.ts** - Video metadata and playback types (NEW)
3. **hand.ts** - Poker hand data structures (Enhanced)
4. **api.ts** - Common API types (errors, pagination, requests)
5. **autocomplete.ts** - Autocomplete API types and state management
6. **errors.ts** - Custom error classes for type-safe error handling
7. **index.ts** - Central export hub for all types

All types are re-exported through `index.ts` for convenient importing.

**Total**: 1,620+ lines of code | 28+ interfaces | 14+ utility functions | 92+ exports

## Usage

### Basic Import

```typescript
import {
  // Search
  SearchQuery,
  SearchRequest,
  SearchResponse,

  // Hand
  Hand,
  HandDetails,
  Position,

  // Video
  VideoMetadata,
  VideoPlayerState,

  // Utilities
  createSearchQuery,
  isSearchResponse,
  isHandDetails,

  // API & Error
  AutocompleteResponse,
  ApiError,
  ValidationError
} from "@/types";
```

### Search Types (NEW)

```typescript
import {
  SearchQuery,
  SearchRequest,
  SearchResponse,
  SearchFilters,
  SearchOptions,
  createSearchQuery,
  isSearchResponse
} from "@/types";

// Create validated search query (2-500 characters)
const query = createSearchQuery("Phil Ivey river call");

// Build search request with filters
const request: SearchRequest = {
  query,
  filters: {
    potSizeMin: 100,
    potSizeMax: 500,
    tags: ["HERO_CALL", "RIVER"],
    position: ["BTN", "CO"],
    resultFilter: ["WIN"],
    dateFrom: "2024-07-01",
    dateTo: "2024-07-31",
  },
  options: {
    limit: 20,
    offset: 0,
    sortBy: "relevance",
    sortOrder: "desc",
  },
};

// Execute search and validate response
const response = await api.search(request);
if (isSearchResponse(response)) {
  console.log(`Found ${response.total} results in ${response.queryTimeMs}ms`);
  response.results.forEach(item => {
    console.log(`${item.hero_name} vs ${item.villain_name}: ${item.score}`);
  });
}
```

### Video Types (NEW)

```typescript
import {
  VideoMetadata,
  VideoPlayerState,
  HandTimelineMarker,
  isVideoMetadata,
  getUrlTimeRemaining
} from "@/types";

// Video metadata with GCS signed URL
const metadata: VideoMetadata = {
  videoUrl: "https://storage.googleapis.com/...",
  thumbnailUrl: "https://...",
  startTime: 3421.5,
  endTime: 3482.0,
  durationSeconds: 60.5,
  expiresAt: "2024-02-18T10:30:00Z",
  format: "mp4",
  resolution: "1080p",
};

// Check URL expiration
const secondsRemaining = getUrlTimeRemaining(metadata.expiresAt);
if (secondsRemaining < 300) {
  // Less than 5 minutes, refresh soon
  const newUrl = await api.refreshVideoUrl(handId);
}

// Player state for video controls
const [playerState, setPlayerState] = useState<VideoPlayerState>({
  isPlaying: false,
  currentTime: 0,
  duration: metadata.durationSeconds,
  volume: 0.8,
  isMuted: false,
  isFullscreen: false,
  playbackRate: 1.0,
});

// Timeline markers for streets
const markers: HandTimelineMarker[] = [
  { street: "PREFLOP", timestamp: 3421.5, label: "Preflop", color: "#E5E7EB" },
  { street: "FLOP", timestamp: 3435.2, label: "Flop", color: "#F3E8FF" },
  { street: "TURN", timestamp: 3455.0, label: "Turn", color: "#E0E7FF" },
  { street: "RIVER", timestamp: 3465.8, label: "River", color: "#DBEAFE" },
];
```

### Hand Details Types (NEW)

```typescript
import {
  HandDetails,
  PlayerInfo,
  StreetAction,
  Action,
  Position,
  isHandDetails
} from "@/types";

// Complete hand with street-by-street breakdown
const details: HandDetails = {
  // Basic fields (inherited from Hand)
  hand_id: "wsop_2024_main_event_hand_3421",
  tournament_id: "wsop_2024_main_event",
  hand_number: 3421,

  // Extended fields
  hero: {
    name: "Junglemann",
    position: Position.BTN,
    stackBB: 87.5,
    cards: ["A♠", "K♥"],
  } as PlayerInfo,

  villain: {
    name: "Phil Ivey",
    position: Position.BB,
    stackBB: 145.5,
    cards: ["Q♠", "J♥"],
  } as PlayerInfo,

  // Street-by-street action
  streets: [
    {
      street: "PREFLOP",
      actions: [
        { player: "hero", actionType: "raise", amount: 25, timestamp: 0 },
        { player: "villain", actionType: "call", amount: 25, timestamp: 1.2 },
      ],
      potBB: 50,
    } as StreetAction,
    {
      street: "FLOP",
      actions: [
        { player: "villain", actionType: "check", timestamp: 2.5 },
        { player: "hero", actionType: "bet", amount: 30, timestamp: 3.1 },
        { player: "villain", actionType: "call", amount: 30, timestamp: 4.0 },
      ],
      communityCards: ["K♠", "Q♥", "9♣"],
      potBB: 110,
    } as StreetAction,
  ],
  duration_seconds: 60.5,
  source: "ati-analysis",
};

if (isHandDetails(details)) {
  // Safe to access street-by-street data
  details.streets.forEach(street => {
    console.log(`${street.street}: ${street.actions.length} actions`);
    street.actions.forEach(action => {
      console.log(`  ${action.player}: ${action.actionType} @ ${action.timestamp}s`);
    });
  });
}
```

### Autocomplete Types

```typescript
import { AutocompleteResponse, AutocompleteState } from "@/types";

// API response
const response: AutocompleteResponse = {
  suggestions: ["Phil Ivey", "Phil Hellmuth"],
  query: "Phil",
  source: "bigquery_cache",
  response_time_ms: 45,
  total: 2
};

// Component state
const [state, setState] = useState<AutocompleteState>({
  suggestions: [],
  isLoading: false,
  error: null,
  source: "bigquery_cache",
  responseTimeMs: 0
});
```

### Hand Types

```typescript
import { Hand, HandFilters } from "@/types";

// Full hand data
const hand: Hand = {
  hand_id: "wsop_2024_main_event_hand_3421",
  tournament_id: "wsop_2024_main_event",
  // ... other fields
};

// Search filters
const filters: HandFilters = {
  minPotBb: 100,
  streets: ["RIVER"],
  tags: ["HERO_CALL"]
};
```

### Error Handling

```typescript
import {
  ValidationError,
  RateLimitError,
  isValidationError,
  isRateLimitError
} from "@/types";

try {
  if (query.length < 2) {
    throw new ValidationError("Query must be at least 2 characters");
  }
  // ... API call
} catch (error) {
  if (isValidationError(error)) {
    console.error(`Validation failed: ${error.message}`);
  } else if (isRateLimitError(error)) {
    console.error(`Rate limited. Retry after ${error.retryAfterSeconds}s`);
  }
}
```

### API Types

```typescript
import { ApiRequestOptions, PaginatedResponse } from "@/types";

// Request configuration
const options: ApiRequestOptions = {
  method: "POST",
  timeout: 5000,
  retries: 3
};

// Paginated response
const response: PaginatedResponse<Hand> = {
  items: [...],
  total: 150,
  page: 1,
  page_size: 20,
  has_next: true,
  has_previous: false
};
```

## Type Guards

Type guards are provided for runtime type checking:

### Autocomplete Type Guards

```typescript
import { isAutocompleteError, hasSuggestionScore } from "@/types";

// Check if response is an error
if (isAutocompleteError(response)) {
  console.error(response.message);
}

// Check if suggestion has a score
if (hasSuggestionScore(suggestion)) {
  console.log(`Score: ${suggestion.score}`);
}
```

### Error Type Guards

```typescript
import {
  isCustomError,
  isValidationError,
  isRateLimitError,
  isNetworkError
} from "@/types";

catch (error) {
  if (isCustomError(error)) {
    console.log(`Error code: ${error.code}`);
  }
}
```

### API Type Guards

```typescript
import { isApiError, isPaginatedResponse } from "@/types";

if (isApiError(response)) {
  console.error(`HTTP ${response.statusCode}: ${response.message}`);
}

if (isPaginatedResponse(response)) {
  console.log(`Page ${response.page} of ${Math.ceil(response.total / response.page_size)}`);
}
```

## Custom Error Classes

All error classes extend `CustomError` and include:
- `code`: Machine-readable error code
- `statusCode`: Optional HTTP status code
- `toJSON()`: Serialize error to JSON
- `toString()`: String representation

### Available Error Classes

| Class | HTTP Status | Use Case |
|-------|-------------|----------|
| `ValidationError` | 422 | Input validation failures |
| `RateLimitError` | 429 | Rate limit exceeded |
| `NetworkError` | - | Network connectivity issues |
| `ServerError` | 500 | Server-side errors |
| `TimeoutError` | - | Request timeouts |
| `NotFoundError` | 404 | Resource not found |
| `AuthenticationError` | 401 | Authentication required |
| `AuthorizationError` | 403 | Insufficient permissions |

### Error Class Examples

```typescript
// Validation with field information
throw new ValidationError("Invalid email format", "email");

// Rate limit with retry duration
throw new RateLimitError("Too many requests", 60);

// Server error with details
throw new ServerError("Database query failed", 500, "Connection timeout");

// Timeout with duration
throw new TimeoutError("Request timed out", 5000);

// Not found with resource ID
throw new NotFoundError("Hand not found", "hand-123");
```

## Type Safety Features

### Readonly Arrays

All array types are marked as `readonly` to prevent accidental mutations:

```typescript
const response: AutocompleteResponse = {
  suggestions: ["Phil Ivey"],
  // ...
};

// ❌ TypeScript error: Cannot assign to 'suggestions' because it is a read-only property
response.suggestions.push("New item");

// ✅ Correct: Create new array
const newSuggestions = [...response.suggestions, "New item"];
```

### Strict Null Checks

All optional fields are explicitly typed with `| undefined`:

```typescript
interface Hand {
  hand_id: string;           // Required
  description: string;       // Required
  total?: number;           // Optional (number | undefined)
}
```

### Branded Types (Future Enhancement)

For additional type safety, consider branded types:

```typescript
type HandId = string & { __brand: "HandId" };
type TournamentId = string & { __brand: "TournamentId" };

// Prevents mixing different ID types
function getHand(handId: HandId): Hand { ... }
function getTournament(tournamentId: TournamentId): Tournament { ... }

const handId = "hand-123" as HandId;
getHand(handId); // ✅ OK
getTournament(handId); // ❌ Type error
```

## File Organization

```
types/
├── search.ts         # Search types (NEW) - 493 LOC
│   ├── SearchQuery, SearchRequest, SearchResponse
│   ├── SearchFilters, SearchOptions
│   ├── SearchResultItem, PaginationMeta
│   └── Type guards & event types
├── video.ts          # Video types (NEW) - 503 LOC
│   ├── VideoMetadata, VideoPlayerState
│   ├── HandTimelineMarker, VideoQualitySettings
│   └── Playback position/range, error handling
├── hand.ts           # Poker hand data (Enhanced) - 478 LOC
│   ├── Hand, HandDetails, HandFilters
│   ├── Position enum, PlayerInfo
│   ├── Action, StreetAction
│   └── Type guards for hand data
├── api.ts            # API infrastructure - 246 LOC
│   ├── ApiError, ApiResponse, ApiRequestOptions
│   └── PaginatedResponse, SortParams
├── autocomplete.ts   # Autocomplete API - 232 LOC
│   ├── AutocompleteResponse, AutocompleteOptions
│   └── AutocompleteState, AutocompleteCacheEntry
├── errors.ts         # Error classes - 426 LOC
│   ├── CustomError (base class)
│   ├── ValidationError, RateLimitError
│   ├── NetworkError, ServerError, TimeoutError
│   └── NotFoundError, AuthenticationError, AuthorizationError
├── index.ts          # Central export hub - 146 LOC
│   └── All exports from above modules
├── __test__.ts       # Type system test - 300+ LOC
└── README.md         # This file

TOTALS:
├── 1,620+ lines of code
├── 28+ interfaces & types
├── 14+ utility functions
└── 92+ exports
```

## TypeScript Configuration

This project uses strict TypeScript configuration:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

## Testing

The `__test__.ts` file verifies:
- ✅ All types compile without errors
- ✅ Type guards work correctly
- ✅ Readonly arrays prevent mutations
- ✅ All exports are accessible
- ✅ Type inference works as expected

Run type checking:
```bash
npm run type-check
# or
npx tsc --noEmit
```

## Contributing

When adding new types:

1. **Add JSDoc comments** for all public interfaces/types
2. **Use `readonly`** for immutable properties
3. **Export from index.ts** for consistency
4. **Add type guards** if runtime checks are needed
5. **Update __test__.ts** to verify new types
6. **Run type-check** to ensure no errors

## Related Documentation

- [Backend API Documentation](../../backend/README.md)
- [ATI Metadata Schema](../../../ati_metadata_schema.json)
- [Architecture Decision](../../../issues/ISSUE-004-final-architecture.md)
