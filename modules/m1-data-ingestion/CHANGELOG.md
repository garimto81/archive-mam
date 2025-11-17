# Changelog - M1 Data Ingestion Service

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-17 (Week 3 - 30% Complete)

### Added
- **Core Pipeline Components**
  - `ParseATIJson` DoFn for JSON parsing and transformation
  - `DeduplicateByHandId` DoFn for duplicate removal
  - BigQuery schema definition (13 fields)
  - Dataflow pipeline orchestration (GCS → BigQuery)

- **Flask API Server**
  - `POST /v1/ingest` - Start ingestion job
  - `GET /v1/ingest/{job_id}/status` - Get job status
  - `GET /v1/stats` - Get ingestion statistics
  - `GET /health` - Health check endpoint

- **BigQuery Client**
  - Connection validation
  - Statistics aggregation (24h, 7d, 30d, all)
  - Hand existence checking
  - Table metadata retrieval

- **Configuration Management**
  - Environment-based config (development, staging, production)
  - `.env` file support
  - Config validation

- **Testing Infrastructure**
  - Unit tests for pipeline components (test_pipeline.py)
  - Unit tests for API endpoints (test_api.py)
  - Unit tests for BigQuery client (test_bigquery_client.py)
  - pytest configuration with 80% coverage target
  - Mock-based testing strategy

- **Deployment**
  - Dockerfile for Cloud Run
  - requirements.txt with pinned versions
  - deployment script (deploy.sh)
  - local development script (run_local.sh)

- **Documentation**
  - Comprehensive README.md
  - API endpoint documentation
  - Architecture diagrams
  - Troubleshooting guide

### Implementation Details

**Week 3 Completion (30%)**:
- ✅ Project structure created
- ✅ Dataflow pipeline basic flow implemented
- ✅ JSON parsing with error handling
- ✅ Duplicate removal logic
- ✅ Flask API with 4 endpoints
- ✅ Unit tests (80% coverage)
- ✅ Dockerfile ready for Cloud Run
- ✅ BigQuery schema defined

**Week 4 Planned (70%)**:
- ⏳ Dead Letter Queue for failed records
- ⏳ Firestore/Redis for job state persistence
- ⏳ Integration tests with sample data
- ⏳ Cloud Monitoring integration
- ⏳ Production deployment validation
- ⏳ Performance testing (10K hands/min target)
- ⏳ Error rate monitoring (<1% target)

### Technical Specifications

**Dependencies**:
- Python 3.11
- Apache Beam 2.50.0
- Flask 2.3.3
- google-cloud-bigquery 3.11.0
- gunicorn 21.2.0

**Architecture**:
- Input: GCS JSONL files (gs://gg-poker-ati/)
- Processing: Dataflow with 2 DoFn transformations
- Output: BigQuery table (prod.hand_summary)
- API: Flask on Cloud Run (2 workers, 4 threads)

**Performance Targets**:
- API response time: <500ms
- Dataflow throughput: 10K hands/min
- Duplicate prevention: 100%
- Error rate: <1%
- Test coverage: 80%+

### Known Limitations (Week 3)

- Job status stored in-memory (will use Firestore in Week 4)
- No Dead Letter Queue for parse errors
- Health check dependencies are mocked
- No integration tests with real GCP services
- No Cloud Monitoring alerts configured

### Dependencies on Other Modules

**Upstream**:
- GCS Bucket: `gs://gg-poker-ati/` (ATI raw data source)

**Downstream**:
- M3 Video Processing Service (consumer)
- M4 Metadata Enrichment Service (consumer)

### Contributors

- Alice (Data Ingestion Developer) - Primary developer

---

## [Unreleased]

### Planned for Week 4 (v1.1.0)

- Dead Letter Queue implementation
- Firestore integration for job state
- Integration tests (E2E)
- Cloud Monitoring dashboards
- Dataflow job metrics tracking
- Production deployment
- Performance validation

---

**Version Format**: MAJOR.MINOR.PATCH
- MAJOR: Breaking API changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Week Tracking**:
- Week 3: v1.0.0 (30% complete)
- Week 4: v1.1.0 (100% complete, production-ready)
