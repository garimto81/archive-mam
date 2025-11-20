# TypeScript Types Quick Reference

## Import Everything

```typescript
import {
  // Autocomplete
  AutocompleteResponse,
  AutocompleteError,
  AutocompleteState,

  // Hand
  Hand,
  HandFilters,

  // Errors
  ValidationError,
  RateLimitError,

  // Type Guards
  isAutocompleteError,
  isValidationError
} from "@/types";
```

## Common Patterns

### 1. Autocomplete Component State

```typescript
const [state, setState] = useState<AutocompleteState>({
  suggestions: [],
  isLoading: false,
  error: null,
  source: "bigquery_cache",
  responseTimeMs: 0
});
```

### 2. API Call with Error Handling

```typescript
try {
  const response = await fetch("/api/autocomplete?q=Phil");
  const data: AutocompleteResponse = await response.json();

  setState({
    suggestions: data.suggestions.map(text => ({ text })),
    isLoading: false,
    error: null,
    source: data.source,
    responseTimeMs: data.response_time_ms
  });
} catch (error) {
  if (isValidationError(error)) {
    setState(prev => ({ ...prev, error }));
  }
}
```

### 3. Validation Before API Call

```typescript
function validateQuery(query: string): void {
  if (query.length < 2) {
    throw new ValidationError(
      "Query must be at least 2 characters",
      "query"
    );
  }
}
```

### 4. Rate Limit Handling

```typescript
catch (error) {
  if (isRateLimitError(error)) {
    const retryDate = error.getRetryAfterDate();
    console.log(`Retry after: ${retryDate.toLocaleTimeString()}`);
  }
}
```

### 5. Paginated Response

```typescript
const response: PaginatedResponse<Hand> = await fetchHands({ page: 1 });

console.log(`Showing ${response.items.length} of ${response.total} hands`);
console.log(`Page ${response.page}, has next: ${response.has_next}`);
```

### 6. Hand Filters

```typescript
const filters: HandFilters = {
  minPotBb: 100,
  streets: ["RIVER"],
  tags: ["HERO_CALL"],
  heroName: "Junglemann"
};
```

### 7. Type Guard Pattern

```typescript
function handleResponse(
  response: AutocompleteResponse | AutocompleteError
): void {
  if (isAutocompleteError(response)) {
    // Handle error
    console.error(response.message);
  } else {
    // Handle success
    console.log(response.suggestions);
  }
}
```

## Type Reference

### AutocompleteSource

```typescript
type AutocompleteSource =
  | "bigquery_cache"  // Fast (<10ms)
  | "vertex_ai"       // Slower (<100ms)
  | "hybrid";         // Combined
```

### HandAction

```typescript
type HandAction =
  | "fold"
  | "call"
  | "raise"
  | "all-in"
  | "check";
```

### Street

```typescript
type Street =
  | "PREFLOP"
  | "FLOP"
  | "TURN"
  | "RIVER";
```

### HandResult

```typescript
type HandResult =
  | "WIN"
  | "LOSE"
  | "SPLIT";
```

## Error Reference

| Class | HTTP | When to Use |
|-------|------|-------------|
| `ValidationError` | 422 | Invalid input |
| `RateLimitError` | 429 | Too many requests |
| `NetworkError` | - | Connection failed |
| `ServerError` | 500 | Server error |
| `TimeoutError` | - | Request timeout |
| `NotFoundError` | 404 | Resource not found |

## Type Guards Cheat Sheet

```typescript
// Autocomplete
isAutocompleteError(response) // → response is AutocompleteError
hasSuggestionScore(suggestion) // → suggestion has score

// Hand
isHand(obj) // → obj is Hand

// API
isApiError(response) // → response is ApiError
isPaginatedResponse(response) // → response is PaginatedResponse

// Errors
isCustomError(error) // → error is CustomError
isValidationError(error) // → error is ValidationError
isRateLimitError(error) // → error is RateLimitError
isNetworkError(error) // → error is NetworkError
```

## Full Type Definitions

### AutocompleteResponse

```typescript
interface AutocompleteResponse {
  readonly suggestions: readonly string[];
  readonly query: string;
  readonly source: AutocompleteSource;
  readonly response_time_ms: number;
  readonly total?: number;
}
```

### Hand

```typescript
interface Hand {
  readonly hand_id: string;
  readonly tournament_id: string;
  readonly hand_number: number;
  readonly timestamp: string;
  readonly hero_name: string;
  readonly hero_position: string;
  readonly hero_stack_bb: number;
  readonly hero_action: HandAction;
  readonly villain_name: string;
  readonly villain_position: string;
  readonly villain_stack_bb: number;
  readonly street: Street;
  readonly pot_bb: number;
  readonly result: HandResult;
  readonly tags: readonly string[];
  readonly hand_type: string;
  readonly description: string;
  readonly video_url: string;
  readonly video_start_time: number;
  readonly video_end_time: number;
  readonly thumbnail_url: string;
}
```

### ApiRequestOptions

```typescript
interface ApiRequestOptions {
  readonly method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  readonly headers?: Readonly<Record<string, string>>;
  readonly body?: unknown;
  readonly timeout?: number;
  readonly signal?: AbortSignal;
  readonly retries?: number;
  readonly retryDelay?: number;
}
```

## Tips

1. **Always import from `@/types`** - Don't import from individual files
2. **Use type guards for runtime checks** - Safer than `as` assertions
3. **Readonly arrays prevent bugs** - Creates new array instead of mutating
4. **Error classes include helpful methods** - Use `toJSON()` for logging
5. **JSDoc in your editor** - Hover over types for documentation
