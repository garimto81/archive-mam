# Filter System Documentation

Comprehensive filter management system for the poker archive search application. Includes validation, serialization, presets, and URL synchronization.

## Overview

The filter system consists of four main modules:

- **Validation** (`validation.ts`) - Filter value validation and sanitization
- **Serialization** (`serialization.ts`) - URL/API parameter encoding/decoding
- **Presets** (`presets.ts`) - Pre-defined filter combinations
- **Hook** (`../hooks/useFilteredSearch.ts`) - Combined search + filters React hook

## Quick Start

### Basic Usage

```typescript
import { useFilteredSearch } from "@/hooks/useFilteredSearch";
import { applyPreset } from "@/lib/filters";

export default function SearchPage() {
  const search = useFilteredSearch({
    initialQuery: "",
    autoSearch: true,
    debounceMs: 300,
    syncUrl: true
  });

  return (
    <div>
      <input
        value={search.query}
        onChange={(e) => search.setQuery(e.target.value)}
        placeholder="Search poker hands..."
      />

      <button onClick={() => search.updateFilter("potSizeMin", 100)}>
        Min Pot 100 BB
      </button>

      <button onClick={() => search.updateFilters(applyPreset("highStakes"))}>
        High Stakes
      </button>

      {search.isLoading && <div>Loading...</div>}
      {search.results.map(hand => <HandCard key={hand.handId} hand={hand} />)}
      {search.error && <div>Error: {search.error.message}</div>}
    </div>
  );
}
```

### With TypeScript

```typescript
import type { SearchFilters } from "@/types/search";
import { validateFilters, sanitizeFilters } from "@/lib/filters";

const filters: SearchFilters = {
  potSizeMin: 100,
  potSizeMax: 500,
  tags: ["BLUFF", "HERO_CALL"],
  position: ["BTN", "CO"]
};

// Validate filters
const validation = validateFilters(filters);
if (!validation.isValid) {
  validation.errors.forEach(error => {
    console.error(`${error.field}: ${error.message}`);
  });
}

// Sanitize and use
const cleanFilters = sanitizeFilters(filters);
const response = await fetchSearch("river bluff", cleanFilters);
```

## Modules

### 1. Validation Module (`validation.ts`)

Comprehensive filter validation with detailed error reporting.

#### Key Functions

```typescript
// Validate entire filter object
const result = validateFilters(filters);
if (!result.isValid) {
  result.errors.forEach(error => {
    console.error(`${error.field}: ${error.code} - ${error.message}`);
  });
}

// Validate individual fields
validatePotSize(100, 500);           // OK
validateCards(["A♠", "K♥"]);         // OK
validateTags(["BLUFF", "HERO_CALL"]); // OK
validatePositions(["BTN", "CO"]);    // OK
validateTournaments(["WSOP_2024_MAIN"]); // OK

// Sanitize filters
const clean = sanitizeFilters({
  tags: ["BLUFF", "", "HERO_CALL"],  // Removes empty
  position: ["btn", "co"],            // Converts to uppercase
  heroName: "  Phil Ivey  "           // Trims whitespace
});
// Result: { tags: ["BLUFF", "HERO_CALL"], position: ["BTN", "CO"], heroName: "Phil Ivey" }
```

#### Validation Rules

| Field | Rules |
|-------|-------|
| `potSizeMin` | Non-negative number, ≤ max |
| `potSizeMax` | Non-negative number, ≥ min |
| `heroCards`, `villainCards` | Format: Rank (A,K,Q,J,T,2-9) + Suit (♠,♥,♦,♣), max 2 cards |
| `tags` | Non-empty strings, max 50 chars each, max 20 tags |
| `tournament` | Non-empty strings, max 100 chars each, max 50 tournaments |
| `position` | Valid positions (BTN, SB, BB, CO, MP, UTG, UTG+1, UTG+2) |
| `streetMin` | PREFLOP, FLOP, TURN, or RIVER |
| `resultFilter` | WIN, LOSE, or SPLIT |
| `heroName`, `villainName` | Non-empty strings, max 100 chars |
| `dateFrom`, `dateTo` | ISO 8601 format, from ≤ to |

### 2. Serialization Module (`serialization.ts`)

Convert filters to/from URL parameters and API requests.

#### Key Functions

```typescript
// URL serialization (for query parameters)
const params = filtersToQueryParams({
  potSizeMin: 100,
  tags: ["BLUFF", "HERO_CALL"]
});
// Result: URLSearchParams with "potMin=100&tags=BLUFF%2CHERO_CALL"

// URL deserialization
const params = new URLSearchParams("potMin=100&tags=BLUFF,HERO_CALL");
const filters = queryParamsToFilters(params);
// Result: { potSizeMin: 100, tags: ["BLUFF", "HERO_CALL"] }

// API serialization (snake_case for backend)
const apiParams = filtersToApiParams({
  potSizeMin: 100,
  heroName: "Phil"
});
// Result: { pot_size_min: 100, hero_name: "Phil" }

// Filter summaries
const count = getActiveFilterCount(filters);     // Number of active filters
const active = hasActiveFilters(filters);        // Boolean
const descriptions = getActiveFilterDescriptions(filters); // ["Min: 100 bb", "BLUFF, ...]
const merged = mergeFilters(base, overrides);    // Combine two filters
```

#### URL Parameter Mapping

| Filter Field | URL Param | Format |
|--------------|-----------|--------|
| `potSizeMin` | `potMin` | Number |
| `potSizeMax` | `potMax` | Number |
| `heroCards` | `heroCards` | CSV (A♠,K♥) |
| `villainCards` | `villainCards` | CSV |
| `tags` | `tags` | CSV |
| `tournament` | `tournament` | CSV |
| `position` | `position` | CSV |
| `streetMin` | `streetMin` | String |
| `resultFilter` | `resultFilter` | CSV |
| `heroName` | `heroName` | String |
| `villainName` | `villainName` | String |
| `dateFrom` | `dateFrom` | ISO 8601 |
| `dateTo` | `dateTo` | ISO 8601 |

### 3. Presets Module (`presets.ts`)

Pre-defined filter combinations for common scenarios.

#### Available Presets

**Pot Size**
- `highStakes` - Pot >= 200 BB
- `microStakes` - Pot <= 50 BB
- `smallStakes` - 50 < Pot <= 200 BB

**Actions**
- `heroCalls` - Hero calls + river decisions
- `bluffs` - Bluff + semi-bluff
- `valueHands` - Value bets + strong hands

**Results**
- `heroWins` - Hero won
- `heroLosses` - Hero lost

**Streets**
- `flopPlays` - Flop+
- `turnPlays` - Turn+
- `riverPlays` - River only

**Positions**
- `buttonPlays` - Button
- `smallBlindPlays` - Small blind

**Combined**
- `aggressiveHeroWins` - Aggressive wins
- `riverCallLosses` - River call losses
- `premiumPairPlays` - Premium pairs in high stakes

**Tournaments**
- `wsopMainEvent` - WSOP 2024 Main Event
- `wsopHighRoller` - WSOP 2024 High Roller

#### Usage

```typescript
import { applyPreset, combinePresets, getAllPresets } from "@/lib/filters";

// Apply single preset
const filters = applyPreset("highStakes");

// Combine multiple presets
const combined = combinePresets("highStakes", "heroCalls", "flopPlays");

// Get all presets
const all = getAllPresets();

// Get by category
const potSizePresets = getPresetsByCategory("pot-size");

// Get by ID
const preset = getPresetById("high-stakes");

// Track usage (for recent presets)
recordPresetUsage("highStakes");
const recent = getRecentPresets();
```

### 4. useFilteredSearch Hook (`../hooks/useFilteredSearch.ts`)

Combined React hook for search query, filters, and results management.

#### Features

- Real-time query/filter updates with debouncing
- Automatic URL synchronization
- Optional auto-search on filter change
- Pagination support
- Request cancellation
- Error handling
- Filter validation and sanitization

#### Usage

```typescript
import { useFilteredSearch } from "@/hooks/useFilteredSearch";

export function SearchComponent() {
  const search = useFilteredSearch({
    initialQuery: "Phil Ivey",
    initialFilters: { potSizeMin: 100 },
    autoSearch: true,
    debounceMs: 300,
    syncUrl: true,
    onError: (error) => console.error(error)
  });

  return (
    <div>
      {/* Query input */}
      <input
        value={search.query}
        onChange={(e) => search.setQuery(e.target.value)}
      />

      {/* Filter controls */}
      <button onClick={() => search.updateFilter("potSizeMin", 200)}>
        Min Pot 200 BB
      </button>

      {/* Clear options */}
      <button onClick={() => search.clearFilters()}>Clear Filters</button>
      <button onClick={() => search.clearAll()}>Clear All</button>

      {/* Results */}
      {search.isLoading && <Spinner />}
      {search.results.map(hand => <HandCard hand={hand} />)}

      {/* Pagination */}
      <Pagination
        current={search.currentPage}
        total={search.totalPages}
        onNext={() => search.loadNextPage()}
        onPrev={() => search.loadPreviousPage()}
        onGoTo={(page) => search.goToPage(page)}
      />

      {/* Filter info */}
      <div>Active filters: {search.activeFilterCount}</div>
      <div>Total results: {search.totalResults}</div>

      {/* Error display */}
      {search.error && <ErrorMessage error={search.error} />}
    </div>
  );
}
```

#### Return Values

```typescript
interface UseFilteredSearchReturn {
  // Search results
  results: readonly SearchResultItem[];
  totalResults: number;
  isLoading: boolean;
  error: Error | null;
  lastQuery: string;
  lastFilters: SearchFilters;
  lastResponse: SearchResponse | null;

  // Query management
  query: string;
  setQuery: (query: string) => void;

  // Filter management
  filters: SearchFilters;
  updateFilter: (key: keyof SearchFilters, value: unknown) => void;
  updateFilters: (updates: Partial<SearchFilters>) => void;
  clearFilters: () => void;
  activeFilterCount: number;
  hasFilters: boolean;

  // Actions
  search: () => Promise<void>;
  clearAll: () => void;
  cancel: () => void;

  // Pagination
  loadNextPage: () => Promise<void>;
  loadPreviousPage: () => Promise<void>;
  goToPage: (page: number) => Promise<void>;
  currentPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}
```

## Advanced Usage

### Filter Validation in Forms

```typescript
import { validateFilters, type ValidationError } from "@/lib/filters";

export function FilterForm() {
  const [filters, setFilters] = useState<SearchFilters>({});
  const [errors, setErrors] = useState<ValidationError[]>([]);

  const handleFilterChange = (key: keyof SearchFilters, value: unknown) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);

    // Validate on change
    const result = validateFilters(updated);
    setErrors(result.errors);
  };

  return (
    <div>
      <input
        type="number"
        value={filters.potSizeMin || ""}
        onChange={(e) => handleFilterChange("potSizeMin", parseFloat(e.target.value))}
      />
      {errors.find(e => e.field === "potSizeMin") && (
        <div className="error">
          {errors.find(e => e.field === "potSizeMin")?.message}
        </div>
      )}
    </div>
  );
}
```

### URL State Persistence

The hook automatically syncs with URL parameters:

```typescript
// User opens: /search/results?q=bluff&potMin=100&tags=HERO_CALL

const search = useFilteredSearch({
  syncUrl: true  // Reads from URL on mount
});

// Later, user updates filters
search.updateFilter("potSizeMax", 500);

// URL automatically updates to:
// /search/results?q=bluff&potMin=100&potMax=500&tags=HERO_CALL
```

### Combining Presets

```typescript
import { combinePresets } from "@/lib/filters";

// User selects multiple preset buttons
search.updateFilters(
  combinePresets("highStakes", "heroCalls", "riverPlays")
);

// Results in filters with:
// - potSizeMin: 200
// - tags: ["HERO_CALL", "RIVER_DECISION"]
// - streetMin: "RIVER"
```

## Testing

Comprehensive test suites included:

```bash
# Run all filter tests
npm test -- src/lib/filters

# Run specific test file
npm test -- src/lib/filters/__tests__/validation.test.ts

# Run with coverage
npm test -- src/lib/filters --coverage
```

### Test Coverage

- **Validation** (40+ tests)
  - Pot size ranges
  - Card formats
  - Tag validation
  - Position validation
  - Complete filter validation
  - Sanitization

- **Serialization** (25+ tests)
  - URL parameter encoding/decoding
  - API parameter conversion
  - Filter summaries
  - Round-trip conversion

- **Presets** (20+ tests)
  - Preset retrieval
  - Category grouping
  - Preset combination
  - Recent presets tracking
  - Preset integrity

## Performance Considerations

### Debouncing

Filter changes are debounced by default (300ms) to avoid excessive API calls:

```typescript
const search = useFilteredSearch({
  debounceMs: 500  // Longer debounce for better performance
});
```

### Caching

Search results are cached by default. Clear when needed:

```typescript
import { clearSearchCache } from "@/lib/api/search";

clearSearchCache(); // Clears all cached results
```

### Memoization

Hook results are stable between renders:

```typescript
// These functions don't change on re-render
const { updateFilter, clearFilters, search } = useFilteredSearch();

// Can safely use in useEffect dependencies
useEffect(() => {
  search();
}, [search]);
```

## Error Handling

### Validation Errors

```typescript
const result = validateFilters(filters);

if (!result.isValid) {
  result.errors.forEach(error => {
    // error.field: "potSizeMin"
    // error.code: "RANGE_INVALID"
    // error.message: "Pot size minimum must be less than or equal to maximum"
    // error.value: { min: 500, max: 100 }
  });
}
```

### Search Errors

```typescript
const search = useFilteredSearch({
  onError: (error) => {
    if (error.message.includes("Filter")) {
      console.log("Filter validation error");
    } else if (error.message.includes("Network")) {
      console.log("Network error");
    } else {
      console.log("Unknown error");
    }
  }
});
```

## API Integration

The filter system is already integrated with the search API:

```typescript
// In lib/api/search.ts
import { validateFilters, sanitizeFilters } from "@/lib/filters/validation";

export async function fetchSearch(query, filters?, options?) {
  // Filters are automatically validated and sanitized
  const validation = validateFilters(filters);
  if (!validation.isValid) {
    throw new ValidationError(`Invalid filters: ${validation.errors.map(e => e.message).join("; ")}`);
  }

  const cleanFilters = sanitizeFilters(filters || {});
  // ... rest of API call
}
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- iOS Safari 14+

Uses native APIs:
- `URLSearchParams`
- `AbortController`
- `localStorage` (for recent presets)

## Troubleshooting

### Filters not persisting in URL

Ensure `syncUrl: true` in hook options (it's the default).

### Validation error on valid filters

Check the specific error code in `ValidationError.code` for details. See validation rules table above.

### Auto-search not triggering

Verify:
1. `autoSearch: true` is set
2. Query is not empty
3. Debounce timer hasn't expired (check `debounceMs`)

### Presets not combining correctly

Note that `combinePresets` merges array fields using Set (removes duplicates) and overrides scalar fields with the last preset's value.

## Contributing

When adding new filters or presets:

1. Add validation rules in `validation.ts`
2. Add serialization logic in `serialization.ts`
3. Add tests for both
4. Update this README with examples
5. Document any new validation error codes

## Related Files

- `src/lib/api/search.ts` - API integration
- `src/lib/utils/url.ts` - URL utilities (deprecated, use serialization.ts)
- `src/types/search.ts` - TypeScript types
- `src/hooks/useFilteredSearch.ts` - Main hook
