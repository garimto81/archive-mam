# 🧪 POKER-BRAIN 실행 및 검증 가이드

## 📋 목차

1. [빠른 검증 (5분)](#빠른-검증-5분) - 테스트만 실행
2. [개별 모듈 실행 (30분)](#개별-모듈-실행-30분) - API 서버 실행 + 호출
3. [전체 시스템 통합 (1시간)](#전체-시스템-통합-1시간) - 6개 모듈 연동
4. [데모 시나리오](#데모-시나리오) - 실제 사용 플로우

---

## ⚡ 빠른 검증 (5분)

**목적**: 코드가 실제로 동작하는지 테스트 실행으로 확인

### 1. M4 RAG Search 테스트 (가장 간단)

```bash
cd D:\AI\claude01\archive-mam\modules\m4-rag-search

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 의존성 설치
pip install -r requirements.txt

# 테스트 실행 (66개 테스트, 약 10초 소요)
pytest tests/ -v

# 예상 결과:
# ✅ test_api.py::test_health_endpoint PASSED
# ✅ test_api.py::test_search_endpoint PASSED
# ✅ test_embedding_service.py::test_generate_embedding PASSED
# ... (총 66개 테스트 통과)
```

**검증 가능한 것**:
- ✅ API 엔드포인트 정상 작동
- ✅ 임베딩 생성 로직 정상
- ✅ Vector Search 알고리즘 정상
- ✅ Mock 데이터 로딩 정상
- ✅ 85% 코드 커버리지 확인

---

### 2. M3 Timecode Validation 테스트

```bash
cd D:\AI\claude01\archive-mam\modules\m3-timecode-validation

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

pytest tests/ -v

# 예상 결과:
# ✅ test_sync_scorer.py::test_calculate_sync_score PASSED
# ✅ test_vision_detector.py::test_detect_poker_scene PASSED
# ... (총 38개 테스트 통과)
```

**검증 가능한 것**:
- ✅ sync_score 계산 알고리즘 (vision*50 + duration*30 + player*20)
- ✅ Vision API Mock 동작
- ✅ Offset 자동 계산 로직

---

### 3. M5 Clipping 테스트

```bash
cd D:\AI\claude01\archive-mam\modules\m5-clipping

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

pytest tests/ -v

# 예상 결과:
# ✅ test_ffmpeg_clipper.py::test_clip_video_success PASSED
# ✅ test_pubsub_publisher.py::test_publish_clip_request PASSED
# ... (총 80+ 테스트 통과)
```

**검증 가능한 것**:
- ✅ FFmpeg 클리핑 로직
- ✅ Pub/Sub 메시지 발행/구독
- ✅ GCS 업로드 시뮬레이션
- ✅ 상태 추적 (queued → processing → completed)

---

## 🚀 개별 모듈 실행 (30분)

**목적**: 실제 API 서버를 띄우고 HTTP 요청으로 검증

### 시나리오 1: M4 검색 API 실행 및 테스트

```bash
# Terminal 1: API 서버 실행
cd D:\AI\claude01\archive-mam\modules\m4-rag-search
venv\Scripts\activate
set POKER_ENV=development  # Windows
# export POKER_ENV=development  # Mac/Linux
python -m app.api

# 출력:
# [INFO] Starting M4 RAG Search Service (Development Mode)
# [INFO] Loading mock data from ../../mock_data/bigquery/hand_summary_mock.json
# [INFO] Loaded 100 mock hands
# [INFO] Running on http://0.0.0.0:8004 (Press CTRL+C to quit)
```

```bash
# Terminal 2: API 호출 테스트
# 1. Health Check
curl http://localhost:8004/health

# 예상 응답:
# {
#   "status": "healthy",
#   "service": "m4-rag-search",
#   "version": "1.0.0",
#   "environment": "development",
#   "timestamp": "2025-01-17T10:00:00Z"
# }

# 2. 검색 요청 (Tom Dwan 검색)
curl -X POST http://localhost:8004/v1/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Tom Dwan bluff\", \"limit\": 5}"

# 예상 응답:
# {
#   "query_id": "search-1705489200",
#   "total_results": 12,
#   "results": [
#     {
#       "hand_id": "wsop2024_me_d1_h001",
#       "summary": "Tom Dwan raises pre-flop...",
#       "relevance_score": 0.87,
#       "players": ["Tom Dwan", "Phil Ivey"],
#       "pot_size_usd": 125000
#     },
#     ...
#   ]
# }

# 3. Autocomplete 테스트
curl "http://localhost:8004/v1/search/autocomplete?prefix=Tom"

# 예상 응답:
# {
#   "suggestions": [
#     "Tom Dwan",
#     "Tom Marchese"
#   ]
# }
```

**검증 완료**:
- ✅ API 서버 정상 실행
- ✅ Mock 데이터 로딩 (100개 핸드)
- ✅ 검색 기능 동작 (텍스트 매칭)
- ✅ Autocomplete 동작
- ✅ JSON 응답 형식 정확

---

### 시나리오 2: M3 타임코드 검증 API

```bash
# Terminal 1: M3 API 실행
cd D:\AI\claude01\archive-mam\modules\m3-timecode-validation
venv\Scripts\activate
set POKER_ENV=development
python -m app.api

# 출력: Running on http://0.0.0.0:8003
```

```bash
# Terminal 2: 타임코드 검증 요청
curl -X POST http://localhost:8003/v1/validate ^
  -H "Content-Type: application/json" ^
  -d "{\"hand_id\": \"wsop2024_me_d1_h001\", \"video_path\": \"/nas/poker/test.mp4\", \"timecode_seconds\": 1234}"

# 예상 응답:
# {
#   "validation_id": "val-20250117-001",
#   "hand_id": "wsop2024_me_d1_h001",
#   "sync_score": 85.5,
#   "vision_confidence": 0.92,
#   "duration_match": 0.88,
#   "player_count_match": 0.75,
#   "suggested_offset": 0,
#   "status": "valid"
# }
```

**검증 완료**:
- ✅ Vision API Mock 동작
- ✅ sync_score 계산 정확
- ✅ Offset 자동 계산 (sync_score < 80일 때)

---

### 시나리오 3: M5 클리핑 요청

```bash
# Terminal 1: M5 API 실행
cd D:\AI\claude01\archive-mam\modules\m5-clipping
venv\Scripts\activate
set POKER_ENV=development
python app/api.py

# 출력: Running on http://0.0.0.0:8005
```

```bash
# Terminal 2: M5 Agent 실행 (Worker)
cd D:\AI\claude01\archive-mam\modules\m5-clipping
venv\Scripts\activate
set POKER_ENV=development
python -m local_agent.subscriber

# 출력:
# [INFO] Starting Local Agent (Development Mode)
# [INFO] Pub/Sub Emulator: localhost:8085
# [INFO] Listening to clipping-requests...
```

```bash
# Terminal 3: 클리핑 요청
curl -X POST http://localhost:8005/v1/clip/request ^
  -H "Content-Type: application/json" ^
  -d "{\"hand_id\": \"wsop2024_me_d1_h001\", \"nas_video_path\": \"/nas/poker/test.mp4\", \"start_seconds\": 100, \"end_seconds\": 250}"

# 응답:
# {
#   "request_id": "clip-20250117-001",
#   "hand_id": "wsop2024_me_d1_h001",
#   "status": "queued",
#   "estimated_duration_sec": 30,
#   "queue_position": 1
# }

# 상태 조회 (5초 후)
curl http://localhost:8005/v1/clip/clip-20250117-001/status

# 응답:
# {
#   "request_id": "clip-20250117-001",
#   "status": "completed",
#   "output_gcs_path": "gs://gg-subclips/wsop2024_me_d1_h001.mp4",
#   "download_url": "https://storage.googleapis.com/...",
#   "file_size_bytes": 52428800
# }
```

**검증 완료**:
- ✅ Pub/Sub 비동기 처리
- ✅ FFmpeg Mock 동작 (실제로는 스킵)
- ✅ 상태 변경: queued → processing → completed
- ✅ Signed URL 생성

---

## 🌐 전체 시스템 통합 (1시간)

**목적**: 6개 모듈을 모두 실행하고 Web UI로 전체 플로우 테스트

### Step 1: 모든 Backend 실행

```bash
# 6개 터미널 준비 (또는 tmux/screen 사용)

# Terminal 1: M1 (포트 8001)
cd modules/m1-data-ingestion
venv\Scripts\activate
set POKER_ENV=development
python -m app.api

# Terminal 2: M2 (포트 8002)
cd modules/m2-video-metadata
venv\Scripts\activate
set POKER_ENV=development
python -m app.api

# Terminal 3: M3 (포트 8003)
cd modules/m3-timecode-validation
venv\Scripts\activate
set POKER_ENV=development
python -m app.api

# Terminal 4: M4 (포트 8004)
cd modules/m4-rag-search
venv\Scripts\activate
set POKER_ENV=development
python -m app.api

# Terminal 5: M5 API (포트 8005)
cd modules/m5-clipping
venv\Scripts\activate
set POKER_ENV=development
python app/api.py

# Terminal 6: M5 Agent
cd modules/m5-clipping
venv\Scripts\activate
set POKER_ENV=development
python -m local_agent.subscriber
```

### Step 2: Web UI 실행

```bash
# Terminal 7: M6 Web UI (포트 3000)
cd modules/m6-web-ui
npm install  # 최초 1회만
npm run dev

# 출력:
# ▲ Next.js 14.0.0
# - Local:        http://localhost:3000
# - Environments: .env.development
```

### Step 3: 브라우저로 접속

```
http://localhost:3000
```

**검증 가능한 전체 플로우**:

1. **검색 플로우**:
   - Home 화면에서 "Tom Dwan" 입력
   - Autocomplete 제안 표시 (M4 API 호출)
   - 검색 버튼 클릭 → `/search` 페이지 이동
   - 검색 결과 목록 표시 (M4 API 호출)
   - 각 핸드에 "즐겨찾기" 버튼 동작

2. **상세 보기 플로우**:
   - 검색 결과에서 핸드 클릭
   - `/hand/wsop2024_me_d1_h001` 페이지 이동
   - 핸드 메타데이터 표시
   - 프록시 영상 플레이어 (M2 Proxy URL)
   - "다운로드" 버튼 클릭

3. **클리핑 다운로드 플로우**:
   - "다운로드" 버튼 클릭 → M5 API 호출
   - 다운로드 페이지 (`/downloads`)로 리다이렉트
   - 상태 폴링: queued → processing → completed (5초 간격)
   - Completed 후 "다운로드" 링크 표시
   - 클릭 시 Signed URL로 파일 다운로드

4. **관리자 대시보드**:
   - `/admin` 페이지 접속
   - M3 타임코드 검증 통계 표시
   - 실시간 새로고침 (30초 간격)

---

## 🎬 데모 시나리오

### 시나리오: "2024 WSOP Main Event Day 3에서 Tom Dwan의 블러프 장면 찾기"

```bash
# 1. Web UI 접속
브라우저: http://localhost:3000

# 2. 검색
입력: "Tom Dwan bluff Main Event 2024"
→ M4 API 호출 (semantic search)
→ 12개 결과 반환

# 3. 결과 필터링
필터: Year = 2024, Event = WSOP Main Event
→ 3개 결과로 좁혀짐

# 4. 상세 보기
클릭: "wsop2024_me_d3_h154"
→ M2 Proxy 영상 재생
→ 타임코드: 03:25:45 ~ 03:28:15 (2분 30초)
→ sync_score: 92.5 (M3 검증 완료)

# 5. 클립 다운로드 요청
클릭: "Download Clip" 버튼
→ M5 API 호출: POST /v1/clip/request
→ request_id: clip-20250117-042

# 6. 다운로드 페이지에서 상태 확인
/downloads 페이지 자동 이동
→ 5초마다 폴링
→ Status: queued (0초)
→ Status: processing (5초)
→ Status: completed (35초)

# 7. 파일 다운로드
클릭: "Download" 링크
→ GCS Signed URL 다운로드
→ wsop2024_me_d3_h154.mp4 (50MB, 2분 30초)
```

**검증 완료**:
- ✅ M4 Semantic Search 동작
- ✅ M2 Proxy 영상 재생
- ✅ M3 타임코드 검증
- ✅ M5 비동기 클리핑
- ✅ M6 UI 모든 페이지 동작
- ✅ 전체 플로우 end-to-end 성공

---

## 📊 검증 체크리스트

### 개별 모듈 검증

- [ ] **M1**: `pytest tests/` 통과 (48 tests)
- [ ] **M2**: `pytest tests/` 통과 (64 tests)
- [ ] **M3**: `pytest tests/` 통과 (38 tests)
- [ ] **M4**: `pytest tests/` 통과 (66 tests)
- [ ] **M5**: `pytest tests/` 통과 (80+ tests)
- [ ] **M6**: `npm test` 통과 (70+ tests)

### API 서버 검증

- [ ] **M1**: `curl http://localhost:8001/health` → 200 OK
- [ ] **M2**: `curl http://localhost:8002/health` → 200 OK
- [ ] **M3**: `curl http://localhost:8003/health` → 200 OK
- [ ] **M4**: `curl http://localhost:8004/health` → 200 OK
- [ ] **M5**: `curl http://localhost:8005/health` → 200 OK
- [ ] **M6**: `curl http://localhost:3000/api/health` → 200 OK

### 통합 플로우 검증

- [ ] **검색**: M6 → M4 → 결과 표시
- [ ] **상세보기**: M6 → M2 Proxy URL → 영상 재생
- [ ] **타임코드**: M6 → M3 → sync_score 표시
- [ ] **클리핑**: M6 → M5 → 다운로드 URL 생성
- [ ] **전체 플로우**: 검색 → 상세 → 다운로드 → 완료

---

## 🐛 트러블슈팅

### 문제 1: "포트 이미 사용 중" 에러

```bash
# 포트 확인
netstat -ano | findstr :8004

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

### 문제 2: Mock 데이터 로딩 실패

```bash
# 경로 확인
cd modules/m4-rag-search
ls ../../mock_data/bigquery/hand_summary_mock.json

# 파일이 있는지 확인
# 없으면: mock_data 디렉토리 생성 필요
```

### 문제 3: 의존성 설치 실패

```bash
# Python 버전 확인 (3.11+ 필요)
python --version

# pip 업그레이드
python -m pip install --upgrade pip

# 재시도
pip install -r requirements.txt
```

---

## 🎯 추천 검증 순서

### 초보자 (처음 실행)
1. ✅ M4 테스트 실행 (5분)
2. ✅ M4 API 서버 실행 + curl 테스트 (10분)
3. ✅ M6 Web UI 실행 + 검색 테스트 (15분)

### 중급자 (모든 기능 확인)
1. ✅ 모든 모듈 테스트 실행 (20분)
2. ✅ M3, M4, M5 API 서버 실행 (20분)
3. ✅ M6 Web UI로 전체 플로우 테스트 (30분)

### 고급자 (Production 배포 준비)
1. ✅ 모든 테스트 + 커버리지 확인
2. ✅ Docker 이미지 빌드
3. ✅ E2E 테스트 (Playwright)
4. ✅ 성능 테스트

---

## 📝 정리

**즉시 실행 가능한 것**:
- ✅ **366+ 테스트** - 모든 모듈에서 pytest/jest 실행
- ✅ **6개 API 서버** - localhost:8001~8005, 3000
- ✅ **Web UI** - 브라우저에서 전체 플로우 테스트
- ✅ **Mock 데이터** - 실제 GCP 없이 로컬 테스트 가능

**검증 완료 시 얻는 것**:
- ✅ 코드가 실제로 동작함을 확인
- ✅ API 엔드포인트 정상 작동 확인
- ✅ 전체 시스템 통합 확인
- ✅ Production 배포 전 신뢰도 확보

**다음 단계**:
- Production 환경 변수 설정 (`POKER_ENV=production`)
- GCP 프로젝트 연동
- Cloud Run 배포
- 실제 데이터로 E2E 테스트
