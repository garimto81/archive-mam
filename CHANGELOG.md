# Changelog

All notable changes to the POKER-BRAIN WSOP Archive System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-17

### Added

**Major Release: Complete 6-Module Implementation**

#### Backend Services (M1-M5)
- **M1 Data Ingestion**: Apache Beam ETL pipeline for ATI XML processing
  - 20 files, 3,264 lines of code
  - 48 test cases, 87% coverage
  - BigQuery integration with mock/production switching
  - 4 REST API endpoints

- **M2 Video Metadata**: FFmpeg-based video processing service
  - 28 files, 2,484+ lines of code
  - 64 test cases, 85% coverage
  - NAS scanning, metadata extraction, 720p proxy generation
  - 8 REST API endpoints

- **M3 Timecode Validation**: Vision API integration for sync validation
  - 19 files, 2,432 lines of code
  - 38 test cases, 83% coverage
  - sync_score algorithm (vision*50 + duration*30 + player*20)
  - 8 REST API endpoints

- **M4 RAG Search**: Vertex AI semantic search service
  - 21 files, 3,200+ lines of code
  - 66 test cases, 85% coverage
  - TextEmbedding-004 integration, Vector Search
  - 8 REST API endpoints

- **M5 Clipping**: Pub/Sub async video clipping service
  - 24 files, 4,000+ lines of code
  - 80+ test cases, 90% coverage
  - FFmpeg clipping, GCS upload, systemd daemon
  - 6 REST API endpoints

#### Frontend Application (M6)
- **M6 Web UI**: Next.js 14 + BFF pattern
  - 36 files, 3,500+ lines of code
  - 70+ test cases, 70% coverage
  - 8 BFF API routes, 6 UI pages, 8 components
  - Responsive design, Playwright E2E tests

#### Infrastructure & Documentation
- **Mock/Real Environment Switching**: POKER_ENV variable for all modules
- **Sample Data Conversion**: CSV to JSON converter for real poker hands
- **Testing Infrastructure**: 366+ tests across all modules (avg 83% coverage)
- **Production Roadmap**: 6-week deployment plan with cost analysis
- **Comprehensive Documentation**: 10,000+ lines of guides and READMEs

#### Testing & Quality
- Unit tests: 366+ test cases
- Integration tests: Mock data support for offline development
- E2E tests: Playwright test suite for M6
- Code coverage: 83.3% average across all modules
- Type safety: 100% type hints (Python), TypeScript strict mode (M6)

### Changed
- Upgraded from simulation-based workflow to actual implementation
- All 6 modules now have production-ready code (previously only documentation)
- Mock data system supports real poker hand data (22 hands from CSV)

### Technical Details

**Total Statistics**:
- **148 files** created
- **18,880+ lines** of production code
- **42 API endpoints** implemented
- **6 Docker images** ready for deployment
- **15 GCP services** integrated

**Technologies Used**:
- Backend: Python 3.11, Flask 2.3+, Apache Beam 2.50+
- Frontend: Next.js 14, React 18, TypeScript
- Cloud: GCP (BigQuery, Vertex AI, Vision API, Pub/Sub, Cloud Run, GCS)
- Testing: pytest, Jest, Playwright
- Infrastructure: Docker, systemd, Vercel

### Migration Guide

**From v1.0.0 (Simulation) to v2.0.0 (Real Implementation)**:

1. **Development Mode** (No GCP required):
   ```bash
   export POKER_ENV=development
   # All modules use mock data
   ```

2. **Production Mode** (GCP required):
   ```bash
   export POKER_ENV=production
   export GCP_PROJECT=gg-poker-prod
   # All modules use real GCP services
   ```

3. **Cost Estimation**:
   - Development: $0 (mock data only)
   - Production: $140-435/month (see PRODUCTION_ROADMAP.md)

### Next Steps

See `PRODUCTION_ROADMAP.md` for detailed deployment plan:
- **Phase 0**: GCP setup (Week 1)
- **Phase 1**: Backend deployment (Week 2-3)
- **Phase 2**: Frontend deployment (Week 4)
- **Phase 3**: Operations preparation (Week 5)

---

## [1.0.0] - 2025-01-15

### Added
- Initial repository setup
- Week 1-9 simulation workflow
- Project structure and documentation
- Mock data generation scripts
- Agent-based development workflow (17 AI agents)

### Features (Simulation Only)
- 99.99% automation achieved in simulation
- Week 3-9 simulation completed (documentation only)
- Only M1 had actual code implementation

---

[2.0.0]: https://github.com/ggproduction/archive-mam/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/ggproduction/archive-mam/releases/tag/v1.0.0
