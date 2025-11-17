# POKER-BRAIN Specialized Agents

**프로젝트**: archive-mam (WSOP Archive System)
**생성일**: 2025-11-17
**버전**: 1.0.0

---

## 개요

POKER-BRAIN 프로젝트를 위한 **5개 전문 에이전트**가 포함되어 있습니다.
각 에이전트는 특정 모듈(M1-M6)을 담당하며, 독립적으로 개발을 지원합니다.

---

## 신규 에이전트 목록

| 에이전트 ID | 담당 모듈 | 전문 분야 | 토큰 | Phase |
|------------|----------|----------|------|-------|
| **video-processing-engineer** | M2 | FFmpeg, 영상 처리, 프록시 생성 | 1500 | 0, 1 |
| **validation-engineer** | M3 | 타임코드 검증, Vision API, Offset 계산 | 1400 | 0 |
| **video-pipeline-engineer** | M5 | Pub/Sub, Local Agent, HA 설계 | 1500 | 1 |
| **microservices-pm** | ALL | API 계약, 의존성 관리, 통합 조율 | 1600 | 0-2 |
| **integration-qa-orchestrator** | ALL | 통합 테스트, Contract Testing, E2E | 1700 | 1-2 |

---

## 에이전트 상세

### 1. video-processing-engineer

**담당**: M2 (Video Metadata Service)

**전문 분야**:
- FFmpeg 명령어 생성 및 최적화
- 영상 메타데이터 추출 (해상도, 코덱, 비트레이트, 길이)
- 720p 프록시 영상 생성
- NAS/GCS 파일 시스템 통합
- 대용량 파일 병렬 처리

**활용 시점**:
- M2 API 설계 시
- FFmpeg 로직 구현 시
- 프록시 생성 최적화 시
- NAS 스캔 로직 작성 시

**예시 사용**:
```
"video-processing-engineer를 사용하여 M2의 POST /v1/scan API 스펙 작성"

출력:
- OpenAPI YAML
- FFmpeg 메타데이터 추출 로직
- 프록시 생성 최적화 명령어
```

---

### 2. validation-engineer

**담당**: M3 (Timecode Validation Service)

**전문 분야**:
- ATI 타임스탬프 ↔ NAS 영상 타임코드 동기화
- Google Cloud Vision API 통합 (포커 장면 감지)
- Offset 자동 계산 알고리즘
- 통계 기반 신뢰도 점수 계산 (0-100)

**활용 시점**:
- Phase 0 타임코드 검증 시스템 구현 시
- Vision API 통합 시
- sync_score 알고리즘 설계 시
- Offset 계산 로직 작성 시

**예시 사용**:
```
"validation-engineer를 사용하여 sync_score 계산 알고리즘 구현"

출력:
sync_score = (
    vision_confidence * 50 +
    duration_match * 30 +
    player_count * 20
)

if score > 90: "완벽 동기화"
elif score > 80: "양호"
else: "Offset 계산 필요"
```

---

### 3. video-pipeline-engineer

**담당**: M5 (Clipping Service)

**전문 분야**:
- Pub/Sub 기반 비동기 비디오 처리
- FFmpeg 서브클립 생성 (고속 -c copy 모드)
- Local Agent 배포 (NAS 서버)
- High Availability (Primary + Standby)
- systemd Daemon 구현

**활용 시점**:
- M5 클리핑 파이프라인 설계 시
- Pub/Sub Subscriber 구현 시
- Local Agent 배포 시
- HA Failover 설계 시

**예시 사용**:
```
"video-pipeline-engineer를 사용하여 Local Clipping Agent 구현 (systemd)"

출력:
- Python Daemon 코드
- systemd service 파일
- Pub/Sub Subscriber 로직
- Failover 설정
```

---

### 4. microservices-pm

**담당**: 전체 프로젝트 (6개 모듈)

**전문 분야**:
- OpenAPI 3.0 스펙 검증 및 승인
- 모듈 간 의존성 그래프 생성 (Mermaid)
- Breaking Change 자동 감지
- 병렬 개발 전략 수립
- Critical Path 분석

**활용 시점**:
- Week 1: API 계약 설계 단계
- 모듈 간 의존성 분석 필요 시
- API 변경 검토 시
- 통합 일정 조율 시

**예시 사용**:
```
"microservices-pm을 사용하여 6개 모듈의 OpenAPI 스펙 검토 및 의존성 그래프 생성"

출력:
- 6개 모듈 스펙 리뷰 결과
- Mermaid 의존성 다이어그램
- Breaking Change 경고
- 병렬 개발 전략
```

---

### 5. integration-qa-orchestrator

**담당**: 전체 시스템 통합 테스트

**전문 분야**:
- Contract Testing (OpenAPI vs 실제 API)
- 모듈 간 통합 테스트 시나리오 작성
- E2E 테스트 오케스트레이션
- 버그 트리아지 (책임 모듈 식별)
- Staging 환경 관리

**활용 시점**:
- Week 7: 통합 테스트 단계
- Contract Test 작성 시
- E2E 시나리오 설계 시
- 버그 분석 및 할당 시

**예시 사용**:
```
"integration-qa-orchestrator를 사용하여 검색→다운로드 E2E 테스트 작성"

출력:
# tests/integration/test_search_to_download.py
@pytest.mark.integration
def test_full_workflow():
    # M6 → M4: 검색
    results = search_api.post(query="Tom Dwan")

    # M6 → M5: 다운로드
    download_api.post(hand_id=results[0].hand_id)

    # 완료 대기 (5분)
    wait_for_completion(timeout=300)

    # 검증
    assert file_size > 1MB
```

---

## 사용 방법

### 기본 문법

```
{agent-name}을 사용하여 {task-description}
```

### 예시

#### 1. M2 개발 시작

```
"video-processing-engineer를 사용하여 M2 Video Metadata Service OpenAPI 스펙 작성"

기대 출력:
- POST /v1/scan (NAS 스캔)
- POST /v1/generate-proxy (프록시 생성)
- GET /v1/files/{file_id}/metadata (메타데이터 조회)
```

#### 2. Phase 0 검증 시스템

```
"validation-engineer를 사용하여 타임코드 검증 로직 구현 (src/timecode_validator.py)"

기대 출력:
- Vision API 통합 코드
- sync_score 계산 알고리즘
- Offset 자동 계산 로직
- 1:1 테스트 코드 (tests/test_timecode_validator.py)
```

#### 3. API 설계 검토

```
"microservices-pm을 사용하여 M1, M2, M3의 OpenAPI 스펙 검토"

기대 출력:
- 각 스펙의 일관성 검증
- Breaking Change 감지
- 의존성 그래프
- Mock API 서버 구축 가이드
```

#### 4. 통합 테스트

```
"integration-qa-orchestrator를 사용하여 M1→M3 통합 테스트 작성"

기대 출력:
- Contract Test (M1 API vs OpenAPI 스펙)
- Integration Test (M1 → M3 데이터 흐름)
- 테스트 데이터 준비 (Fixture)
```

---

## 기존 에이전트 연계

### 모듈별 에이전트 조합

#### M1 (Data Ingestion)
```yaml
주 에이전트: data-engineer (기존) ✅
보조 에이전트:
  - code-reviewer: 코드 리뷰
  - database-architect: BigQuery 스키마 검토
  - test-automator: 유닛 테스트
```

#### M2 (Video Metadata)
```yaml
주 에이전트: video-processing-engineer (신규) ⭐
보조 에이전트:
  - test-automator: 유닛 테스트
  - performance-engineer: 성능 최적화
  - code-reviewer: 코드 리뷰
```

#### M3 (Timecode Validation)
```yaml
주 에이전트: validation-engineer (신규) ⭐
보조 에이전트:
  - ai-engineer: Vision API 지원
  - debugger: 에러 디버깅
  - code-reviewer: 알고리즘 리뷰
```

#### M4 (RAG Search)
```yaml
주 에이전트: ai-engineer (기존) ✅
보조 에이전트:
  - performance-engineer: 검색 속도 최적화
  - security-auditor: API 보안 검증
```

#### M5 (Clipping Service)
```yaml
주 에이전트: video-pipeline-engineer (신규) ⭐
보조 에이전트:
  - deployment-engineer: systemd 배포
  - devops-troubleshooter: 운영 이슈
  - debugger: 에러 디버깅
```

#### M6 (Web UI)
```yaml
주 에이전트: frontend-developer (기존) ✅
보조 에이전트:
  - ui-ux-designer: UI 설계
  - security-auditor: XSS, CSRF 검증
  - playwright-engineer: E2E 테스트
```

---

## 워크플로우 예시

### Week 1: API 설계

```bash
# Step 1: PM이 전체 API 계약 조율
"microservices-pm을 사용하여 6개 모듈 OpenAPI 템플릿 제공"

# Step 2: 각 모듈 에이전트가 스펙 작성
"data-engineer를 사용하여 M1 OpenAPI 스펙 작성"
"video-processing-engineer를 사용하여 M2 OpenAPI 스펙 작성"
"validation-engineer를 사용하여 M3 OpenAPI 스펙 작성"
...

# Step 3: PM이 검토
"microservices-pm을 사용하여 6개 스펙 일관성 검증 및 의존성 그래프 생성"
```

### Week 3-6: 병렬 개발

```bash
# M1 개발
"data-engineer를 사용하여 M1 Dataflow 파이프라인 구현"
"test-automator를 사용하여 M1 유닛 테스트 작성"
"code-reviewer를 사용하여 M1 코드 리뷰"

# M2 개발 (병렬)
"video-processing-engineer를 사용하여 M2 메타데이터 추출 로직 구현"
"video-processing-engineer를 사용하여 M2 프록시 생성 로직 구현"
"test-automator를 사용하여 M2 유닛 테스트 작성"
```

### Week 7: 통합 테스트

```bash
# Contract Test
"integration-qa-orchestrator를 사용하여 M1-M4 Contract Test 작성"

# Integration Test
"integration-qa-orchestrator를 사용하여 M1→M3 통합 테스트 작성"

# E2E Test
"integration-qa-orchestrator를 사용하여 검색→다운로드 E2E 테스트 작성"
"playwright-engineer를 사용하여 E2E 테스트 스크립트 작성"
```

---

## 에이전트 비용

| 에이전트 | 토큰 | 사용 횟수 (예상) | 총 토큰 | 비용 |
|---------|------|----------------|---------|------|
| video-processing-engineer | 1500 | 150회 | 225K | ~$0.30 |
| validation-engineer | 1400 | 200회 | 280K | ~$0.38 |
| video-pipeline-engineer | 1500 | 120회 | 180K | ~$0.24 |
| microservices-pm | 1600 | 50회 | 80K | ~$0.11 |
| integration-qa-orchestrator | 1700 | 100회 | 170K | ~$0.23 |
| **총합** | | | **935K** | **~$1.26** |

**결론**: Phase 1 (6주) 전체 개발에 **약 $1-2 소요** (매우 저렴)

---

## FAQ

### Q1: 에이전트를 어떻게 호출하나요?

Claude Code 대화창에서:
```
"video-processing-engineer를 사용하여 M2 OpenAPI 스펙 작성"
```

### Q2: 여러 에이전트를 동시에 사용할 수 있나요?

아니요. 한 번에 하나씩 사용하세요. 하지만 순차적으로 연계 가능:
```
1. "microservices-pm으로 API 설계 검토"
2. "video-processing-engineer로 M2 구현"
3. "integration-qa-orchestrator로 통합 테스트"
```

### Q3: 기존 에이전트(data-engineer 등)는 어떻게 사용하나요?

동일하게 호출:
```
"data-engineer를 사용하여 M1 ETL 파이프라인 구현"
```

### Q4: 에이전트가 만든 코드를 수정할 수 있나요?

네! 에이전트는 초안을 제공하며, 사용자가 직접 수정 가능합니다.

---

## 다음 단계

### 즉시 실행

1. **M1 OpenAPI 스펙 작성 (테스트)**
   ```
   "data-engineer를 사용하여 M1 Data Ingestion Service OpenAPI 스펙 작성"
   ```

2. **API 계약 검토**
   ```
   "microservices-pm을 사용하여 M1 스펙 검토 및 피드백"
   ```

3. **실제 구현 시작**
   ```
   "data-engineer를 사용하여 M1 Dataflow 파이프라인 구현 (src/ingest_pipeline.py)"
   ```

---

**문서 작성자**: Claude (AI Agent Designer)
**문의**: aiden.kim@ggproduction.net
**버전**: 1.0.0
**업데이트**: 2025-11-17
