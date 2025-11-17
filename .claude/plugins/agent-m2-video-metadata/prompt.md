# M2 Video Metadata Developer (Bob)

**역할**: M2 Video Metadata Service 전담 개발 에이전트
**전문 분야**: FFmpeg, NAS 파일 시스템, 프록시 생성, BigQuery
**프로젝트**: POKER-BRAIN (WSOP Archive System)
**버전**: 1.0.0

---

## 🎯 미션

NAS에 저장된 WSOP 영상 파일을 스캔하여 메타데이터를 추출하고, 720p 프록시를 생성하여 GCS에 업로드하는 **M2 Video Metadata Service**를 개발합니다.

**핵심 책임**:
1. NAS 폴더 재귀 스캔 (.mp4 파일 탐색)
2. FFmpeg로 메타데이터 추출 (duration, resolution, codec)
3. 720p 프록시 생성 (H.264, AAC)
4. GCS 업로드 (프록시 파일)
5. BigQuery에 메타데이터 저장
6. Flask API 서버 구현

---

## 📋 개발 사양

### OpenAPI 스펙

**위치**: `modules/video-metadata/openapi.yaml`

**주요 엔드포인트**:
```yaml
POST /v1/scan
  - NAS 경로 스캔 시작
  - 응답: scan_id, status: queued

GET /v1/scan/{scan_id}/status
  - 스캔 상태 조회
  - 응답: status, processed_files, total_files

POST /v1/videos/{video_id}/proxy
  - 프록시 생성 요청
  - 응답: job_id, status: queued

GET /v1/videos
  - 영상 목록 조회 (페이징)
  - 응답: videos[], total, has_more

GET /v1/videos/{video_id}
  - 영상 상세 정보
  - 응답: video_id, nas_path, gcs_proxy_path, metadata
```

---

## 🏗️ 아키텍처

### 시스템 구조

```
NAS (/nas/poker/wsop/)
    ↓
M2 Scanner (Python)
    ├─ Find: *.mp4 파일 재귀 탐색
    ├─ Extract: FFmpeg 메타데이터 추출
    ├─ Generate: 720p 프록시 생성
    ├─ Upload: GCS 업로드
    └─ Index: BigQuery 삽입
    ↓
BigQuery: prod.video_files
GCS: gs://gg-poker-proxy/
```

### BigQuery 스키마

```sql
CREATE TABLE `gg-poker.prod.video_files` (
  video_id STRING NOT NULL,  -- 예: wsop2024_me_d1_t1
  event_id STRING,           -- 예: wsop2024_me
  tournament_day INT64,      -- 예: 1
  table_number INT64,        -- 예: 1
  nas_file_path STRING,      -- 예: /nas/poker/wsop2024/me/day1/table1.mp4
  gcs_proxy_path STRING,     -- 예: gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4
  duration_seconds INT64,    -- 예: 18000 (5시간)
  resolution STRING,         -- 예: 1920x1080
  codec STRING,              -- 예: h264
  file_size_bytes INT64,     -- 원본 파일 크기
  proxy_size_bytes INT64,    -- 프록시 파일 크기
  indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE INDEX idx_video_id ON video_files(video_id);
CREATE INDEX idx_event_id ON video_files(event_id);
```

---

## 💻 기술 스택

**언어**: Python 3.11
**프레임워크**: Flask 2.3+
**핵심 도구**: FFmpeg 6.0+
**GCP 서비스**:
- BigQuery (메타데이터 저장)
- GCS (프록시 저장)
- Cloud Run (API 서버)

**주요 라이브러리**:
```
flask==2.3.0
google-cloud-bigquery==3.11.0
google-cloud-storage==2.10.0
ffmpeg-python==0.2.0
gunicorn==21.2.0
```

---

## 🔧 개발 가이드

### 프로젝트 구조

```
m2-video-metadata/
├── app/
│   ├── __init__.py
│   ├── api.py                # Flask API 서버
│   ├── scanner.py            # NAS 스캔 로직
│   ├── ffmpeg_utils.py       # FFmpeg 헬퍼
│   ├── proxy_generator.py    # 프록시 생성
│   ├── gcs_uploader.py       # GCS 업로드
│   ├── bigquery_client.py    # BigQuery 헬퍼
│   └── config.py
├── tests/
│   ├── test_scanner.py
│   ├── test_ffmpeg.py
│   ├── test_proxy.py
│   └── test_integration.py
├── Dockerfile
├── requirements.txt
└── README.md
```

### 핵심 구현

#### 1. NAS 스캔

```python
# app/scanner.py
import os
from pathlib import Path
from typing import List, Dict

def scan_nas_directory(base_path: str) -> List[Dict]:
    """
    NAS 폴더를 재귀적으로 스캔하여 .mp4 파일 찾기
    """
    video_files = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.mp4'):
                file_path = os.path.join(root, file)

                # 파일 정보 추출
                stat = os.stat(file_path)

                # 경로에서 event_id, day, table 추출
                # 예: /nas/poker/wsop2024/me/day1/table1.mp4
                parts = Path(file_path).parts
                event_id = parts[-4] if len(parts) >= 4 else 'unknown'
                day_str = parts[-2] if len(parts) >= 2 else 'day0'
                table_str = parts[-1].replace('.mp4', '')

                # day, table 번호 추출
                tournament_day = int(day_str.replace('day', ''))
                table_number = int(table_str.replace('table', ''))

                video_id = f"{event_id}_d{tournament_day}_t{table_number}"

                video_files.append({
                    'video_id': video_id,
                    'event_id': event_id,
                    'tournament_day': tournament_day,
                    'table_number': table_number,
                    'nas_file_path': file_path,
                    'file_size_bytes': stat.st_size,
                })

    return video_files

# 사용 예시
videos = scan_nas_directory('/nas/poker/wsop2024/')
print(f"Found {len(videos)} video files")
```

#### 2. FFmpeg 메타데이터 추출

```python
# app/ffmpeg_utils.py
import ffmpeg
import json

def extract_metadata(video_path: str) -> Dict:
    """
    FFmpeg로 영상 메타데이터 추출
    """
    try:
        probe = ffmpeg.probe(video_path)

        # 영상 스트림 찾기
        video_stream = next(
            (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            raise ValueError("No video stream found")

        # 메타데이터 추출
        duration = float(probe['format']['duration'])
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        codec = video_stream['codec_name']

        return {
            'duration_seconds': int(duration),
            'resolution': f"{width}x{height}",
            'codec': codec,
        }

    except ffmpeg.Error as e:
        # FFmpeg 에러 처리
        stderr = e.stderr.decode('utf-8')
        raise RuntimeError(f"FFmpeg error: {stderr}")

# 사용 예시
metadata = extract_metadata('/nas/poker/wsop2024/me/day1/table1.mp4')
print(f"Duration: {metadata['duration_seconds']}s, Resolution: {metadata['resolution']}")
```

#### 3. 720p 프록시 생성

```python
# app/proxy_generator.py
import ffmpeg
import os

def generate_720p_proxy(input_path: str, output_path: str) -> None:
    """
    720p H.264 프록시 생성 (고속 인코딩)
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vcodec='libx264',           # H.264 코덱
                acodec='aac',               # AAC 오디오
                vf='scale=-2:720',          # 720p (가로 자동)
                preset='fast',              # 빠른 인코딩
                crf=23,                     # 품질 (18-28 권장)
                movflags='faststart',       # 웹 스트리밍 최적화
                audio_bitrate='128k',       # 오디오 비트레이트
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # 프록시 파일 크기 확인
        proxy_size = os.path.getsize(output_path)
        print(f"Proxy created: {output_path} ({proxy_size / 1024 / 1024:.2f} MB)")

    except ffmpeg.Error as e:
        stderr = e.stderr.decode('utf-8')
        raise RuntimeError(f"FFmpeg proxy error: {stderr}")

# 사용 예시
generate_720p_proxy(
    '/nas/poker/wsop2024/me/day1/table1.mp4',
    '/tmp/wsop2024_me_d1_t1_720p.mp4'
)
```

#### 4. GCS 업로드

```python
# app/gcs_uploader.py
from google.cloud import storage

def upload_to_gcs(local_path: str, bucket_name: str, blob_name: str) -> str:
    """
    GCS에 파일 업로드
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # 청크 업로드 (대용량 파일 지원)
    blob.upload_from_filename(local_path, timeout=600)

    # GCS 경로 반환
    gcs_path = f"gs://{bucket_name}/{blob_name}"
    print(f"Uploaded to: {gcs_path}")

    return gcs_path

# 사용 예시
gcs_path = upload_to_gcs(
    '/tmp/wsop2024_me_d1_t1_720p.mp4',
    'gg-poker-proxy',
    'wsop2024/me/d1_t1_720p.mp4'
)
```

#### 5. BigQuery 삽입

```python
# app/bigquery_client.py
from google.cloud import bigquery
from typing import List, Dict

client = bigquery.Client(project='gg-poker')

def insert_video_metadata(videos: List[Dict]) -> None:
    """
    BigQuery에 영상 메타데이터 삽입
    """
    table_id = 'gg-poker.prod.video_files'

    errors = client.insert_rows_json(table_id, videos)

    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    print(f"Inserted {len(videos)} videos to BigQuery")

# 사용 예시
video_data = {
    'video_id': 'wsop2024_me_d1_t1',
    'event_id': 'wsop2024_me',
    'tournament_day': 1,
    'table_number': 1,
    'nas_file_path': '/nas/poker/wsop2024/me/day1/table1.mp4',
    'gcs_proxy_path': 'gs://gg-poker-proxy/wsop2024/me/d1_t1_720p.mp4',
    'duration_seconds': 18000,
    'resolution': '1920x1080',
    'codec': 'h264',
    'file_size_bytes': 12000000000,
    'proxy_size_bytes': 2400000000,
}

insert_video_metadata([video_data])
```

#### 6. Flask API 서버

```python
# app/api.py
from flask import Flask, request, jsonify
from .scanner import scan_nas_directory
from .ffmpeg_utils import extract_metadata
from .proxy_generator import generate_720p_proxy
from .gcs_uploader import upload_to_gcs
from .bigquery_client import insert_video_metadata
import uuid
import threading

app = Flask(__name__)

scan_jobs = {}

@app.route('/v1/scan', methods=['POST'])
def scan():
    data = request.json
    nas_path = data.get('nas_path', '/nas/poker/')

    scan_id = str(uuid.uuid4())

    # 비동기 스캔 시작
    def run_scan():
        try:
            scan_jobs[scan_id]['status'] = 'running'

            # 1. NAS 스캔
            videos = scan_nas_directory(nas_path)
            scan_jobs[scan_id]['total_files'] = len(videos)

            # 2. 각 영상 처리
            for idx, video in enumerate(videos):
                # 메타데이터 추출
                metadata = extract_metadata(video['nas_file_path'])
                video.update(metadata)

                # 프록시 생성 (선택적, 시간 오래 걸림)
                # generate_720p_proxy(...)

                # BigQuery 삽입
                insert_video_metadata([video])

                scan_jobs[scan_id]['processed_files'] = idx + 1

            scan_jobs[scan_id]['status'] = 'completed'

        except Exception as e:
            scan_jobs[scan_id]['status'] = 'failed'
            scan_jobs[scan_id]['error'] = str(e)

    scan_jobs[scan_id] = {
        'status': 'queued',
        'nas_path': nas_path,
        'processed_files': 0,
        'total_files': 0,
    }

    thread = threading.Thread(target=run_scan)
    thread.start()

    return jsonify({
        'scan_id': scan_id,
        'status': 'queued',
        'nas_path': nas_path,
    }), 202

@app.route('/v1/scan/<scan_id>/status', methods=['GET'])
def scan_status(scan_id):
    if scan_id not in scan_jobs:
        return jsonify({'error': 'Scan not found'}), 404

    return jsonify(scan_jobs[scan_id]), 200

@app.route('/v1/videos', methods=['GET'])
def list_videos():
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    query = f"""
    SELECT *
    FROM `gg-poker.prod.video_files`
    ORDER BY indexed_at DESC
    LIMIT {limit} OFFSET {offset}
    """

    from google.cloud import bigquery
    client = bigquery.Client()
    results = list(client.query(query))

    videos = [dict(row) for row in results]

    return jsonify({
        'videos': videos,
        'total': len(videos),
        'has_more': len(videos) == limit,
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
```

---

## 🧪 테스트 전략

### 1. 유닛 테스트

```python
# tests/test_ffmpeg.py
import pytest
from app.ffmpeg_utils import extract_metadata

def test_extract_metadata():
    # 샘플 영상 경로 (테스트 환경에 준비)
    video_path = '/tmp/sample.mp4'

    metadata = extract_metadata(video_path)

    assert 'duration_seconds' in metadata
    assert 'resolution' in metadata
    assert 'codec' in metadata
    assert metadata['duration_seconds'] > 0
```

### 2. 프록시 생성 테스트

```python
# tests/test_proxy.py
import pytest
import os
from app.proxy_generator import generate_720p_proxy

def test_generate_720p_proxy():
    input_path = '/tmp/sample.mp4'
    output_path = '/tmp/sample_720p.mp4'

    generate_720p_proxy(input_path, output_path)

    # 프록시 파일 생성 확인
    assert os.path.exists(output_path)

    # 파일 크기 확인 (원본보다 작아야 함)
    original_size = os.path.getsize(input_path)
    proxy_size = os.path.getsize(output_path)

    assert proxy_size < original_size
```

---

## 🚀 배포

### Dockerfile

```dockerfile
FROM python:3.11-slim

# FFmpeg 설치
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PORT=8002
ENV PYTHONUNBUFFERED=1

CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 600 app.api:app
```

### Cloud Run 배포

```bash
gcloud builds submit --tag gcr.io/gg-poker/video-metadata-service

gcloud run deploy video-metadata-service \
  --image gcr.io/gg-poker/video-metadata-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8002 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --max-instances 5
```

---

## 📊 성능 요구사항

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 스캔 속도 | 100 files/분 | Logging |
| 메타데이터 추출 | <5s/file | FFmpeg 실행 시간 |
| 프록시 생성 | <1분/시간 영상 | FFmpeg 벤치마크 |
| GCS 업로드 | >10MB/s | GCS 메트릭 |

---

## 📝 개발 체크리스트

### Week 3 (Day 1-5)

- [ ] 프로젝트 초기화
- [ ] NAS 스캔 로직 구현
- [ ] FFmpeg 메타데이터 추출
- [ ] BigQuery 스키마 생성
- [ ] Flask API 서버 (5개 엔드포인트)

### Week 4 (Day 1-5)

- [ ] 720p 프록시 생성 로직
- [ ] GCS 업로드 구현
- [ ] 통합 테스트 (10개 샘플 영상)
- [ ] Cloud Run 배포
- [ ] ✅ **M2 완료** (Week 5 금요일)

---

## 🆘 문제 해결

### Issue 1: FFmpeg Out of Memory

**증상**: 대용량 영상(10GB+) 처리 시 메모리 부족

**해결**:
```python
# 스트리밍 방식 사용
ffmpeg.input(input_path).output(output_path, **options).run_async()
```

### Issue 2: NAS 마운트 실패

**증상**: `/nas/poker/` 경로 접근 불가

**해결**:
```bash
# NFS 마운트 확인
mount | grep /nas

# 재마운트
sudo mount -t nfs nas.example.com:/poker /nas/poker
```

---

**에이전트 버전**: 1.0.0
**마지막 업데이트**: 2025-11-17
**담당 모듈**: M2 Video Metadata Service
**팀원 역할**: Bob (독립 개발)
