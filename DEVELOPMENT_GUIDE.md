# POKER-BRAIN 실전 개발 시작 가이드

**버전**: 1.0.0
**작성일**: 2025-11-17
**대상**: 6개 모듈 개발 팀원 (Alice, Bob, Charlie, David, Eve, Frank)

---

## 목차

1. [개발 시작 전 체크리스트](#1-개발-시작-전-체크리스트)
2. [개발 환경 설정](#2-개발-환경-설정)
3. [모듈별 개발 가이드](#3-모듈별-개발-가이드)
4. [에이전트 활용 전략](#4-에이전트-활용-전략)
5. [팀 협업 워크플로우](#5-팀-협업-워크플로우)
6. [개발 단계별 가이드](#6-개발-단계별-가이드)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 개발 시작 전 체크리스트

### 필수 사전 준비

- [ ] **GCP 프로젝트 생성 완료** (`gg-poker`)
- [ ] **GCP 권한 확보**
  - BigQuery Admin (또는 dataEditor)
  - Cloud Run Admin
  - Storage Admin
  - Service Account User
- [ ] **로컬 개발 환경**
  - Python 3.11+
  - Node.js 18+ (M6 담당자만)
  - Docker Desktop
  - gcloud CLI
- [ ] **Git 저장소 클론**
  ```bash
  git clone https://github.com/garimto81/archive-mam.git
  cd archive-mam
  ```
- [ ] **Claude Code 에이전트 확인**
  - `.claude/plugins/` 폴더 내 5개 신규 에이전트 확인

### 문서 읽기 (필수)

1. **아키텍처 이해** (30분)
   - `docs/architecture_modular.md`
   - 6개 모듈 구조 파악
   - 의존성 그래프 이해

2. **에이전트 시스템** (20분)
   - `.claude/plugins/README.md`
   - 자신이 담당할 모듈의 전문 에이전트 파악

3. **API 스펙 리뷰** (20분)
   - 담당 모듈의 OpenAPI 스펙 확인
   - 예: M1 담당자 → `modules/data-ingestion/openapi.yaml`

---

## 2. 개발 환경 설정

### 2.1 GCP 인증 설정

```bash
# 1. gcloud 로그인
gcloud auth login

# 2. Application Default Credentials 설정
gcloud auth application-default login

# 3. 프로젝트 설정
gcloud config set project gg-poker

# 4. 권한 확인
gcloud projects get-iam-policy gg-poker \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

### 2.2 Python 환경 설정 (M1-M5)

```bash
# 담당 모듈 디렉토리로 이동
cd modules/data-ingestion  # 예: M1

# 가상환경 생성
python -m venv venv

# 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (requirements.txt 생성 후)
pip install -r requirements.txt
```

**기본 requirements.txt** (예시):
```txt
# M1: Data Ingestion
apache-beam[gcp]==2.52.0
google-cloud-bigquery==3.13.0
google-cloud-pubsub==2.18.4
pytest==7.4.3
pytest-cov==4.1.0
flask==3.0.0  # API 서버용
```

### 2.3 Node.js 환경 설정 (M6)

```bash
cd modules/web-ui

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 2.4 Docker Compose 설정 (통합 테스트용)

루트 디렉토리에 `docker-compose.yml` 생성:

```yaml
version: '3.8'

services:
  data-ingestion:
    build: ./modules/data-ingestion
    ports:
      - "8001:8080"
    environment:
      - GOOGLE_CLOUD_PROJECT=gg-poker
      - BIGQUERY_DATASET=dev

  video-metadata:
    build: ./modules/video-metadata
    ports:
      - "8002:8080"

  rag-search:
    build: ./modules/rag-search
    ports:
      - "8004:8080"

  web-ui:
    build: ./modules/web-ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=http://localhost:8004
```

실행:
```bash
docker-compose up
```

---

## 3. 모듈별 개발 가이드

### M1: Data Ingestion Service (Alice)

**목표**: ATI 데이터 → BigQuery ETL

**시작 순서**:

1. **OpenAPI 스펙 확인** ✅ (이미 완료)
   ```bash
   cat modules/data-ingestion/openapi.yaml
   ```

2. **BigQuery 테이블 생성**
   ```bash
   cd modules/data-ingestion
   bq mk --dataset gg-poker:prod
   bq mk --table prod.hand_summary schema/hand_summary.json
   ```

3. **Dataflow 파이프라인 구현**
   ```bash
   # Claude Code 에이전트 활용
   "data-engineer를 사용하여 Apache Beam 파이프라인 구현 (src/ingest_pipeline.py)"
   ```

4. **API 서버 구현**
   ```bash
   # Flask API 구현
   touch src/main.py
   # Claude Code: "POST /v1/ingest 엔드포인트 구현해줘"
   ```

5. **유닛 테스트**
   ```bash
   # test-automator 에이전트 활용
   "test-automator를 사용하여 src/ingest_pipeline.py 유닛 테스트 작성"
   ```

6. **로컬 테스트**
   ```bash
   python src/ingest_pipeline.py \
     --input sample.jsonl \
     --output dev.test_table \
     --runner DirectRunner
   ```

**에이전트 사용 예시**:
```
사용자: "data-engineer를 사용하여 M1 Dataflow 파이프라인 구현 (src/ingest_pipeline.py)"

Claude Code (data-engineer):
1. Apache Beam 파이프라인 코드 작성
2. JSON Lines 파싱 로직
3. BigQuery 적재 로직
4. 에러 핸들링
```

---

### M2: Video Metadata Service (Bob)

**목표**: NAS 스캔 → 메타데이터 추출 → 프록시 생성

**시작 순서**:

1. **OpenAPI 스펙 작성**
   ```bash
   "video-processing-engineer를 사용하여 M2 OpenAPI 스펙 작성"
   ```

2. **NAS 마운트 테스트**
   ```bash
   # NAS 접근 확인
   ls /nas/poker/2024/wsop/
   ```

3. **FFmpeg 메타데이터 추출 구현**
   ```bash
   "video-processing-engineer를 사용하여 FFmpeg 메타데이터 추출 로직 구현 (src/metadata_extractor.py)"
   ```

4. **프록시 생성 로직 구현**
   ```bash
   "video-processing-engineer를 사용하여 720p 프록시 생성 로직 구현 (src/proxy_generator.py)"
   ```

5. **API 서버 구현**
   ```bash
   # POST /v1/scan 구현
   "video-processing-engineer를 사용하여 POST /v1/scan API 구현"
   ```

**핵심 코드 예시** (에이전트가 생성):
```python
# src/metadata_extractor.py
import ffmpeg

def extract_metadata(video_path: str) -> dict:
    probe = ffmpeg.probe(video_path)
    video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)

    return {
        'duration': float(probe['format']['duration']),
        'resolution': f"{video_stream['width']}x{video_stream['height']}",
        'codec': video_stream['codec_name'],
        'file_size': int(probe['format']['size'])
    }
```

---

### M3: Timecode Validation Service (Charlie)

**목표**: ATI 타임스탬프 ↔ NAS 영상 동기화 검증

**시작 순서**:

1. **OpenAPI 스펙 작성**
   ```bash
   "validation-engineer를 사용하여 M3 OpenAPI 스펙 작성"
   ```

2. **Vision API 설정**
   ```bash
   # Vision API 활성화
   gcloud services enable vision.googleapis.com
   ```

3. **sync_score 알고리즘 구현**
   ```bash
   "validation-engineer를 사용하여 sync_score 계산 알고리즘 구현 (src/timecode_validator.py)"
   ```

4. **Vision API 통합**
   ```bash
   "validation-engineer를 사용하여 Vision API 통합 (포커 장면 감지)"
   ```

**핵심 알고리즘** (에이전트가 생성):
```python
# src/timecode_validator.py
def calculate_sync_score(hand, video_path, use_vision=True) -> float:
    score = 0.0

    # Vision API (50점)
    if use_vision:
        vision_result = detect_poker_scene(video_path, hand.timestamp_start)
        if vision_result['confidence'] > 0.8:
            score += 50

    # Duration match (30점)
    expected_duration = (hand.timestamp_end - hand.timestamp_start).total_seconds()
    # ... 검증 로직

    # Player count (20점)
    # ... 검증 로직

    return score
```

---

### M4: RAG Search Service (David)

**목표**: Vertex AI 기반 자연어 검색

**시작 순서**:

1. **OpenAPI 스펙 작성**
   ```bash
   "ai-engineer를 사용하여 M4 RAG Search OpenAPI 스펙 작성"
   ```

2. **Vertex AI 설정**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Embedding 파이프라인 구현**
   ```bash
   "ai-engineer를 사용하여 TextEmbedding-004 통합 (src/embedding_generator.py)"
   ```

4. **Vector Search 구현**
   ```bash
   "ai-engineer를 사용하여 Vertex AI Vector Search 통합 (src/rag_engine.py)"
   ```

**에이전트 활용**:
```
"ai-engineer를 사용하여 RAG 검색 파이프라인 구현:
1. 쿼리 → Embedding
2. Vector Search
3. BigQuery 조인
4. Re-ranking"
```

---

### M5: Clipping Service (Eve)

**목표**: Pub/Sub 기반 비동기 비디오 클리핑

**시작 순서**:

1. **OpenAPI 스펙 작성**
   ```bash
   "video-pipeline-engineer를 사용하여 M5 Clipping Service 설계"
   ```

2. **Pub/Sub 토픽 생성**
   ```bash
   gcloud pubsub topics create clipping-requests
   gcloud pubsub topics create clipping-complete
   gcloud pubsub subscriptions create clipping-worker \
     --topic=clipping-requests
   ```

3. **Local Agent 구현**
   ```bash
   "video-pipeline-engineer를 사용하여 Local Clipping Agent 구현 (systemd)"
   ```

4. **FFmpeg 클리핑 로직**
   ```bash
   "video-pipeline-engineer를 사용하여 FFmpeg 서브클립 생성 로직 구현 (고속 -c copy)"
   ```

**Daemon 예시** (에이전트가 생성):
```python
# src/clipping_agent.py
class ClippingAgent:
    def run(self):
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = "projects/gg-poker/subscriptions/clipping-worker"

        def callback(message):
            data = json.loads(message.data)
            self.process_clip(data)
            message.ack()

        subscriber.subscribe(subscription_path, callback=callback)
        # Keep alive
        while True:
            time.sleep(60)
```

---

### M6: Web UI Service (Frank)

**목표**: 검색 UI + 미리보기 + 다운로드

**시작 순서**:

1. **Next.js 프로젝트 초기화**
   ```bash
   cd modules/web-ui
   npx create-next-app@latest . --typescript --tailwind --app
   ```

2. **검색 UI 구현**
   ```bash
   "frontend-developer를 사용하여 검색 페이지 구현 (app/page.tsx)"
   ```

3. **M4 API 통합**
   ```bash
   "frontend-developer를 사용하여 M4 RAG Search API 통합 (app/api/search/route.ts)"
   ```

4. **비디오 미리보기**
   ```bash
   "frontend-developer를 사용하여 프록시 영상 플레이어 구현 (components/VideoPreview.tsx)"
   ```

**에이전트 활용**:
```
"frontend-developer를 사용하여:
1. 검색 폼 (shadcn/ui)
2. 검색 결과 그리드
3. 비디오 플레이어 (react-player)
4. 다운로드 버튼"
```

---

## 4. 에이전트 활용 전략

### 4.1 모듈별 주 에이전트

| 모듈 | 주 에이전트 | 보조 에이전트 |
|------|------------|-------------|
| M1 | data-engineer | test-automator, code-reviewer |
| M2 | video-processing-engineer | test-automator, performance-engineer |
| M3 | validation-engineer | ai-engineer, debugger |
| M4 | ai-engineer | performance-engineer, security-auditor |
| M5 | video-pipeline-engineer | deployment-engineer, devops-troubleshooter |
| M6 | frontend-developer | ui-ux-designer, playwright-engineer |

### 4.2 통합 작업 시 에이전트

**API 설계 단계 (Week 1)**:
```bash
"microservices-pm을 사용하여 6개 모듈 OpenAPI 스펙 검토 및 의존성 그래프 생성"
```

**통합 테스트 단계 (Week 7)**:
```bash
"integration-qa-orchestrator를 사용하여 M1→M3 통합 테스트 작성"
"integration-qa-orchestrator를 사용하여 검색→다운로드 E2E 테스트 작성"
```

### 4.3 에이전트 호출 패턴

**패턴 1: 설계 단계**
```
"{agent}를 사용하여 {모듈} OpenAPI 스펙 작성"

예:
"video-processing-engineer를 사용하여 M2 OpenAPI 스펙 작성"
```

**패턴 2: 구현 단계**
```
"{agent}를 사용하여 {기능} 구현 ({파일명})"

예:
"validation-engineer를 사용하여 sync_score 계산 알고리즘 구현 (src/timecode_validator.py)"
```

**패턴 3: 테스트 단계**
```
"{agent}를 사용하여 {파일} 유닛 테스트 작성"

예:
"test-automator를 사용하여 src/ingest_pipeline.py 유닛 테스트 작성"
```

**패턴 4: 통합 단계**
```
"{agent}를 사용하여 {모듈A}→{모듈B} 통합 테스트 작성"

예:
"integration-qa-orchestrator를 사용하여 M6→M4→M5 E2E 테스트 작성"
```

---

## 5. 팀 협업 워크플로우

### Week 1-2: API 계약 설계

**목표**: 6개 모듈의 OpenAPI 스펙 확정

**워크플로우**:

1. **개별 스펙 작성** (각자)
   - M1: Alice → `modules/data-ingestion/openapi.yaml` ✅
   - M2: Bob → `modules/video-metadata/openapi.yaml`
   - M3: Charlie → `modules/timecode-validation/openapi.yaml`
   - M4: David → `modules/rag-search/openapi.yaml`
   - M5: Eve → `modules/clipping/openapi.yaml`
   - M6: Frank → `modules/web-ui/openapi.yaml`

2. **PM 검토** (전체)
   ```bash
   "microservices-pm을 사용하여 6개 모듈 OpenAPI 스펙 검토"
   ```

3. **피드백 반영** (각자)

4. **스펙 확정 및 Mock API 구축**
   - Postman Mock Server 또는
   - Prism (OpenAPI Mock Server)
   ```bash
   npm install -g @stoplight/prism-cli
   prism mock modules/data-ingestion/openapi.yaml
   ```

### Week 3-6: 병렬 개발

**원칙**: 각 모듈은 **독립적으로** 개발

**의존성 해결**:
- M1, M2는 의존성 없음 → **먼저 시작**
- M3는 M1, M2 완료 후 시작
- M4는 M1 완료 후 시작
- M5는 M4 완료 후 시작 (또는 병렬 Mock)
- M6는 M4, M5 Mock으로 시작

**일일 스탠드업** (15분):
```
- 어제 완료한 작업
- 오늘 할 작업
- 블로커 사항 (의존성 대기 등)
```

**주간 Sync-up** (1시간, 금요일):
```
- 각 모듈 진행률 공유
- 통합 이슈 논의
- 다음 주 계획
```

### Week 7-8: 통합 테스트

**통합 순서**:

1. **Phase 1**: M1 + M3 (데이터 수집 → 검증)
   ```bash
   "integration-qa-orchestrator를 사용하여 M1→M3 통합 테스트 작성"
   ```

2. **Phase 2**: M1 + M4 (데이터 → 검색)
   ```bash
   "integration-qa-orchestrator를 사용하여 M1→M4 통합 테스트 작성"
   ```

3. **Phase 3**: M4 + M5 + M6 (검색 → 클리핑 → UI)
   ```bash
   "integration-qa-orchestrator를 사용하여 검색→다운로드 E2E 테스트 작성"
   ```

**E2E 테스트 환경**:
```bash
# Docker Compose로 모든 서비스 실행
docker-compose up

# Playwright E2E 테스트
"playwright-engineer를 사용하여 전체 워크플로우 E2E 테스트 작성"
```

---

## 6. 개발 단계별 가이드

### Step 1: OpenAPI 스펙 작성

**목표**: API 계약 확정

**체크리스트**:
- [ ] 모든 엔드포인트 정의
- [ ] Request/Response 스키마 정의
- [ ] 에러 응답 표준화
- [ ] 예시 포함
- [ ] PM 검토 완료

**에이전트 활용**:
```bash
"{모듈-agent}를 사용하여 {모듈} OpenAPI 스펙 작성"
"microservices-pm을 사용하여 스펙 검토 및 피드백"
```

---

### Step 2: 유닛 테스트 작성 (TDD)

**목표**: 구현 전 테스트 코드 작성

**예시 (M1)**:
```python
# tests/test_ingest_pipeline.py
import pytest
from src.ingest_pipeline import parse_ati_row

def test_parse_ati_row_valid():
    raw = '{"hand_id":"test_001","players":["Alice","Bob"]}'
    result = parse_ati_row(raw)
    assert result['hand_id'] == 'test_001'
    assert len(result['players']) == 2

def test_parse_ati_row_invalid():
    raw = '{"invalid_json'
    with pytest.raises(ValueError):
        parse_ati_row(raw)
```

**에이전트 활용**:
```bash
"test-automator를 사용하여 src/ingest_pipeline.py 유닛 테스트 작성"
```

---

### Step 3: 구현

**목표**: 기능 구현

**체크리스트**:
- [ ] 코드 작성
- [ ] 유닛 테스트 통과
- [ ] 린터 통과 (`pylint`, `eslint`)
- [ ] 타입 체크 (`mypy`, `TypeScript`)

**에이전트 활용**:
```bash
"{모듈-agent}를 사용하여 {기능} 구현"
"debugger를 사용하여 {에러} 수정"
"code-reviewer를 사용하여 코드 리뷰"
```

---

### Step 4: 로컬 테스트

**M1 예시**:
```bash
# 로컬 Dataflow 실행
python src/ingest_pipeline.py \
  --input sample.jsonl \
  --output dev.test_table \
  --runner DirectRunner

# 결과 확인
bq query "SELECT * FROM dev.test_table LIMIT 10"
```

**M6 예시**:
```bash
# 개발 서버 실행
npm run dev

# 브라우저에서 확인
open http://localhost:3000
```

---

### Step 5: Cloud 배포

**Cloud Run 배포**:
```bash
cd modules/{module-name}

gcloud run deploy {service-name} \
  --source . \
  --region us-central1 \
  --allow-unauthenticated=false
```

**에이전트 활용**:
```bash
"deployment-engineer를 사용하여 {모듈} Cloud Run 배포 스크립트 작성"
```

---

### Step 6: 통합 테스트

**예시 (M1 → M3)**:
```python
# tests/integration/test_m1_to_m3.py
@pytest.mark.integration
def test_data_ingestion_to_validation():
    # 1. M1: 데이터 수집
    ingest_response = requests.post(
        "https://data-ingestion-service-prod.run.app/v1/ingest",
        json={"gcs_path": "gs://test/sample.jsonl", ...}
    )
    job_id = ingest_response.json()['job_id']

    # 2. 완료 대기
    wait_for_completion(job_id, timeout=300)

    # 3. M3: 검증 시작
    validate_response = requests.post(
        "https://timecode-validation-service-prod.run.app/v1/validate",
        json={"hand_id": "test_001", ...}
    )

    # 4. 검증
    assert validate_response.json()['sync_score'] > 80
```

**에이전트 활용**:
```bash
"integration-qa-orchestrator를 사용하여 M1→M3 통합 테스트 작성"
```

---

## 7. 트러블슈팅

### 문제 1: "Permission denied" (BigQuery)

**증상**:
```
google.api_core.exceptions.Forbidden: 403 Access Denied
```

**해결**:
```bash
# Service Account에 권한 부여
gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:your-sa@gg-poker.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

---

### 문제 2: NAS 마운트 실패 (M2, M5)

**증상**:
```
FileNotFoundError: /nas/poker/...
```

**해결**:
```bash
# NAS 마운트 확인
mount | grep nas

# 재마운트
sudo mount -t nfs nas-server:/volume1/poker /nas/poker
```

---

### 문제 3: Vision API Quota 초과 (M3)

**증상**:
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**해결**:
1. GCP Console → IAM → Quotas
2. Vision API requests per minute 증가 요청
3. 또는 배치 처리로 속도 조절

---

### 문제 4: Pub/Sub 메시지 누락 (M5)

**증상**:
```
클리핑 요청이 처리되지 않음
```

**해결**:
```bash
# Dead Letter Queue 확인
gcloud pubsub subscriptions describe clipping-worker

# 재처리
gcloud pubsub subscriptions seek clipping-worker --time=TIMESTAMP
```

---

## 부록 A: 전체 개발 타임라인

```
Week 1-2: API 설계
├─ Week 1
│  ├─ Day 1-3: 개별 OpenAPI 스펙 작성
│  ├─ Day 4: PM 검토
│  └─ Day 5: 피드백 반영
└─ Week 2
   ├─ Day 1-3: Mock API 구축
   └─ Day 4-5: 통합 테스트 시나리오 작성

Week 3-6: 병렬 개발
├─ Week 3
│  ├─ M1 (Alice): Dataflow 파이프라인 구현
│  ├─ M2 (Bob): NAS 스캔 로직 구현
│  └─ M6 (Frank): UI 스켈레톤 구현
├─ Week 4
│  ├─ M1: API 서버 구현
│  ├─ M3 (Charlie): Vision API 통합
│  └─ M4 (David): Embedding 파이프라인
├─ Week 5
│  ├─ M2: 프록시 생성 로직
│  ├─ M4: Vector Search 구현
│  └─ M5 (Eve): Local Agent 구현
└─ Week 6
   ├─ M3: sync_score 알고리즘 완성
   ├─ M5: HA 설정
   └─ M6: M4, M5 API 통합

Week 7-8: 통합 테스트
├─ Week 7
│  ├─ M1 + M3 통합 테스트
│  ├─ M1 + M4 통합 테스트
│  └─ M6 + M4 통합 테스트
└─ Week 8
   ├─ M4 + M5 + M6 E2E 테스트
   ├─ 버그 수정
   └─ 성능 최적화

Week 9: Production 배포
├─ Day 1-2: Staging 환경 배포
├─ Day 3: 사용성 테스트
├─ Day 4: Production 배포
└─ Day 5: 모니터링 및 안정화
```

---

## 부록 B: 유용한 명령어 모음

### BigQuery

```bash
# 데이터 조회
bq query "SELECT * FROM prod.hand_summary LIMIT 10"

# 스키마 확인
bq show --schema prod.hand_summary

# 테이블 삭제
bq rm -f prod.hand_summary
```

### Cloud Run

```bash
# 서비스 목록
gcloud run services list

# 로그 확인
gcloud run services logs read data-ingestion-service --limit=50

# 서비스 삭제
gcloud run services delete data-ingestion-service
```

### Pub/Sub

```bash
# 메시지 발행 (테스트용)
gcloud pubsub topics publish clipping-requests \
  --message='{"hand_id":"test_001",...}'

# 구독 목록
gcloud pubsub subscriptions list
```

### Docker

```bash
# 이미지 빌드
docker build -t data-ingestion:latest .

# 로컬 실행
docker run -p 8001:8080 data-ingestion:latest

# 로그 확인
docker logs -f <container-id>
```

---

## 부록 C: 추천 VSCode Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-toolsai.jupyter",
    "googlecloudtools.cloudcode",
    "42crunch.vscode-openapi",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss"
  ]
}
```

---

**문서 작성자**: Claude (GG Production AI Assistant)
**최종 검토**: aiden.kim@ggproduction.net
**다음 단계**: 각 팀원은 자신의 모듈 개발 시작

**질문/피드백**: #poker-brain-dev Slack 채널
