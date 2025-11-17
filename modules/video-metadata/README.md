# M2: Video Metadata Service

**담당**: Backend Engineer (Bob)
**버전**: 1.0.0
**배포**: Cloud Run (us-central1)

---

## 개요

NAS 영상 파일을 스캔하여 메타데이터를 추출하고, 720p 프록시 영상을 생성하는 서비스입니다.

### 주요 기능

- ✅ NAS 디렉토리 재귀 스캔
- ✅ FFmpeg 메타데이터 추출 (해상도, 코덱, 길이, FPS)
- ✅ 720p H.264 프록시 생성
- ✅ GCS 업로드
- ✅ BigQuery 적재

---

## 아키텍처

```
NAS (/nas/poker/)
    ↓
POST /v1/scan (재귀 탐색)
    ↓
For each video file:
    ├─ FFmpeg Probe (메타데이터)
    ├─ FFmpeg Transcode (720p 프록시)
    └─ GCS Upload
    ↓
BigQuery (prod.video_files)
```

---

## API 스펙

**OpenAPI 3.0**: `openapi.yaml`

### 주요 엔드포인트

#### 1. POST /v1/scan

NAS 스캔 시작:

```bash
curl -X POST https://video-metadata-service-prod.run.app/v1/scan \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "nas_path": "/nas/poker/2024/wsop/",
    "recursive": true,
    "generate_proxy": true,
    "proxy_resolution": "720p"
  }'
```

#### 2. GET /v1/files/{file_id}

파일 메타데이터 조회:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://video-metadata-service-prod.run.app/v1/files/vid_wsop2024_me_d3
```

#### 3. POST /v1/proxy/generate

개별 프록시 생성:

```bash
curl -X POST https://video-metadata-service-prod.run.app/v1/proxy/generate \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -d '{"file_id": "vid_wsop2024_me_d3", "resolution": "720p"}'
```

---

## BigQuery 스키마

### prod.video_files

```sql
CREATE TABLE prod.video_files (
  file_id STRING NOT NULL,
  nas_path STRING,
  file_name STRING,
  event_id STRING,
  duration_seconds FLOAT64,
  file_size_bytes INT64,
  resolution STRING,
  codec STRING,
  bitrate_kbps INT64,
  fps FLOAT64,
  proxy_gcs_path STRING,
  is_archived BOOL DEFAULT FALSE,
  created_at TIMESTAMP,
  scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

## 로컬 개발

### 1. NAS 마운트

```bash
# NFS 마운트 (Linux/Mac)
sudo mount -t nfs nas-server:/volume1/poker /nas/poker

# Windows (SMB)
net use Z: \\nas-server\poker
```

### 2. FFmpeg 설치

```bash
# Ubuntu
sudo apt install ffmpeg

# Mac
brew install ffmpeg

# 버전 확인
ffmpeg -version  # 최소 4.4 이상
```

### 3. 환경 설정

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

**requirements.txt**:
```txt
ffmpeg-python==0.2.0
google-cloud-bigquery==3.13.0
google-cloud-storage==2.10.0
flask==3.0.0
gunicorn==21.2.0
pytest==7.4.3
```

### 4. 로컬 실행

```bash
# API 서버 실행
python src/main.py

# 테스트 스캔
curl -X POST http://localhost:8002/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "nas_path": "/nas/poker/test/",
    "recursive": false,
    "generate_proxy": false
  }'
```

---

## FFmpeg 메타데이터 추출

**핵심 로직**:

```python
# src/metadata_extractor.py
import ffmpeg

def extract_metadata(video_path: str) -> dict:
    """FFmpeg Probe로 메타데이터 추출"""
    try:
        probe = ffmpeg.probe(video_path)

        # 비디오 스트림
        video_stream = next(
            (s for s in probe['streams'] if s['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            raise ValueError("No video stream found")

        # 메타데이터 반환
        return {
            'duration': float(probe['format']['duration']),
            'file_size': int(probe['format']['size']),
            'resolution': f"{video_stream['width']}x{video_stream['height']}",
            'codec': video_stream['codec_name'],
            'bitrate': int(probe['format'].get('bit_rate', 0)) // 1000,  # kbps
            'fps': eval(video_stream.get('r_frame_rate', '0/1'))  # 예: "30000/1001"
        }
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
```

---

## 720p 프록시 생성

**최적화된 FFmpeg 명령**:

```python
# src/proxy_generator.py
import ffmpeg

def generate_proxy_720p(input_path: str, output_path: str, quality='medium'):
    """
    720p H.264 프록시 생성

    CRF 값:
    - high: 18 (높은 품질, ~5GB for 10h video)
    - medium: 23 (균형, ~3GB)
    - low: 28 (낮은 품질, ~2GB)
    """

    crf_map = {'high': 18, 'medium': 23, 'low': 28}
    crf = crf_map.get(quality, 23)

    stream = ffmpeg.input(input_path)
    stream = ffmpeg.filter(stream, 'scale', 1280, 720)
    stream = ffmpeg.output(
        stream,
        output_path,
        vcodec='libx264',
        crf=crf,
        preset='medium',  # 속도 vs 품질 (fast, medium, slow)
        acodec='aac',
        audio_bitrate='128k',
        movflags='faststart'  # 웹 스트리밍 최적화
    )

    # 실행 (Progress 콜백 포함)
    ffmpeg.run(stream, overwrite_output=True)
```

**예상 처리 시간**:
- 10시간 영상 (50GB) → 720p (3GB): ~20분 (6코어 CPU)
- 병렬 처리 시 15개 파일 동시 처리 가능

---

## 배포

### Cloud Run 배포

```bash
gcloud run deploy video-metadata-service \
  --source . \
  --region us-central1 \
  --service-account video-metadata-sa@gg-poker.iam.gserviceaccount.com \
  --set-env-vars "BIGQUERY_DATASET=prod,GCS_BUCKET=gg-proxy" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600s \
  --max-instances 10
```

**NAS 접근 설정**:
- Cloud Run은 NAS 직접 마운트 불가
- **해결책**: GCS FUSE 또는 별도 Worker VM 사용

---

## 성능 최적화

### 병렬 처리

```python
# src/scanner.py
from concurrent.futures import ThreadPoolExecutor

def scan_directory_parallel(nas_path: str, max_workers=10):
    """병렬 스캔 (I/O bound)"""

    video_files = find_all_videos(nas_path)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(extract_metadata, video_files))

    return results
```

### 프록시 생성 최적화

```python
# GPU 가속 (NVIDIA)
def generate_proxy_gpu(input_path, output_path):
    stream = ffmpeg.input(input_path)
    stream = ffmpeg.output(
        stream,
        output_path,
        vcodec='h264_nvenc',  # GPU 인코더
        preset='fast',
        crf=23
    )
    ffmpeg.run(stream)
```

---

## 모니터링

### Cloud Logging

```bash
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=video-metadata-service \
  AND severity>=ERROR" \
  --limit 50
```

### 주요 지표

- **스캔 속도**: files_scanned_per_hour
- **프록시 생성 실패율**: proxy_generation_error_rate
- **NAS I/O 대기 시간**: nas_read_latency_ms

---

## 트러블슈팅

### 1. NAS 마운트 실패

```bash
# 마운트 확인
mount | grep nas

# 권한 확인
ls -la /nas/poker/
```

### 2. FFmpeg 메모리 부족

**증상**:
```
Conversion failed: Cannot allocate memory
```

**해결**:
```bash
# Cloud Run 메모리 증가
gcloud run services update video-metadata-service --memory 8Gi
```

### 3. 프록시 생성 속도 개선

**현재**: 10시간 영상 → 20분
**개선 방법**:
1. GPU 사용 (`h264_nvenc`) → ~5분
2. `preset=ultrafast` → ~10분 (품질 저하)
3. 해상도 낮춤 (480p) → ~8분

---

## 개발 체크리스트

- [x] OpenAPI 스펙 작성
- [ ] NAS 마운트 설정
- [ ] FFmpeg 메타데이터 추출 구현
- [ ] 720p 프록시 생성 구현
- [ ] GCS 업로드 구현
- [ ] BigQuery 테이블 생성
- [ ] POST /v1/scan API 구현
- [ ] GET /v1/files API 구현
- [ ] 유닛 테스트
- [ ] Cloud Run 배포

---

**담당자**: aiden.kim@ggproduction.net
**최종 업데이트**: 2025-11-17
