# M6 Web UI Development Guide

Complete guide for developing, testing, and deploying the POKER-BRAIN Web UI.

---

## Table of Contents

1. [Setup](#setup)
2. [Development Workflow](#development-workflow)
3. [Component Development](#component-development)
4. [API Route Development](#api-route-development)
5. [Testing Strategy](#testing-strategy)
6. [Deployment](#deployment)
7. [Best Practices](#best-practices)

---

## Setup

### 1. Prerequisites

```bash
# Check Node.js version (18+ required)
node --version  # Should be v18.x.x or higher

# Check npm version (9+ required)
npm --version   # Should be 9.x.x or higher
```

### 2. Install Dependencies

```bash
cd modules/m6-web-ui
npm install
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env.development

# Edit environment variables
# NEXT_PUBLIC_M3_API_URL=http://localhost:8003/v1
# NEXT_PUBLIC_M4_API_URL=http://localhost:8004/v1
# NEXT_PUBLIC_M5_API_URL=http://localhost:8005/v1
```

### 4. Start Backend Services

```bash
# Terminal 1: M3 Timecode Validation
cd modules/m3-timecode-validation
python -m app.api
# Running on http://localhost:8003

# Terminal 2: M4 RAG Search
cd modules/m4-rag-search
python -m app.api
# Running on http://localhost:8004

# Terminal 3: M5 Clipping
cd modules/m5-clipping
python app/api.py
# Running on http://localhost:8005
```

### 5. Start Web UI

```bash
# Terminal 4: M6 Web UI
cd modules/m6-web-ui
npm run dev
# Running on http://localhost:3000
```

---

## Development Workflow

### Hot Reload

Next.js provides automatic hot reload for:
- Pages (`app/**/*.tsx`)
- Components (`components/**/*.tsx`)
- API routes (`app/api/**/route.ts`)
- Styles (`app/globals.css`, component styles)

Changes are reflected instantly without server restart.

### Folder Structure Convention

```
app/
├── (pages)/              # Page routes
│   ├── page.tsx          # Home page (/)
│   ├── search/
│   │   └── page.tsx      # Search page (/search)
│   └── hand/[hand_id]/
│       └── page.tsx      # Dynamic hand detail (/hand/wsop2024_me_d3_h154)
└── api/                  # BFF API routes
    ├── search/
    │   └── route.ts      # API route (/api/search)
    └── [dynamic]/
        └── route.ts      # Dynamic API route

components/
├── ui/                   # Reusable UI primitives (shadcn/ui)
│   ├── button.tsx
│   └── card.tsx
└── (feature)/            # Feature-specific components
    ├── SearchBar.tsx
    └── HandCard.tsx

lib/
├── types.ts              # Shared TypeScript types
├── api-config.ts         # API endpoint configuration
├── api-client.ts         # Fetch wrappers
└── utils.ts              # Utility functions
```

### Type Safety

All components and functions are fully typed with TypeScript:

```typescript
// Define props interface
interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  defaultValue?: string;
}

// Type component
export function SearchBar({ onSearch, placeholder, defaultValue }: SearchBarProps) {
  // Implementation
}
```

---

## Component Development

### 1. Create New Component

```bash
# Create component file
touch components/MyComponent.tsx
```

```typescript
// components/MyComponent.tsx
'use client';  // Required for client-side interactivity

import * as React from 'react';
import { Button } from '@/components/ui/button';

interface MyComponentProps {
  title: string;
  onClick?: () => void;
}

export function MyComponent({ title, onClick }: MyComponentProps) {
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <h2>{title}</h2>
      <p>Count: {count}</p>
      <Button onClick={() => setCount(count + 1)}>
        Increment
      </Button>
      {onClick && (
        <Button variant="outline" onClick={onClick}>
          Custom Action
        </Button>
      )}
    </div>
  );
}
```

### 2. Use shadcn/ui Components

We use shadcn/ui for consistent, accessible UI primitives:

```typescript
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

// Usage
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    <Input placeholder="Search..." />
    <Button>Search</Button>
    <Badge>New</Badge>
  </CardContent>
</Card>
```

### 3. Styling with Tailwind CSS

```typescript
// Use cn() utility for conditional classes
import { cn } from '@/lib/utils';

<div className={cn(
  'base-class',
  isActive && 'active-class',
  variant === 'primary' ? 'primary-variant' : 'secondary-variant'
)}>
  Content
</div>
```

### 4. State Management

**Local State** (useState):
```typescript
const [query, setQuery] = React.useState('');
```

**Shared State** (Context API):
```typescript
// contexts/SearchContext.tsx
const SearchContext = React.createContext<SearchContextType | null>(null);

export function SearchProvider({ children }: { children: React.ReactNode }) {
  const [results, setResults] = React.useState([]);
  return (
    <SearchContext.Provider value={{ results, setResults }}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  const context = React.useContext(SearchContext);
  if (!context) throw new Error('useSearch must be used within SearchProvider');
  return context;
}
```

**Server State** (SWR):
```typescript
import useSWR from 'swr';

function useHandDetail(handId: string) {
  const { data, error, isLoading } = useSWR(
    `/api/hand/${handId}`,
    (url) => fetch(url).then(r => r.json())
  );

  return {
    hand: data,
    isLoading,
    error
  };
}
```

---

## API Route Development

### 1. Create BFF API Route

```typescript
// app/api/my-endpoint/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/lib/api-config';

export async function GET(req: NextRequest) {
  try {
    // Extract query parameters
    const searchParams = req.nextUrl.searchParams;
    const id = searchParams.get('id');

    // Validate input
    if (!id) {
      return NextResponse.json(
        { error: { code: 'INVALID_REQUEST', message: 'id is required' } },
        { status: 400 }
      );
    }

    // Proxy to upstream service
    const response = await fetch(`${API_ENDPOINTS.M4_SEARCH}/resource/${id}`);

    if (!response.ok) {
      throw new Error('Upstream service error');
    }

    const data = await response.json();

    // Return response
    return NextResponse.json(data);
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'An error occurred' } },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Proxy POST request
    const response = await fetch(`${API_ENDPOINTS.M4_SEARCH}/resource`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'An error occurred' } },
      { status: 500 }
    );
  }
}
```

### 2. Dynamic API Routes

```typescript
// app/api/hand/[hand_id]/route.ts
export async function GET(
  req: NextRequest,
  { params }: { params: { hand_id: string } }
) {
  const handId = params.hand_id;
  // Use handId in logic
}
```

### 3. Error Handling Pattern

```typescript
try {
  // Main logic
} catch (error) {
  console.error('API error:', error);

  // Determine error type
  if (error instanceof ApiClientError) {
    return NextResponse.json(
      { error: { code: error.code, message: error.message } },
      { status: error.statusCode }
    );
  }

  // Generic error
  return NextResponse.json(
    { error: { code: 'INTERNAL_ERROR', message: 'An error occurred' } },
    { status: 500 }
  );
}
```

---

## Testing Strategy

### 1. Unit Tests (Jest)

```bash
# Run unit tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

**Example test**:
```typescript
// __tests__/components/SearchBar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchBar } from '@/components/SearchBar';

describe('SearchBar', () => {
  it('renders search input', () => {
    render(<SearchBar onSearch={jest.fn()} />);
    const input = screen.getByPlaceholderText(/search/i);
    expect(input).toBeInTheDocument();
  });

  it('calls onSearch when submitted', () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test query' } });

    const button = screen.getByRole('button', { name: /search/i });
    fireEvent.click(button);

    expect(onSearch).toHaveBeenCalledWith('test query');
  });
});
```

### 2. E2E Tests (Playwright)

```bash
# Run E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Install browsers (first time)
npx playwright install
```

**Example E2E test**:
```typescript
// tests/e2e/search-flow.spec.ts
import { test, expect } from '@playwright/test';

test('complete search flow', async ({ page }) => {
  // Navigate to home
  await page.goto('/');

  // Search for hand
  await page.fill('input[placeholder*="Search"]', 'Tom Dwan bluff');
  await page.click('button:has-text("Search")');

  // Verify results page
  await expect(page).toHaveURL(/\/search\?q=Tom%20Dwan%20bluff/);

  // Wait for results
  await page.waitForSelector('[data-testid="hand-card"]');

  // Click first result
  await page.click('[data-testid="hand-card"]', { first: true });

  // Verify hand detail page
  await expect(page).toHaveURL(/\/hand\//);
});
```

### 3. Manual Testing Checklist

**Search Flow**:
- [ ] Home page loads
- [ ] Search bar accepts input
- [ ] Autocomplete appears (if available)
- [ ] Search results display
- [ ] Hand cards show metadata
- [ ] Click hand navigates to detail

**Hand Detail**:
- [ ] Video player loads
- [ ] Video controls work (play, pause, seek)
- [ ] Download button works
- [ ] Favorite button works
- [ ] Back button works

**Favorites**:
- [ ] Favorites list loads
- [ ] Remove favorite works
- [ ] Empty state displays

**Downloads**:
- [ ] Download history loads
- [ ] Download status polling works
- [ ] Download URL works when completed

**Admin**:
- [ ] Validation stats load
- [ ] Stats refresh automatically

---

## Deployment

### Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

**Environment Variables (Vercel Dashboard)**:
```
NEXT_PUBLIC_POKER_ENV=production
NEXT_PUBLIC_M3_API_URL=https://timecode-validation-service-prod.run.app/v1
NEXT_PUBLIC_M4_API_URL=https://rag-search-service-prod.run.app/v1
NEXT_PUBLIC_M5_API_URL=https://clipping-service-prod.run.app/v1
```

### Docker Deployment

```bash
# Build image
docker build \
  --build-arg NEXT_PUBLIC_M3_API_URL=https://... \
  --build-arg NEXT_PUBLIC_M4_API_URL=https://... \
  --build-arg NEXT_PUBLIC_M5_API_URL=https://... \
  -t m6-web-ui:1.0.0 .

# Test locally
docker run -p 3000:3000 m6-web-ui:1.0.0

# Push to registry
docker tag m6-web-ui:1.0.0 gcr.io/YOUR_PROJECT/m6-web-ui:1.0.0
docker push gcr.io/YOUR_PROJECT/m6-web-ui:1.0.0

# Deploy to Cloud Run
gcloud run deploy m6-web-ui \
  --image gcr.io/YOUR_PROJECT/m6-web-ui:1.0.0 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Best Practices

### 1. Code Organization

- **Group by feature** (not by type): `components/search/`, `components/favorites/`
- **Co-locate tests**: `SearchBar.tsx` + `SearchBar.test.tsx`
- **Use barrel exports**: `components/index.ts` exports all components

### 2. Performance

- **Use `React.memo`** for expensive components
- **Lazy load routes**: Already handled by Next.js App Router
- **Debounce API calls**: Use `debounce()` utility for autocomplete
- **Image optimization**: Use Next.js `<Image>` component

### 3. Accessibility

- **Use semantic HTML**: `<nav>`, `<main>`, `<article>`, `<section>`
- **Add ARIA labels**: `aria-label`, `aria-describedby`
- **Keyboard navigation**: All interactive elements focusable
- **Color contrast**: Minimum 4.5:1 ratio

### 4. Error Handling

- **User-friendly messages**: Avoid technical jargon
- **Retry logic**: Provide retry button on errors
- **Loading states**: Show skeleton/spinner during async operations
- **Error boundaries**: Catch React errors gracefully

### 5. Git Workflow

```bash
# Create feature branch
git checkout -b feature/search-filters

# Make changes
git add .
git commit -m "feat: Add advanced search filters"

# Push and create PR
git push origin feature/search-filters
```

**Commit Message Format**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting, no code change
- `refactor:` Code restructure
- `test:` Add tests
- `chore:` Build/config changes

---

## Common Issues & Solutions

### Issue: Port 3000 already in use

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3001 npm run dev
```

### Issue: Module not found errors

```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

### Issue: TypeScript errors

```bash
# Check types without running
npm run type-check

# Generate types
npm run build
```

### Issue: Hydration errors

**Cause**: Server/client HTML mismatch

**Solution**: Ensure no browser-only code in SSR components
```typescript
// Bad
const isClient = typeof window !== 'undefined';

// Good
'use client';  // Mark as client component
```

---

**Happy Coding!** 🚀
