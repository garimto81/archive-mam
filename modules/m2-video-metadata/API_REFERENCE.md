# M2 Video Metadata Service - API Reference

Complete API documentation for the M2 Video Metadata Service.

**Base URL**: `https://video-metadata-service-{env}.run.app` or `http://localhost:8002`

**Version**: 1.0.0

---

## Authentication

For production deployments, all endpoints require Bearer token authentication (Google IAP JWT).

```http
Authorization: Bearer <jwt_token>
```

For local development, authentication can be disabled.

---

## Endpoints

### 1. Start NAS Scan

**POST** `/v1/scan`

Initiate a scan of a NAS directory to discover and index video files.

#### Request Body

```json
{
  "nas_path": "/nas/poker/2024/wsop/",
  "recursive": true,
  "generate_proxy": true,
  "proxy_resolution": "720p",
  "file_extensions": ["mp4", "mov", "avi"]
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `nas_path` | string | Yes | - | NAS directory path (must start with `/nas/poker/`) |
| `recursive` | boolean | No | `true` | Scan subdirectories recursively |
| `generate_proxy` | boolean | No | `true` | Generate 720p proxies for found videos |
| `proxy_resolution` | string | No | `"720p"` | Proxy resolution (`"720p"` or `"480p"`) |
| `file_extensions` | array | No | `["mp4", "mov", "avi"]` | File extensions to scan |

#### Response (202 Accepted)

```json
{
  "scan_id": "scan-20241117-001",
  "status": "queued",
  "nas_path": "/nas/poker/2024/wsop/",
  "started_at": "2024-11-17T10:30:00Z"
}
```

#### Example

```bash
curl -X POST http://localhost:8002/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "nas_path": "/nas/poker/2024/wsop/main_event/",
    "recursive": true,
    "generate_proxy": true
  }'
```

---

### 2. Get Scan Status

**GET** `/v1/scan/{scan_id}/status`

Retrieve the status of a running or completed scan job.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `scan_id` | string | Scan job ID (format: `scan-YYYYMMDD-NNN`) |

#### Response (200 OK)

**Running scan**:
```json
{
  "scan_id": "scan-20241117-001",
  "status": "running",
  "total_files": 150,
  "processed_files": 85,
  "failed_files": 3,
  "proxy_generated": 82,
  "started_at": "2024-11-17T10:30:00Z",
  "completed_at": null
}
```

**Completed scan**:
```json
{
  "scan_id": "scan-20241117-001",
  "status": "completed",
  "total_files": 150,
  "processed_files": 148,
  "failed_files": 2,
  "proxy_generated": 145,
  "started_at": "2024-11-17T10:30:00Z",
  "completed_at": "2024-11-17T11:30:00Z",
  "failed_files_list": [
    {
      "file_path": "/nas/poker/2024/wsop/corrupted.mp4",
      "error": "Invalid video format"
    }
  ]
}
```

#### Status Values

- `queued`: Scan job created but not started
- `running`: Scan in progress
- `completed`: Scan finished successfully
- `failed`: Scan failed with error

#### Example

```bash
curl http://localhost:8002/v1/scan/scan-20241117-001/status
```

---

### 3. Get File Metadata

**GET** `/v1/files/{file_id}`

Retrieve detailed metadata for a specific video file.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | Video file ID (format: `{event_id}_d{day}_t{table}`) |

#### Response (200 OK)

```json
{
  "file_id": "wsop2024_me_d1_t1",
  "event_id": "wsop2024_me",
  "tournament_day": 1,
  "table_number": 1,
  "nas_path": "/nas/poker/2024/wsop/main_event/day1/table1.mp4",
  "file_name": "table1.mp4",
  "file_size_bytes": 52428800000,
  "duration_seconds": 36000,
  "resolution": "1920x1080",
  "codec": "h264",
  "bitrate_kbps": 11520,
  "fps": 29.97,
  "proxy_gcs_path": "gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
  "proxy_url": "https://storage.googleapis.com/gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
  "proxy_size_bytes": 5242880000,
  "created_at": "2024-07-15T10:00:00Z",
  "scanned_at": "2024-11-17T10:35:42Z",
  "indexed_at": "2024-11-17T10:35:45Z"
}
```

#### Example

```bash
curl http://localhost:8002/v1/files/wsop2024_me_d1_t1
```

---

### 4. List Files

**GET** `/v1/files`

List video files with optional filtering and pagination.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `event_id` | string | No | - | Filter by event ID (e.g., `wsop2024_me`) |
| `date_from` | string | No | - | Start date filter (YYYY-MM-DD) |
| `date_to` | string | No | - | End date filter (YYYY-MM-DD) |
| `has_proxy` | boolean | No | - | Filter by proxy existence |
| `limit` | integer | No | `100` | Maximum results (1-1000) |
| `offset` | integer | No | `0` | Pagination offset |

#### Response (200 OK)

```json
{
  "total": 1250,
  "limit": 100,
  "offset": 0,
  "files": [
    {
      "file_id": "wsop2024_me_d1_t1",
      "event_id": "wsop2024_me",
      "duration_seconds": 36000,
      "resolution": "1920x1080",
      "proxy_gcs_path": "gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
      "proxy_url": "https://storage.googleapis.com/gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4"
    }
  ]
}
```

#### Examples

```bash
# List all files
curl http://localhost:8002/v1/files

# Filter by event
curl "http://localhost:8002/v1/files?event_id=wsop2024_me&limit=50"

# Files with proxies only
curl "http://localhost:8002/v1/files?has_proxy=true"

# Pagination
curl "http://localhost:8002/v1/files?limit=100&offset=100"
```

---

### 5. Generate Proxy

**POST** `/v1/proxy/generate`

Generate a 720p proxy video for a specific file.

#### Request Body

```json
{
  "file_id": "wsop2024_me_d1_t1",
  "resolution": "720p",
  "quality": "medium"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_id` | string | Yes | - | Video file ID |
| `resolution` | string | No | `"720p"` | Target resolution (`"720p"` or `"480p"`) |
| `quality` | string | No | `"medium"` | Quality preset: `"high"` (CRF 18), `"medium"` (CRF 23), `"low"` (CRF 28) |

#### Response (202 Accepted)

```json
{
  "proxy_job_id": "proxy-20241117-001",
  "file_id": "wsop2024_me_d1_t1",
  "status": "queued",
  "estimated_duration_sec": 1200,
  "output_gcs_path": "gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
  "started_at": "2024-11-17T14:00:00Z"
}
```

#### Example

```bash
curl -X POST http://localhost:8002/v1/proxy/generate \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "wsop2024_me_d1_t1",
    "quality": "high"
  }'
```

---

### 6. Get Proxy Status

**GET** `/v1/proxy/{proxy_job_id}/status`

Check the status of a proxy generation job.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `proxy_job_id` | string | Proxy job ID (format: `proxy-YYYYMMDD-NNN`) |

#### Response (200 OK)

**Processing**:
```json
{
  "proxy_job_id": "proxy-20241117-001",
  "file_id": "wsop2024_me_d1_t1",
  "status": "processing",
  "duration_sec": null,
  "output_gcs_path": "gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
  "output_url": null,
  "output_size_bytes": null,
  "started_at": "2024-11-17T14:00:00Z",
  "completed_at": null
}
```

**Completed**:
```json
{
  "proxy_job_id": "proxy-20241117-001",
  "file_id": "wsop2024_me_d1_t1",
  "status": "completed",
  "duration_sec": 1150,
  "output_gcs_path": "gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
  "output_url": "https://storage.googleapis.com/gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4",
  "output_size_bytes": 5242880000,
  "completed_at": "2024-11-17T14:19:10Z"
}
```

#### Status Values

- `queued`: Job created but not started
- `processing`: Proxy generation in progress
- `completed`: Proxy generated successfully
- `failed`: Proxy generation failed

#### Example

```bash
curl http://localhost:8002/v1/proxy/proxy-20241117-001/status
```

---

### 7. Get Statistics

**GET** `/v1/stats`

Retrieve scanning statistics for a time period.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `period` | string | No | `"24h"` | Time period: `"24h"`, `"7d"`, `"30d"`, `"all"` |

#### Response (200 OK)

```json
{
  "period": "24h",
  "total_files_scanned": 450,
  "total_files_in_db": 125000,
  "total_storage_bytes": 52428800000000,
  "proxies_generated": 380,
  "avg_duration_seconds": 7200.5,
  "last_scan_at": "2024-11-17T10:30:00Z"
}
```

#### Example

```bash
curl "http://localhost:8002/v1/stats?period=7d"
```

---

### 8. Health Check

**GET** `/health`

Check service health and dependencies status.

#### Response (200 OK)

**Healthy**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "dependencies": {
    "nas": "ok",
    "bigquery": "ok",
    "gcs": "ok"
  }
}
```

**Degraded**:
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "dependencies": {
    "nas": "error",
    "bigquery": "ok",
    "gcs": "ok"
  }
}
```

#### Example

```bash
curl http://localhost:8002/health
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  },
  "request_id": "req-20241117-001",
  "timestamp": "2024-11-17T10:30:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Example Error

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "nas_path must start with '/nas/poker/'",
    "details": {
      "field": "nas_path",
      "provided": "/mnt/videos/"
    }
  },
  "request_id": "req-20241117-001",
  "timestamp": "2024-11-17T10:30:00Z"
}
```

---

## Rate Limits

- **Scan endpoint**: 3 concurrent scans maximum
- **Proxy generation**: 10 concurrent jobs maximum
- **API calls**: 1000 requests/minute per IP

---

## Webhooks (Future)

Webhook notifications for long-running operations:

```json
{
  "event": "scan.completed",
  "scan_id": "scan-20241117-001",
  "status": "completed",
  "total_files": 150,
  "timestamp": "2024-11-17T11:30:00Z"
}
```

---

## SDK Examples

### Python

```python
import requests

# Start scan
response = requests.post('http://localhost:8002/v1/scan', json={
    'nas_path': '/nas/poker/2024/wsop/',
    'recursive': True,
    'generate_proxy': True
})
scan_id = response.json()['scan_id']

# Poll status
import time
while True:
    status = requests.get(f'http://localhost:8002/v1/scan/{scan_id}/status').json()
    if status['status'] == 'completed':
        break
    time.sleep(10)

print(f"Processed {status['processed_files']} files")
```

### cURL

```bash
# Complete workflow
SCAN_ID=$(curl -s -X POST http://localhost:8002/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"nas_path":"/nas/poker/test/"}' | jq -r '.scan_id')

echo "Scan ID: $SCAN_ID"

# Wait for completion
while true; do
  STATUS=$(curl -s http://localhost:8002/v1/scan/$SCAN_ID/status | jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 10
done
```

### JavaScript

```javascript
// Start scan
const response = await fetch('http://localhost:8002/v1/scan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    nas_path: '/nas/poker/2024/wsop/',
    recursive: true
  })
});

const { scan_id } = await response.json();

// Poll status
const pollStatus = async () => {
  const res = await fetch(`http://localhost:8002/v1/scan/${scan_id}/status`);
  const status = await res.json();

  if (status.status === 'completed') {
    console.log(`Processed ${status.processed_files} files`);
  } else {
    setTimeout(pollStatus, 10000);
  }
};

pollStatus();
```

---

## Support

- **OpenAPI Spec**: See `modules/video-metadata/openapi.yaml`
- **Issues**: Create GitHub issue
- **Contact**: aiden.kim@ggproduction.net
