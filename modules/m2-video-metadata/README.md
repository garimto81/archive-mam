# M2 Video Metadata Service (Bob)

**Status**: Week 3 - 30% Complete
**Agent**: Bob
**Version**: 0.3.0

## Overview

NAS 스캔 및 비디오 메타데이터 추출 서비스입니다.

## Week 3 Deliverables (30%)

### Core Structure
- ✅ NAS scanner basic structure
- ✅ FFmpeg metadata extraction
- ✅ Flask API (8 endpoints planned, 3 implemented)
- ⏳ Proxy generation (pending Week 4)
- ⏳ Database schema (pending Week 4)

### Implemented (Week 3)
```
m2-video-metadata/
├── app/
│   ├── api.py           # Flask API (3/8 endpoints)
│   ├── nas_scanner.py   # NAS directory scanning
│   └── ffmpeg_client.py # FFmpeg metadata extraction
├── tests/
│   └── test_scanner.py  # Basic tests
├── requirements.txt
└── README.md
```

### API Endpoints (Week 3)
- ✅ GET /v1/health - Health check
- ✅ POST /v1/scan - Start NAS scan
- ✅ GET /v1/scan/{job_id}/status - Scan status
- ⏳ POST /v1/extract/{video_id} (Week 4)
- ⏳ GET /v1/videos (Week 4)
- ⏳ POST /v1/proxy/{video_id} (Week 4)
- ⏳ GET /v1/proxy/{video_id}/status (Week 4)
- ⏳ GET /v1/stats (Week 4)

## Week 4 Plan (70%)
- Proxy generation (FFmpeg transcoding)
- Full database integration
- Remaining 5 API endpoints
- Integration tests
- Cloud Run deployment

## Dependencies
- FFmpeg 6.0+
- Flask 2.3+
- Cloud Storage (NAS mount)

**Last Updated**: 2025-01-17 (Week 3)
