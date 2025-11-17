# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Repository**: archive-mam (POKER-BRAIN WSOP Archive System)
**Version**: 2.0.0
**Primary Language**: Korean (한글) with English technical terms
**Architecture**: 6-module microservices system with mock/production environment support

---

## Project Overview

This is a **Media Asset Management (MAM) system** for World Series of Poker (WSOP) archive footage. The system consists of 6 independent microservices that process, validate, search, and deliver poker hand video clips.

**Key Principle**: All modules support **mock/production environment switching** via `POKER_ENV` environment variable:
- `development`: Uses mock data (no GCP required, free)
- `production`: Uses real GCP services (costs apply)

---

## Module Architecture

### Backend Services (Python 3.11 + Flask)

**M1 - Data Ingestion** (`modules/m1-data-ingestion/`)
- Purpose: Apache Beam ETL pipeline for ATI XML → BigQuery
- Stack: apache-beam[gcp], google-cloud-bigquery, Flask
- Tests: 48 test cases, 87% coverage
- API: 4 endpoints

**M2 - Video Metadata** (`modules/m2-video-metadata/`)
- Purpose: NAS scanning, FFmpeg metadata extraction, 720p proxy generation
- Stack: ffmpeg-python, google-cloud-storage, Flask
- Tests: 64 test cases, 85% coverage
- API: 8 endpoints

**M3 - Timecode Validation** (`modules/m3-timecode-validation/`)
- Purpose: Vision API integration for ATI timestamp ↔ NAS video sync validation
- Core Algorithm: `sync_score = vision*50 + duration*30 + player*20`
- Stack: google-cloud-vision, Flask
- Tests: 38 test cases, 83% coverage
- API: 8 endpoints

**M4 - RAG Search** (`modules/m4-rag-search/`)
- Purpose: Vertex AI semantic search (TextEmbedding-004 + Vector Search)
- Stack: google-cloud-aiplatform, Flask
- Tests: 66 test cases, 85% coverage
- API: 8 endpoints

**M5 - Clipping** (`modules/m5-clipping/`)
- Purpose: Pub/Sub async video clipping with systemd daemon
- Stack: google-cloud-pubsub, ffmpeg-python, Flask
- Tests: 80+ test cases, 90% coverage
- API: 6 endpoints

### Frontend Application (TypeScript + Next.js 14)

**M6 - Web UI** (`modules/m6-web-ui/`)
- Purpose: Search UI + video preview + download management
- Pattern: BFF (Backend-for-Frontend) with Next.js API routes
- Stack: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui
- Tests: 70+ test cases (Jest + Playwright E2E), 70% coverage
- API Routes: 8 BFF endpoints
- Pages: 6 (home, search, hand detail, favorites, downloads, admin)

---

## Development Commands

### Python Modules (M1-M5)

**Setup & Testing**:
```bash
cd modules/m{1-5}-{module-name}

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v

# Type checking (if mypy configured)
mypy app/

# Code formatting
black app/ tests/
flake8 app/ tests/
```

**Running API Server (Development Mode)**:
```bash
# Set environment to development (uses mock data)
export POKER_ENV=development  # Mac/Linux
set POKER_ENV=development     # Windows CMD
$env:POKER_ENV="development"  # Windows PowerShell

# Run Flask server
python -m app.api
# Server starts on http://localhost:8080

# Health check
curl http://localhost:8080/health
```

**Production Mode** (requires GCP credentials):
```bash
export POKER_ENV=production
export GCP_PROJECT=gg-poker-prod

# GCP authentication
gcloud auth application-default login

python -m app.api
```

### Next.js Module (M6)

**Setup & Development**:
```bash
cd modules/m6-web-ui

# Install dependencies
npm install

# Run development server
npm run dev
# Server starts on http://localhost:3000

# Build for production
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

**Testing**:
```bash
# Unit tests (Jest)
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage

# E2E tests (Playwright)
npm run test:e2e

# E2E with UI
npm run test:e2e:ui
```

### Quick Validation (All Modules)

**Windows quick test script**:
```bash
# From repository root
quick-test.bat
```

This runs all module tests sequentially and reports status.

---

## Environment Configuration

### Mock vs Production Switching

**All modules respect `POKER_ENV` variable**:

```bash
# Development Mode (default)
POKER_ENV=development
# - Uses mock_data/ fixtures
# - No GCP credentials needed
# - No costs
# - Fast iteration

# Production Mode
POKER_ENV=production
GCP_PROJECT=gg-poker-prod
# - Uses real GCP services (BigQuery, Vertex AI, Vision API, Pub/Sub, GCS)
# - Requires authentication: gcloud auth application-default login
# - Costs apply ($140-435/month, see PRODUCTION_ROADMAP.md)
```

### Mock Data Location

```
mock_data/
├── bigquery/
│   ├── hand_summary_mock.json      # 22 hands from real data
│   └── video_files_mock.json       # Video metadata
├── embeddings/
│   └── hand_embeddings_mock.json   # Pre-computed embeddings
└── pubsub/
    └── config.json                 # Pub/Sub emulator config
```

**Converting CSV to Mock Data**:
```bash
python scripts/convert_csv_to_sample_data.py
# Converts CSV poker hands to mock JSON format
```

---

## Testing Strategy

### Test Organization

Each Python module follows this structure:
```
modules/m{N}-{name}/
├── app/              # Production code
│   ├── __init__.py
│   ├── config.py     # Environment switching logic
│   ├── api.py        # Flask endpoints
│   └── *.py          # Core logic
└── tests/            # Test code (mirrors app/)
    ├── __init__.py
    ├── test_api.py   # API endpoint tests
    └── test_*.py     # Unit tests (1:1 with app/ files)
```

**1:1 Test Pairing Rule**: Every `app/foo.py` must have `tests/test_foo.py`

### Coverage Requirements

- **Minimum**: 80% code coverage
- **Current Average**: 83.3% across all modules
- **Best Practice**: Run coverage report before committing

```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html to view detailed coverage
```

### E2E Testing (M6 Only)

```bash
cd modules/m6-web-ui

# Run E2E tests
npm run test:e2e

# Specific test file
npx playwright test tests/e2e/search.spec.ts

# Debug mode
npx playwright test --debug

# UI mode (recommended)
npm run test:e2e:ui
```

**E2E Test Coverage**:
- Search flow (SearchBar component + API integration)
- Navigation (header, footer, routing)
- Video player functionality
- Download button states

---

## Automation Scripts

### Full Workflow Automation

**Master Script** (runs entire 9-week development cycle):
```bash
python scripts/run_full_workflow.py
```

This orchestrates:
- Week 1: OpenAPI spec generation
- Week 2-8: Module development (simulated with AI agents)
- Week 9: Production deployment

**Approval System**:
```bash
# Approve specific week
python scripts/approve_week.py --week 1
python scripts/approve_week.py --week 9
```

### Mock Environment Setup

```bash
# Set up all mock servers and data
python scripts/setup_mock_env.py

# This creates:
# - Mock BigQuery tables
# - Pub/Sub emulator
# - Mock API servers on ports 8001-8006
```

### Weekly Validation

```bash
# Run validation for specific week
python scripts/run_weekly_validator.py --week 4

# Generate validation summary
python scripts/generate_validation_summary.py
```

---

## GCP Integration

### Required GCP Services

When running in `production` mode:

1. **BigQuery** (M1, M2, M3, M4)
   - Dataset: `prod` (or `dev` for staging)
   - Tables: `hand_summary`, `video_files`, `validation_results`

2. **Cloud Storage** (M2, M5)
   - Buckets: `{project}-poker-videos`, `{project}-proxy-videos`, `{project}-clips`

3. **Vertex AI** (M4)
   - TextEmbedding-004 API
   - Vector Search index

4. **Vision API** (M3)
   - Label detection
   - Object detection (poker-specific)

5. **Pub/Sub** (M5)
   - Topics: `clipping-requests`, `clipping-complete`
   - Subscriptions: `clipping-worker`

6. **Cloud Run** (All modules)
   - Deployment target for Flask apps (M1-M5)
   - Or self-hosted with Docker

### Authentication

```bash
# Application Default Credentials (recommended for local dev)
gcloud auth application-default login

# Service Account (for production Cloud Run)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Deployment (Cloud Run)

```bash
cd modules/m{N}-{module-name}

# Deploy to Cloud Run
gcloud run deploy {service-name} \
  --source . \
  --region us-central1 \
  --allow-unauthenticated=false \
  --set-env-vars POKER_ENV=production,GCP_PROJECT=gg-poker-prod

# Example for M4
gcloud run deploy rag-search-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated=false
```

**Module Deployment Scripts**:
- M1: `modules/m1-data-ingestion/deploy.sh`
- M2: `modules/m2-video-metadata/run.sh`

---

## API Documentation

### OpenAPI Specifications

Each module has OpenAPI 3.0 spec (planned, not all exist yet):
- `modules/m1-data-ingestion/openapi.yaml` ✅ (exists)
- `modules/m2-video-metadata/openapi.yaml` (planned)
- `modules/m3-timecode-validation/openapi.yaml` (planned)
- `modules/m4-rag-search/openapi.yaml` (planned)
- `modules/m5-clipping/openapi.yaml` (planned)
- `modules/m6-web-ui/openapi.yaml` (planned)

### Common API Patterns

**Health Check** (all modules):
```bash
GET /health
Response: {"status": "healthy", "version": "2.0.0"}
```

**Error Response Format** (standardized):
```json
{
  "error": "InvalidRequest",
  "message": "Missing required field: hand_id",
  "details": {...}
}
```

**Authentication**: Not implemented in v2.0.0 (planned for future)

---

## Development Workflow

### Creating New Features

1. **Branch naming**: `feature/PRD-{NNNN}-{feature-name}`
2. **Commit format**: `type: description (vX.Y.Z) [PRD-NNNN]`
   - Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`
   - Example: `feat: Add autocomplete API (v2.1.0) [PRD-0042]`

### Code Style

**Python**:
- Formatter: `black` (line length 88)
- Linter: `flake8`
- Type hints: Required for all functions
- Docstrings: Google style

**TypeScript**:
- ESLint: Next.js config
- Prettier: Enabled
- Strict mode: `"strict": true` in tsconfig.json

### Testing Before Commit

```bash
# Python modules
pytest tests/ -v --cov=app

# TypeScript (M6)
npm test && npm run type-check && npm run lint

# E2E (M6)
npm run test:e2e
```

---

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'google.cloud'`
**Solution**:
```bash
pip install -r requirements.txt
# Ensure venv is activated
```

**Issue**: Mock data not loading
**Solution**:
```bash
# Verify POKER_ENV is set
echo $POKER_ENV  # Should be "development"

# Check mock data exists
ls mock_data/bigquery/*.json

# Regenerate if missing
python scripts/convert_csv_to_sample_data.py
```

**Issue**: GCP authentication errors in production
**Solution**:
```bash
# Re-authenticate
gcloud auth application-default login

# Verify project
gcloud config get-value project

# Check service account permissions
gcloud projects get-iam-policy gg-poker-prod
```

**Issue**: Playwright tests fail on first run
**Solution**:
```bash
# Install Playwright browsers
npx playwright install
```

**Issue**: Port already in use (8080, 3000, etc.)
**Solution**:
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID {PID} /F

# Mac/Linux
lsof -ti:8080 | xargs kill -9
```

---

## Documentation Index

**Getting Started**:
- `README.md` - Repository overview
- `QUICK_START.md` - 3-step quick start (20 min user time, 9 weeks automation)
- `ULTIMATE_QUICK_START.md` - Ultra-detailed guide

**Development**:
- `DEVELOPMENT_GUIDE.md` - Full development workflow (6 modules, AI agents)
- `TESTING_GUIDE.md` - Testing strategies and demo scenarios

**Deployment**:
- `PRODUCTION_ROADMAP.md` - 6-week deployment plan, cost analysis ($140-435/month)
- `PROJECT_READY.md` - Pre-deployment checklist
- `PROJECT_LAUNCHED.md` - Post-deployment monitoring
- `DEPLOYMENT_COMPLETE.md` - Final deployment report

**Review & Quality**:
- `FINAL_REVIEW.md` - Code review notes
- `CHANGELOG.md` - Version history (current: v2.0.0)
- `VERSION` - Current version number

---

## Key Files & Directories

```
archive-mam/
├── modules/                    # 6 microservices
│   ├── m1-data-ingestion/     # Apache Beam ETL
│   ├── m2-video-metadata/     # FFmpeg processing
│   ├── m3-timecode-validation/# Vision API sync
│   ├── m4-rag-search/         # Vertex AI search
│   ├── m5-clipping/           # Pub/Sub clipping
│   └── m6-web-ui/             # Next.js frontend
│
├── mock_data/                  # Development fixtures
│   ├── bigquery/              # 22 real poker hands
│   ├── embeddings/            # Pre-computed vectors
│   └── pubsub/                # Emulator config
│
├── mock_servers/               # Standalone mock servers
│   ├── m3_mock_server.py
│   ├── m4_mock_server.py
│   └── m5_mock_server.py
│
├── scripts/                    # Automation
│   ├── run_full_workflow.py   # Master automation
│   ├── approve_week.py        # Week approval
│   ├── setup_mock_env.py      # Mock setup
│   └── convert_csv_to_sample_data.py
│
├── .validation/                # Validation artifacts
│   ├── current-week.txt
│   ├── progress.json
│   └── week-{N}-approval.json
│
├── docs/                       # Architecture docs
├── tasks/                      # PRDs and task lists
├── .claude/                    # Claude Code hooks
├── .github/workflows/          # CI/CD (weekly-validation.yml)
│
├── CLAUDE.md                   # This file
├── VERSION                     # 2.0.0
└── CHANGELOG.md                # Release notes
```

---

## Performance & Scale

### Current Test Results

**Total Tests**: 366+ across all modules
**Average Coverage**: 83.3%
**Test Execution Time**:
- M1: ~5s
- M2: ~8s
- M3: ~6s
- M4: ~10s (66 tests)
- M5: ~12s (80+ tests)
- M6: ~15s (unit) + ~45s (E2E)

### Expected Production Scale

**From PRODUCTION_ROADMAP.md**:
- **Storage**: 500GB-1TB video files
- **BigQuery**: 1M hands/year (~3GB data)
- **Requests**: 10-100 searches/day (low traffic initially)
- **Costs**: $140-435/month (conservative estimate)

---

## Version History

**v2.0.0** (2025-01-17) - Current
- Complete 6-module implementation
- 148 files, 18,880+ lines of code
- 366+ tests, 83.3% average coverage
- Mock/production environment switching
- Real poker hand data (22 hands from CSV)

**v1.0.0** (2025-01-15)
- Initial repository setup
- Only M1 had actual code
- Week 1-9 simulation workflow (documentation only)

---

## Contact & Support

**Primary Contact**: aiden.kim@ggproduction.net
**Slack Channel**: #poker-brain-dev (if applicable)

**For Issues**:
1. Check this CLAUDE.md first
2. Review relevant guide (TESTING_GUIDE.md, PRODUCTION_ROADMAP.md, etc.)
3. Check `.validation/` logs if automation-related
4. Contact maintainer

---

**Last Updated**: 2025-01-17
**Maintained By**: Claude (GG Production AI Assistant)
