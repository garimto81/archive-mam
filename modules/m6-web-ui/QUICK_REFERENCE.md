# M6 Web UI - Quick Reference Card

Essential commands and configurations for daily development.

---

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server (after M3, M4, M5 are running)
npm run dev

# Open browser
http://localhost:3000
```

---

## 📦 Development Commands

```bash
# Development
npm run dev              # Start dev server (port 3000)
npm run build            # Build for production
npm run start            # Start production server
npm run lint             # Run ESLint
npm run type-check       # TypeScript type checking
npm run format           # Format code with Prettier

# Testing
npm test                 # Run unit tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Generate coverage report
npm run test:e2e         # Run E2E tests (headless)
npm run test:e2e:ui      # Run E2E tests with UI
```

---

## 🔧 Backend Services (Required for Development)

```bash
# Terminal 1: M3 Timecode Validation
cd modules/m3-timecode-validation
python -m app.api
# → http://localhost:8003

# Terminal 2: M4 RAG Search
cd modules/m4-rag-search
python -m app.api
# → http://localhost:8004

# Terminal 3: M5 Clipping
cd modules/m5-clipping
python app/api.py
# → http://localhost:8005

# Terminal 4: M6 Web UI
cd modules/m6-web-ui
npm run dev
# → http://localhost:3000
```

---

## 🌍 Environment Variables

**Development** (`.env.development`):
```bash
NEXT_PUBLIC_POKER_ENV=development
NEXT_PUBLIC_M3_API_URL=http://localhost:8003/v1
NEXT_PUBLIC_M4_API_URL=http://localhost:8004/v1
NEXT_PUBLIC_M5_API_URL=http://localhost:8005/v1
```

**Production** (`.env.production`):
```bash
NEXT_PUBLIC_POKER_ENV=production
NEXT_PUBLIC_M3_API_URL=https://timecode-validation-service-prod.run.app/v1
NEXT_PUBLIC_M4_API_URL=https://rag-search-service-prod.run.app/v1
NEXT_PUBLIC_M5_API_URL=https://clipping-service-prod.run.app/v1
```

---

## 📡 API Endpoints (BFF Routes)

```
POST   /api/search                      # Search hands
GET    /api/search/autocomplete         # Autocomplete suggestions
POST   /api/download                    # Request clip download
GET    /api/download/{id}/status        # Download status
GET    /api/hand/{hand_id}              # Hand details
GET    /api/favorites                   # List favorites
POST   /api/favorites                   # Add favorite
DELETE /api/favorites?hand_id=...       # Remove favorite
GET    /api/downloads/history           # Download history
GET    /api/admin/validation/stats      # Admin stats
GET    /api/health                      # Health check
```

---

## 🎨 Component Import Paths

```typescript
// UI Primitives
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Feature Components
import { SearchBar } from '@/components/SearchBar';
import { HandCard } from '@/components/HandCard';
import { VideoPlayer } from '@/components/VideoPlayer';
import { DownloadButton } from '@/components/DownloadButton';

// Utilities
import { cn } from '@/lib/utils';
import { bffApi } from '@/lib/api-client';
import { API_ENDPOINTS } from '@/lib/api-config';

// Types
import type { HandSummary, SearchResponse } from '@/lib/types';
```

---

## 🧪 Testing Commands

```bash
# Unit Tests
npm test                              # Run all tests
npm run test:watch                    # Watch mode
npm run test:coverage                 # With coverage

# E2E Tests
npx playwright install                # Install browsers (first time)
npm run test:e2e                      # Run E2E (headless)
npm run test:e2e:ui                   # Run with UI
npx playwright show-report            # View last test report
```

---

## 🚢 Deployment

**Vercel** (Recommended):
```bash
npm i -g vercel
vercel login
vercel          # Deploy to preview
vercel --prod   # Deploy to production
```

**Docker** (Cloud Run):
```bash
docker build \
  --build-arg NEXT_PUBLIC_M3_API_URL=https://... \
  -t gcr.io/PROJECT/m6-web-ui:1.0.0 .

docker push gcr.io/PROJECT/m6-web-ui:1.0.0

gcloud run deploy m6-web-ui \
  --image gcr.io/PROJECT/m6-web-ui:1.0.0 \
  --region us-central1
```

---

## 🐛 Troubleshooting

### Port 3000 Already in Use
```bash
# Find process
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3001 npm run dev
```

### Module Not Found
```bash
rm -rf node_modules .next
npm install
```

### TypeScript Errors
```bash
npm run type-check
```

### Backend Service Not Responding
```bash
# Check if service is running
curl http://localhost:8003/health  # M3
curl http://localhost:8004/health  # M4
curl http://localhost:8005/health  # M5
```

---

## 📁 Important File Paths

```
# Configuration
next.config.js              # Next.js configuration
tsconfig.json              # TypeScript configuration
tailwind.config.ts         # Tailwind CSS configuration
.env.development           # Development environment variables

# Source Code
app/page.tsx               # Home page
app/search/page.tsx        # Search results page
app/api/search/route.ts    # Search API route
components/SearchBar.tsx   # Search component
lib/types.ts               # TypeScript types
lib/api-client.ts          # API client

# Tests
tests/e2e/search.spec.ts   # E2E search tests
tests/e2e/navigation.spec.ts # E2E navigation tests

# Documentation
README.md                  # Main documentation
DEVELOPMENT_GUIDE.md       # Development workflow
PROJECT_SUMMARY.md         # Project overview
QUICK_REFERENCE.md         # This file
```

---

## 💡 Common Tasks

### Create New Page
```bash
# 1. Create page file
touch app/my-page/page.tsx

# 2. Add page component
# app/my-page/page.tsx
export default function MyPage() {
  return <div>My Page</div>
}

# 3. Navigate to /my-page
```

### Create New API Route
```bash
# 1. Create route file
mkdir -p app/api/my-endpoint
touch app/api/my-endpoint/route.ts

# 2. Add handler
# app/api/my-endpoint/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  return NextResponse.json({ data: 'Hello' });
}

# 3. Call /api/my-endpoint
```

### Create New Component
```bash
# 1. Create component file
touch components/MyComponent.tsx

# 2. Add component
# components/MyComponent.tsx
'use client';

interface MyComponentProps {
  title: string;
}

export function MyComponent({ title }: MyComponentProps) {
  return <div>{title}</div>
}

# 3. Import and use
import { MyComponent } from '@/components/MyComponent';
```

---

## 📊 Performance Targets

- Page Load: < 3s (FCP)
- Search Response: < 500ms
- Video Start: < 2s
- Lighthouse Score: 90+

---

## 🔐 Security Checklist

- [ ] No hardcoded secrets
- [ ] Environment variables in .env
- [ ] Input validation on all API routes
- [ ] CSP headers configured
- [ ] HTTPS enforced in production

---

## 📚 Documentation Links

- [README.md](./README.md) - Full documentation
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Development workflow
- [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - Project overview
- [Next.js Docs](https://nextjs.org/docs) - Next.js documentation
- [Tailwind CSS](https://tailwindcss.com/docs) - Tailwind documentation
- [shadcn/ui](https://ui.shadcn.com/) - Component library

---

**Version**: 1.0.0
**Last Updated**: 2025-01-17
