# M2 Video Metadata Service - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    M2 VIDEO METADATA SERVICE                     │
│                         (Flask + Gunicorn)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │         8 REST API ENDPOINTS             │
        │  /scan, /files, /proxy, /stats, /health  │
        └──────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ NAS Scanner │      │   FFmpeg    │      │ GCS Uploader│
│  (scanner)  │      │  (ffmpeg)   │      │    (gcs)    │
└─────────────┘      └─────────────┘      └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│     NAS     │      │   Proxy     │      │ BigQuery    │
│  /nas/poker │      │  Generator  │      │   Client    │
└─────────────┘      └─────────────┘      └─────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Video Files │      │ GCS Bucket  │      │  BigQuery   │
│ .mp4, .mov  │      │ gg-poker-   │      │prod.video_  │
│   .avi      │      │   proxy     │      │   files     │
└─────────────┘      └─────────────┘      └─────────────┘
```

## Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                          │
│  (cURL, Python SDK, JavaScript, Cloud Scheduler)           │
└────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/JSON
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    API LAYER (Flask)                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  api.py (500+ lines)                                 │ │
│  │  - Request validation                                │ │
│  │  - Background job management                         │ │
│  │  - Response formatting                               │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    SCANNER   │  │    FFMPEG    │  │  PROXY GEN   │
│  scanner.py  │  │ffmpeg_utils  │  │ proxy_gen.py │
│  (200 lines) │  │  (100 lines) │  │  (150 lines) │
│              │  │              │  │              │
│ - Recursive  │  │ - Metadata   │  │ - 720p H.264 │
│   dir walk   │  │   extraction │  │ - Quality    │
│ - .mp4 find  │  │ - Validation │  │   presets    │
│ - Event ID   │  │ - FPS calc   │  │ - Fast enc   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        │                  │                  ▼
        │                  │         ┌──────────────┐
        │                  │         │ GCS UPLOADER │
        │                  │         │gcs_uploader  │
        │                  │         │  (120 lines) │
        │                  │         │              │
        │                  │         │ - Chunked    │
        │                  │         │   upload     │
        │                  │         │ - MD5 verify │
        │                  │         │ - Signed URL │
        │                  │         └──────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                  ┌──────────────┐
                  │  BIGQUERY    │
                  │   CLIENT     │
                  │bigquery_     │
                  │ client.py    │
                  │ (250 lines)  │
                  │              │
                  │ - Insert     │
                  │ - Upsert     │
                  │ - Query      │
                  │ - Stats      │
                  └──────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌──────────────┐                     ┌──────────────┐
│   GCS BUCKET │                     │   BIGQUERY   │
│ gg-poker-    │                     │prod.video_   │
│   proxy/     │                     │   files      │
│              │                     │              │
│ - Proxies    │                     │ - Metadata   │
│ - Public URL │                     │ - Searchable │
└──────────────┘                     └──────────────┘
```

## Data Flow

### Scan Workflow

```
1. Client POST /v1/scan
   │
   ▼
2. API creates scan_id (scan-20241117-001)
   │
   ▼
3. Background thread starts
   │
   ├─► NAS Scanner finds .mp4 files
   │   │
   │   ├─► /nas/poker/2024/wsop/day1/table1.mp4
   │   ├─► /nas/poker/2024/wsop/day1/table2.mp4
   │   └─► /nas/poker/2024/wsop/day2/table1.mp4
   │
   ▼
4. For each video file:
   │
   ├─► FFmpeg extracts metadata
   │   ├─► Duration: 36000s
   │   ├─► Resolution: 1920x1080
   │   ├─► Codec: h264
   │   ├─► Bitrate: 11520 kbps
   │   └─► FPS: 29.97
   │
   ├─► (Optional) Generate 720p proxy
   │   ├─► FFmpeg transcode (H.264, CRF 23)
   │   ├─► Output: /tmp/wsop2024_me_d1_t1_720p.mp4
   │   └─► Upload to GCS
   │       └─► gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4
   │
   └─► Insert/Update BigQuery
       └─► prod.video_files table

5. Update scan_jobs[scan_id] status
   │
   ▼
6. Client polls GET /v1/scan/{scan_id}/status
   │
   └─► Returns: processed_files, total_files, status
```

### Proxy Generation Workflow

```
1. Client POST /v1/proxy/generate
   │
   ▼
2. API creates proxy_job_id (proxy-20241117-001)
   │
   ▼
3. Get video metadata from BigQuery
   │
   ▼
4. Background thread starts FFmpeg transcode
   │
   ├─► Input: /nas/poker/.../video.mp4
   │
   ├─► FFmpeg command:
   │   ├─► scale=-2:720 (720p, aspect ratio preserved)
   │   ├─► vcodec=libx264 (H.264)
   │   ├─► acodec=aac (AAC audio)
   │   ├─► crf=23 (quality)
   │   ├─► preset=fast (speed)
   │   └─► movflags=faststart (web streaming)
   │
   ├─► Output: /tmp/proxy_720p.mp4
   │
   ▼
5. Upload to GCS
   │
   ├─► Chunked upload (for large files)
   ├─► MD5 checksum verification
   └─► gs://gg-poker-proxy/...

6. Update BigQuery with proxy path
   │
   ▼
7. Update proxy_jobs[job_id] status
   │
   ▼
8. Client polls GET /v1/proxy/{job_id}/status
   │
   └─► Returns: output_url, output_size_bytes, status
```

## Database Schema

### BigQuery: prod.video_files

```
┌──────────────────┬──────────┬──────────────────────────┐
│     Column       │   Type   │      Description         │
├──────────────────┼──────────┼──────────────────────────┤
│ video_id         │ STRING   │ PK: wsop2024_me_d1_t1    │
│ event_id         │ STRING   │ wsop2024_me              │
│ tournament_day   │ INT64    │ 1                        │
│ table_number     │ INT64    │ 1                        │
│ nas_file_path    │ STRING   │ /nas/poker/.../table1.mp4│
│ file_name        │ STRING   │ table1.mp4               │
│ gcs_proxy_path   │ STRING   │ gs://gg-poker-proxy/...  │
│ duration_seconds │ INT64    │ 36000 (10 hours)         │
│ resolution       │ STRING   │ 1920x1080                │
│ codec            │ STRING   │ h264                     │
│ bitrate_kbps     │ INT64    │ 11520                    │
│ fps              │ FLOAT64  │ 29.97                    │
│ file_size_bytes  │ INT64    │ 52428800000 (48.8 GB)    │
│ proxy_size_bytes │ INT64    │ 5242880000 (4.88 GB)     │
│ created_at       │ TIMESTAMP│ 2024-07-15T10:00:00Z     │
│ scanned_at       │ TIMESTAMP│ 2024-11-17T10:35:42Z     │
│ indexed_at       │ TIMESTAMP│ 2024-11-17T10:35:45Z     │
└──────────────────┴──────────┴──────────────────────────┘

Indexes:
- video_id (PRIMARY)
- event_id
- indexed_at (for time-based queries)
```

## Deployment Architecture

### Cloud Run Deployment

```
┌──────────────────────────────────────────────────────┐
│                   CLOUD RUN SERVICE                  │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Container: gcr.io/gg-poker/m2-video-metadata │ │
│  │  - Python 3.11                                 │ │
│  │  - FFmpeg 6.0                                  │ │
│  │  - Gunicorn (2 workers, 4 threads)            │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Resources:                                          │
│  - Memory: 4 GB                                     │
│  - CPU: 2 cores                                     │
│  - Timeout: 900s (15 min)                          │
│  - Concurrency: 10 requests/instance                │
│  - Min instances: 1                                 │
│  - Max instances: 5                                 │
└──────────────────────────────────────────────────────┘
                      │
                      │ HTTPS
                      ▼
┌──────────────────────────────────────────────────────┐
│              EXTERNAL DEPENDENCIES                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  BigQuery   │  │ GCS Bucket  │  │     NAS     │ │
│  │prod.video_  │  │gg-poker-    │  │ /nas/poker  │ │
│  │   files     │  │   proxy     │  │ (via FUSE)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└──────────────────────────────────────────────────────┘
```

### High Availability Setup

```
┌───────────────────────────────────────────────┐
│        LOAD BALANCER (Cloud Load Balancing)  │
└───────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │Instance│   │Instance│   │Instance│
   │   1    │   │   2    │   │   3    │
   └────────┘   └────────┘   └────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │BigQuery│   │  GCS   │   │  NAS   │
   │ (HA)   │   │ (HA)   │   │(shared)│
   └────────┘   └────────┘   └────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                      │
│  (Authenticated via Google IAP or API Key)          │
└─────────────────────────────────────────────────────┘
                       │
                       │ HTTPS + JWT Token
                       ▼
┌─────────────────────────────────────────────────────┐
│              IDENTITY-AWARE PROXY (IAP)             │
│  - JWT validation                                   │
│  - User authentication                              │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 CLOUD RUN SERVICE                   │
│  Service Account: m2-video-metadata@gg-poker...    │
└─────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  BigQuery    │ │     GCS      │ │     NAS      │
│  IAM Roles:  │ │  IAM Roles:  │ │  Read-Only   │
│ - dataEditor │ │ - objectAdmin│ │   Mount      │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Monitoring & Logging

```
┌─────────────────────────────────────────────────────┐
│                  APPLICATION LOGS                   │
│  (Google Cloud Logging)                             │
│  - INFO: Scan started, file processed               │
│  - WARNING: Missing metadata                        │
│  - ERROR: FFmpeg failure, GCS upload error          │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                CLOUD MONITORING                     │
│  - Request count                                    │
│  - Error rate                                       │
│  - Latency (p50, p95, p99)                         │
│  - Memory usage                                     │
│  - CPU utilization                                  │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                  ALERTING                           │
│  - Error rate > 10%                                 │
│  - Memory usage > 90%                               │
│  - Health check failures                            │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              NOTIFICATION CHANNELS                  │
│  - Email: aiden.kim@ggproduction.net               │
│  - Slack: #poker-brain-alerts                      │
│  - PagerDuty: On-call rotation                     │
└─────────────────────────────────────────────────────┘
```

## Scalability

### Horizontal Scaling

```
Load: 100 videos/min
   │
   ▼
┌────────────┐
│ 1 Instance │  ← Handles 50 videos/min
└────────────┘

Load: 300 videos/min
   │
   ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Instance 1 │  │ Instance 2 │  │ Instance 3 │
└────────────┘  └────────────┘  └────────────┘
  50 vid/min      50 vid/min      50 vid/min
      │                │                │
      └────────────────┴────────────────┘
                       │
                  150 vid/min total
                  + 150 vid/min capacity
```

### Vertical Scaling

```
Default:
- Memory: 4 GB
- CPU: 2 cores
- Throughput: ~50 videos/min

Scaled Up:
- Memory: 8 GB
- CPU: 4 cores
- Throughput: ~100 videos/min
```

## Integration Points

```
┌──────────────────────────────────────────────────────┐
│               M2 VIDEO METADATA SERVICE              │
│              (This Service)                          │
└──────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  M3 CLIP     │ │  M4 TRANS-   │ │  M5 SEARCH   │
│ SEGMENTATION │ │  CRIPTION    │ │    ENGINE    │
│              │ │              │ │              │
│ Reads:       │ │ Reads:       │ │ Reads:       │
│ - video_id   │ │ - proxy_url  │ │ - video_id   │
│ - duration   │ │ - duration   │ │ - metadata   │
│ - nas_path   │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘

        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
        ┌──────────────────────────┐
        │     FRONTEND UI          │
        │   (React/Next.js)        │
        │                          │
        │ - Video catalog          │
        │ - Proxy playback         │
        │ - Search results         │
        └──────────────────────────┘
```

## Performance Optimization

### Caching Strategy

```
┌──────────────────────────────────────────────────────┐
│                   CLIENT                             │
└──────────────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────┐
│              CLOUD CDN (Optional)                    │
│  - Cache proxy URLs                                  │
│  - TTL: 24 hours                                     │
└──────────────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────┐
│              APPLICATION CACHE                       │
│  - In-memory job status (scan_jobs, proxy_jobs)     │
│  - No persistent cache needed                        │
└──────────────────────────────────────────────────────┘
```

### Parallel Processing

```
Sequential (Slow):
Video 1 → Video 2 → Video 3 → Video 4
 (10s)     (10s)     (10s)     (10s)
Total: 40 seconds

Parallel (Fast):
Video 1 ──┐
Video 2 ──┼─→ Process in parallel
Video 3 ──┤
Video 4 ──┘
Total: 10 seconds (4x faster)
```

---

**Architecture Version**: 1.0.0
**Last Updated**: 2024-11-17
**Author**: Bob (M2 Video Metadata Developer)
