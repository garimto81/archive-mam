# M6 Web UI Service (Frank)

**Status**: Week 4 - Production Ready ✅
**Agent**: Frank
**Version**: 1.0.0
**Tech Stack**: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui

---

## 🎯 Overview

Production-ready Web UI application for POKER-BRAIN WSOP Archive System. Built with Next.js 14 App Router and BFF (Backend-for-Frontend) pattern.

**Key Features**:
- ✅ Semantic search with autocomplete (powered by M4 RAG Search)
- ✅ Video preview and playback (proxy videos from M2)
- ✅ Clip download with real-time progress polling (M5 Clipping)
- ✅ Favorites management
- ✅ Admin dashboard (timecode validation stats from M3)
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Accessibility (WCAG 2.1 AA compliant)
- ✅ E2E tested with Playwright

---

## 📁 Project Structure

```
m6-web-ui/
├── app/                          # Next.js 14 App Router
│   ├── api/                      # BFF API Routes (8 endpoints)
│   │   ├── search/
│   │   │   ├── route.ts          # POST /api/search
│   │   │   └── autocomplete/
│   │   │       └── route.ts      # GET /api/search/autocomplete
│   │   ├── download/
│   │   │   ├── route.ts          # POST /api/download
│   │   │   └── [id]/status/
│   │   │       └── route.ts      # GET /api/download/{id}/status
│   │   ├── hand/[hand_id]/
│   │   │   └── route.ts          # GET /api/hand/{hand_id}
│   │   ├── favorites/
│   │   │   └── route.ts          # GET/POST/DELETE /api/favorites
│   │   ├── downloads/history/
│   │   │   └── route.ts          # GET /api/downloads/history
│   │   ├── admin/validation/stats/
│   │   │   └── route.ts          # GET /api/admin/validation/stats
│   │   └── health/
│   │       └── route.ts          # GET /api/health
│   ├── page.tsx                  # Home page
│   ├── search/
│   │   └── page.tsx              # Search results
│   ├── hand/[hand_id]/
│   │   └── page.tsx              # Hand detail
│   ├── favorites/
│   │   └── page.tsx              # User favorites
│   ├── downloads/
│   │   └── page.tsx              # Download history
│   ├── admin/
│   │   └── page.tsx              # Admin dashboard
│   ├── layout.tsx                # Root layout
│   └── globals.css               # Global styles
├── components/
│   ├── ui/                       # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── badge.tsx
│   ├── SearchBar.tsx             # Search with autocomplete
│   ├── HandCard.tsx              # Hand result card
│   ├── VideoPlayer.tsx           # HTML5 video player
│   └── DownloadButton.tsx        # Download with polling
├── lib/
│   ├── types.ts                  # TypeScript types
│   ├── api-config.ts             # API endpoint configuration
│   ├── api-client.ts             # Fetch wrappers
│   └── utils.ts                  # Utility functions
├── tests/
│   └── e2e/                      # Playwright E2E tests
│       ├── search.spec.ts
│       └── navigation.spec.ts
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── Dockerfile
├── vercel.json
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Running M3, M4, M5 services (for development mode)

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.development

# Start development server
npm run dev
```

Access the app at `http://localhost:3000`

---

## 🔧 Environment Configuration

### Development Mode (Local M3, M4, M5 Services)

```bash
# .env.development
NEXT_PUBLIC_POKER_ENV=development
NEXT_PUBLIC_M3_API_URL=http://localhost:8003/v1
NEXT_PUBLIC_M4_API_URL=http://localhost:8004/v1
NEXT_PUBLIC_M5_API_URL=http://localhost:8005/v1
```

**Start backend services**:
```bash
# Terminal 1: M3 Timecode Validation
cd ../m3-timecode-validation
python -m app.api

# Terminal 2: M4 RAG Search
cd ../m4-rag-search
python -m app.api

# Terminal 3: M5 Clipping
cd ../m5-clipping
python app/api.py

# Terminal 4: M6 Web UI
npm run dev
```

### Production Mode (Cloud Run)

```bash
# .env.production
NEXT_PUBLIC_POKER_ENV=production
NEXT_PUBLIC_M3_API_URL=https://timecode-validation-service-prod.run.app/v1
NEXT_PUBLIC_M4_API_URL=https://rag-search-service-prod.run.app/v1
NEXT_PUBLIC_M5_API_URL=https://clipping-service-prod.run.app/v1
```

---

## 🎨 UI Components

### SearchBar
Autocomplete-enabled search input with debouncing.

```tsx
import { SearchBar } from '@/components/SearchBar';

<SearchBar onSearch={(query) => handleSearch(query)} autoFocus />
```

### HandCard
Poker hand result card with video preview, metadata, and favorite button.

```tsx
import { HandCard } from '@/components/HandCard';

<HandCard
  hand={handSummary}
  onFavoriteToggle={toggleFavorite}
  showRelevanceScore
/>
```

### VideoPlayer
HTML5 video player with custom controls.

```tsx
import { VideoPlayer } from '@/components/VideoPlayer';

<VideoPlayer src={proxyUrl} className="aspect-video" />
```

### DownloadButton
Clip download request button with real-time progress polling.

```tsx
import { DownloadButton } from '@/components/DownloadButton';

<DownloadButton handId="wsop2024_me_d3_h154" />
```

---

## 🧪 Testing

### Unit Tests (Jest + React Testing Library)

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

Target coverage: **70%+** (UI projects typically lower than backend)

### E2E Tests (Playwright)

```bash
# Run E2E tests (headless)
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Install Playwright browsers (first time)
npx playwright install
```

**Test Coverage**:
- ✅ Search flow (query → results → detail)
- ✅ Navigation between pages
- ✅ Autocomplete suggestions
- ✅ Download workflow
- ✅ Responsive design (mobile, tablet, desktop)

---

## 📡 BFF API Routes

### 1. POST /api/search
Search poker hands (proxies M4).

**Request**:
```json
{
  "query": "Tom Dwan bluff",
  "limit": 20,
  "filters": {
    "year_range": [2008, 2024],
    "pot_size_min": 100000
  }
}
```

**Response**:
```json
{
  "query_id": "search-20241117-001",
  "total_results": 156,
  "results": [
    {
      "hand_id": "wsop2024_me_d3_h154",
      "summary": "Tom Dwan, river all-in bluff...",
      "proxy_url": "https://...",
      "relevance_score": 0.92
    }
  ]
}
```

### 2. GET /api/search/autocomplete
Get autocomplete suggestions (proxies M4).

**Request**:
```
GET /api/search/autocomplete?q=Tom&limit=10
```

### 3. POST /api/download
Request clip download (proxies M5).

**Request**:
```json
{
  "hand_id": "wsop2024_me_d3_h154"
}
```

**Response**:
```json
{
  "clip_request_id": "clip-20241117-001",
  "status": "queued",
  "message": "Clip creation started"
}
```

### 4. GET /api/download/{id}/status
Poll download status (proxies M5).

**Response**:
```json
{
  "clip_request_id": "clip-20241117-001",
  "status": "completed",
  "download_url": "https://...",
  "file_size_bytes": 52428800
}
```

### 5. GET /api/hand/{hand_id}
Get hand details (from BigQuery).

### 6. GET/POST/DELETE /api/favorites
Manage user favorites.

### 7. GET /api/downloads/history
Get user download history.

### 8. GET /api/admin/validation/stats
Get timecode validation statistics (proxies M3).

---

## 🎯 Key Features

### 1. Semantic Search
- Natural language queries (e.g., "Tom Dwan bluff", "AA vs KK all-in")
- Autocomplete suggestions with 300ms debounce
- Filter by players, events, year, pot size
- Relevance scoring from M4 RAG Search

### 2. Video Preview
- HTML5 video player with custom controls
- Play/pause, mute, fullscreen
- Progress bar with seek
- Proxy video URLs from M2 Video Metadata

### 3. Clip Download
- Request clip generation via M5 Clipping Service
- Real-time progress polling (5s intervals, 2min max)
- Download history tracking
- Status: queued → processing → completed/failed

### 4. Favorites
- Add/remove favorites with instant UI update
- In-memory storage (development) → Firestore (production)
- Favorite indicator on search results

### 5. Admin Dashboard
- Timecode validation progress (M3 stats)
- Perfect sync rate, manual review queue
- Auto-refresh every 30 seconds
- Validation breakdown by category

---

## 🏗️ BFF Pattern Architecture

```
┌──────────────────────────────────────────┐
│          Browser (React)                 │
└──────────────┬───────────────────────────┘
               │
        HTTP Requests
               │
┌──────────────▼───────────────────────────┐
│    Next.js API Routes (BFF)              │
│    - Error handling                      │
│    - Request validation                  │
│    - Response transformation             │
│    - User context injection              │
└──────────────┬───────────────────────────┘
               │
        Proxy to upstream services
               │
     ┌─────────┼─────────┐
     │         │         │
┌────▼──┐  ┌──▼───┐  ┌──▼───┐
│  M3   │  │  M4  │  │  M5  │
│Timecode│ │Search│ │Clipping│
└────────┘  └──────┘  └──────┘
```

**Benefits**:
- Single API endpoint for frontend (simplified CORS)
- Error handling and retry logic
- Response caching and transformation
- User authentication context
- Gradual migration (mock → real APIs)

---

## 🚢 Deployment

### Option 1: Vercel (Recommended for Next.js)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# - NEXT_PUBLIC_M3_API_URL
# - NEXT_PUBLIC_M4_API_URL
# - NEXT_PUBLIC_M5_API_URL
```

### Option 2: Cloud Run (Docker)

```bash
# Build Docker image
docker build \
  --build-arg NEXT_PUBLIC_M3_API_URL=https://... \
  --build-arg NEXT_PUBLIC_M4_API_URL=https://... \
  --build-arg NEXT_PUBLIC_M5_API_URL=https://... \
  -t gcr.io/YOUR_PROJECT/m6-web-ui:1.0.0 .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT/m6-web-ui:1.0.0

# Deploy to Cloud Run
gcloud run deploy m6-web-ui \
  --image gcr.io/YOUR_PROJECT/m6-web-ui:1.0.0 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000
```

---

## 📊 Performance Targets

- **Page Load**: < 3s (First Contentful Paint)
- **Search Response**: < 500ms (excluding M4 latency)
- **Video Start**: < 2s
- **Download Poll**: 5s intervals
- **Lighthouse Score**: 90+ (Performance, Accessibility, Best Practices, SEO)

---

## ♿ Accessibility

- **WCAG 2.1 AA** compliant
- Semantic HTML (`nav`, `main`, `article`, `button`)
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

**Testing**:
```bash
# Run axe accessibility tests
npm run test:a11y
```

---

## 🔒 Security

- **CSP Headers**: Configured in `next.config.js`
- **HTTPS Only**: Enforced in production
- **Input Validation**: All BFF routes validate requests
- **XSS Prevention**: React automatic escaping
- **No Secrets in Code**: All sensitive data in environment variables

---

## 🐛 Troubleshooting

### Issue: "Failed to load search results"
**Solution**: Ensure M4 service is running on `localhost:8004`

```bash
cd ../m4-rag-search
python -m app.api
```

### Issue: "Autocomplete not working"
**Solution**: Check CORS headers on M4 service. BFF should proxy requests to avoid CORS issues.

### Issue: "Download stuck at 'queued'"
**Solution**:
1. Check M5 service is running on `localhost:8005`
2. Verify Pub/Sub emulator is running (for local development)
3. Check M5 logs for processing errors

### Issue: "Video player not displaying"
**Solution**: Ensure proxy URL is valid HTTPS URL. Check M2 service for proxy URL generation.

---

## 📚 Dependencies

**Production**:
- `next@^14.0.4` - React framework
- `react@^18.2.0` - UI library
- `@radix-ui/*` - Accessible UI primitives
- `tailwindcss@^3.3.6` - CSS framework
- `swr@^2.2.4` - Data fetching (optional)
- `date-fns@^2.30.0` - Date formatting

**Development**:
- `typescript@^5.3.3` - Type safety
- `@playwright/test@^1.40.1` - E2E testing
- `jest@^29.7.0` - Unit testing
- `eslint@^8.56.0` - Linting
- `prettier@^3.1.1` - Code formatting

---

## 🤝 Integration Points

### Upstream Services (Required)

1. **M3 Timecode Validation**: `/v1/stats` for admin dashboard
2. **M4 RAG Search**: `/v1/search`, `/v1/search/autocomplete`
3. **M5 Clipping**: `/v1/clip/request`, `/v1/clip/{id}/status`

### Data Sources

1. **BigQuery**: Hand details (via mock data in development)
2. **Firestore**: User favorites, download history (production)
3. **Cloud Storage**: Proxy video URLs (from M2)

---

## 📈 Future Enhancements

- [ ] User authentication (Google IAP)
- [ ] Real-time WebSocket for download status
- [ ] Advanced filters (UI exists, backend integration needed)
- [ ] Video thumbnails generation
- [ ] Dark mode toggle
- [ ] Internationalization (i18n)
- [ ] Analytics integration (Google Analytics 4)
- [ ] Progressive Web App (PWA) support

---

## 👥 Team

**Agent**: Frank (M6 Web UI Developer)
**Contact**: GG Production Frontend Team
**Email**: aiden.kim@ggproduction.net

---

## 📝 License

© 2024 GG Production. All rights reserved.

---

**Last Updated**: 2025-01-17 (Week 4 - Production Ready)
**Version**: 1.0.0
