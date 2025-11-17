# POKER-BRAIN: 전문 에이전트 설계

**문서 버전**: 1.0
**작성일**: 2025-11-17
**목적**: 각 모듈별 전문 에이전트 및 PM/QA 에이전트 설계

---

## 목차

1. [기존 에이전트 분석](#1-기존-에이전트-분석)
2. [모듈별 에이전트 매핑](#2-모듈별-에이전트-매핑)
3. [신규 에이전트 설계](#3-신규-에이전트-설계)
4. [PM 에이전트 검토 및 개선](#4-pm-에이전트-검토-및-개선)
5. [QA 에이전트 검토 및 개선](#5-qa-에이전트-검토-및-개선)
6. [에이전트 스킬 정의](#6-에이전트-스킬-정의)
7. [에이전트 협업 워크플로우](#7-에이전트-협업-워크플로우)

---

## 1. 기존 에이전트 분석

### 1.1 현재 사용 가능한 에이전트 (33개)

#### Core Agents (15개)

| 에이전트 | 전문 분야 | 토큰 | 모델 |
|---------|----------|------|------|
| context7-engineer | 외부 라이브러리 문서 검증 | 1200 | Sonnet |
| seq-engineer | 순차적 사고, 요구사항 분석 | 500 | Haiku |
| task-decomposition | 태스크 분해 | 600 | Haiku |
| backend-architect | 백엔드 아키텍처, API 설계 | 1400 | Sonnet |
| frontend-developer | React/Vue/Svelte UI | 1300 | Sonnet |
| fullstack-developer | End-to-end 개발 | 1600 | Sonnet |
| typescript-expert | 타입 안전성 | 1000 | Sonnet |
| debugger | 에러 디버깅 | 1300 | Sonnet |
| test-automator | Unit/integration 테스트 | 600 | Haiku |
| playwright-engineer | E2E 테스트 | 1500 | Sonnet |
| code-reviewer | 코드 품질 리뷰 | 1300 | Sonnet |
| security-auditor | OWASP 컴플라이언스 | 1400 | Sonnet |
| performance-engineer | 성능 최적화 | 1300 | Sonnet |
| deployment-engineer | CI/CD, 배포 | 700 | Haiku |
| architect-reviewer | 아키텍처 리뷰 | 1300 | Sonnet |

#### Extended Agents (18개)

| 에이전트 | 전문 분야 | 토큰 | 모델 |
|---------|----------|------|------|
| data-engineer | ETL 파이프라인, 데이터 레이크 | 1400 | Sonnet |
| data-scientist | SQL, BigQuery 분석 | 1200 | Sonnet |
| ai-engineer | LLM/RAG 시스템 설계 | 1500 | Sonnet |
| ml-engineer | ML 파이프라인, 모델 배포 | 1400 | Sonnet |
| cloud-architect | AWS/GCP/Azure 설계 | 1500 | Sonnet |
| devops-troubleshooter | 프로덕션 디버깅 | 1400 | Sonnet |
| database-architect | DB 스키마 설계 | 1300 | Sonnet |
| database-optimizer | 쿼리 최적화 | 1200 | Sonnet |
| taskmanager-planner | 태스크 계획, 마일스톤 | 700 | Haiku |
| github-engineer | Git 워크플로우 | 800 | Haiku |
| ... (나머지 8개) | | | |

---

### 1.2 현재 에이전트의 한계

**발견된 Gap**:

| 필요 역할 | 기존 에이전트 | Gap |
|----------|-------------|-----|
| **영상 처리** (M2, M5) | ❌ 없음 | FFmpeg, 트랜스코딩, 메타데이터 추출 전문 에이전트 부재 |
| **검증 로직** (M3) | ai-engineer (부분적) | Vision API + 타임코드 동기화 로직 전문성 부족 |
| **마이크로서비스 PM** | taskmanager-planner (일반) | API 계약 관리, 모듈 간 의존성 관리 전문성 부족 |
| **통합 QA** | test-automator (유닛 테스트만) | 모듈 간 통합 테스트, E2E 오케스트레이션 부재 |

**결론**: 4개 신규 에이전트 설계 필요

---

## 2. 모듈별 에이전트 매핑

### 2.1 완전 매핑 테이블

| 모듈 | 담당 인간 | 기존 에이전트 | 신규 에이전트 | 보조 에이전트 |
|------|----------|-------------|-------------|-------------|
| **M1: Data Ingestion** | Alice | ✅ data-engineer | - | database-architect, code-reviewer |
| **M2: Video Metadata** | Bob | ⚠️ backend-architect (API만) | ⭐ **video-processing-engineer** | debugger, test-automator |
| **M3: Timecode Validation** | Charlie | ⚠️ ai-engineer (Vision만) | ⭐ **validation-engineer** | debugger, code-reviewer |
| **M4: RAG Search** | David | ✅ ai-engineer | - | performance-engineer, security-auditor |
| **M5: Clipping Service** | Eve | ⚠️ devops-troubleshooter (운영만) | ⭐ **video-pipeline-engineer** | deployment-engineer, debugger |
| **M6: Web UI** | Frank | ✅ frontend-developer | - | ui-ux-designer, security-auditor |
| **전체 PM** | PM | ⚠️ taskmanager-planner (일반) | ⭐ **microservices-pm** | architect-reviewer |
| **전체 QA** | QA | ⚠️ test-automator (유닛만) | ⭐ **integration-qa-orchestrator** | playwright-engineer, security-auditor |

**범례**:
- ✅ 기존 에이전트로 충분
- ⚠️ 기존 에이전트로 부분 커버, 신규 필요
- ⭐ 신규 에이전트 필수

---

## 3. 신규 에이전트 설계

### 3.1 Video Processing Engineer

**목적**: M2 (Video Metadata Service) 전담

```yaml
Agent ID: video-processing-engineer
Model: Sonnet (복잡한 FFmpeg 로직)
Tokens: ~1500

전문 분야:
  - FFmpeg 명령어 생성 및 최적화
  - 영상 메타데이터 추출 (해상도, 코덱, 비트레이트, 길이)
  - 프록시 영상 생성 (트랜스코딩)
  - NAS/GCS 파일 시스템 통합
  - 대용량 영상 파일 처리 최적화

핵심 스킬:
  1. ffmpeg-mastery:
     - 메타데이터 추출: ffprobe JSON 파싱
     - 트랜스코딩: H.264/H.265, 해상도 변환
     - 최적화: -c copy (빠른 복사), CRF 설정

  2. video-analysis:
     - 영상 길이 정확도 검증
     - 코덱 호환성 체크
     - 파일 손상 감지

  3. storage-integration:
     - NAS SMB/NFS 마운트 처리
     - GCS 대용량 업로드 (멀티파트)
     - 파일 무결성 검증 (checksum)

  4. performance-optimization:
     - 병렬 처리 (멀티 프로세싱)
     - 메모리 관리 (스트리밍 처리)
     - I/O 최적화

사용 도구:
  - FFmpeg/FFprobe
  - Python: subprocess, multiprocessing
  - google-cloud-storage
  - PyFilesystem2 (NAS 추상화)

API 설계 지원:
  - POST /v1/scan (NAS 스캔)
  - POST /v1/generate-proxy (프록시 생성)
  - GET /v1/files/{file_id}/metadata

예시 출력:
  "NAS 영상을 720p H.264 프록시로 변환하는 최적화된 FFmpeg 명령어:

  ffmpeg -i /nas/wsop2024_d3.mp4 \
         -vf scale=1280:720 \
         -c:v libx264 -preset medium -crf 23 \
         -c:a aac -b:a 128k \
         -movflags +faststart \
         /tmp/proxy.mp4

  설명:
  - scale=1280:720: 720p로 다운스케일
  - crf 23: 시각적 품질 유지하면서 압축
  - preset medium: 속도와 압축률 균형
  - movflags +faststart: 웹 스트리밍 최적화

  예상 처리 시간: 10시간 원본 → 약 30분 (8x 속도)"

성공 지표:
  - 메타데이터 추출 정확도 100%
  - 프록시 생성 실패율 < 1%
  - 처리 속도: 실시간의 8-10배
```

---

### 3.2 Validation Engineer

**목적**: M3 (Timecode Validation Service) 전담

```yaml
Agent ID: validation-engineer
Model: Sonnet (복잡한 검증 로직)
Tokens: ~1400

전문 분야:
  - 데이터 품질 검증 (타임코드 정확성)
  - Vision API 통합 (포커 장면 감지)
  - Offset 자동 계산 알고리즘
  - 통계 기반 신뢰도 점수 계산
  - 예외 케이스 처리 (수동 매칭 필요 판단)

핵심 스킬:
  1. timecode-validation:
     - ATI 타임스탬프 vs 영상 타임코드 비교
     - Offset 패턴 감지 (시간대, DST, 파일 시작점)
     - 동기화 점수 계산 (0-100)

  2. vision-api-integration:
     - Google Vision API Object Detection
     - 포커 관련 객체 인식 (table, cards, chips, players)
     - Confidence threshold 설정
     - 비용 최적화 (배치 처리)

  3. offset-calculation:
     - ±30초 범위 샘플링 (5초 간격)
     - 최적 Offset 자동 탐색
     - Confidence 기반 자동/수동 판단

  4. statistical-analysis:
     - Sync Score = Vision(50%) + Duration(30%) + Players(20%)
     - 이상치 감지 (예: 10시간 핸드)
     - 검증 결과 품질 리포트

사용 도구:
  - Google Cloud Vision API
  - FFmpeg (프레임 추출)
  - NumPy/Pandas (통계 분석)
  - BigQuery (검증 결과 저장)

API 설계 지원:
  - POST /v1/validate (단일 검증)
  - POST /v1/validate/batch (배치 검증)
  - GET /v1/validate/{id}/result

예시 출력:
  "타임코드 검증 알고리즘:

  def calculate_sync_score(hand, video_path) -> dict:
      # 1. 프레임 추출
      frame = extract_frame_at_timecode(video_path, hand.timestamp_start)

      # 2. Vision API 호출
      result = vision_api.detect_objects(frame)
      poker_objects = ['table', 'playing_card', 'poker_chip', 'person']
      confidence = sum([o.score for o in result if o.name in poker_objects]) / len(poker_objects)

      # 3. 점수 계산
      score = 0
      if confidence > 0.8:
          score += 50  # Vision confidence

      duration_diff = abs(expected_duration - actual_duration)
      if duration_diff < 5:
          score += 30  # Duration match

      if player_count_match:
          score += 20  # Player count

      # 4. Offset 계산 (필요 시)
      if score < 80:
          offset = find_best_offset(hand, video_path)
          return {
              'sync_score': score,
              'is_synced': False,
              'calculated_offset': offset
          }

      return {
          'sync_score': score,
          'is_synced': True,
          'calculated_offset': 0
      }

  성공 기준:
  - score > 90: 완벽 동기화
  - score 80-90: 양호
  - score < 80: Offset 계산 또는 수동 매칭"

성공 지표:
  - 자동 매칭 성공률 > 95%
  - Vision API 정확도 > 90%
  - Offset 계산 성공률 > 70%
```

---

### 3.3 Video Pipeline Engineer

**목적**: M5 (Clipping Service) 전담

```yaml
Agent ID: video-pipeline-engineer
Model: Sonnet (복잡한 파이프라인)
Tokens: ~1500

전문 분야:
  - 비동기 비디오 처리 파이프라인
  - Pub/Sub 기반 이벤트 처리
  - FFmpeg 서브클립 생성 최적화
  - Local Agent 아키텍처 (NAS 서버 배포)
  - High Availability (HA) 설계

핵심 스킬:
  1. async-video-processing:
     - Pub/Sub Subscriber 구현
     - 비동기 큐 처리 (Celery/RQ)
     - 병렬 클리핑 (최대 10개 동시)
     - Dead Letter Queue 처리

  2. ffmpeg-clipping:
     - 정확한 타임코드 클리핑 (-ss, -to)
     - Copy 모드 (빠른 처리)
     - Keyframe 정렬 (avoid_negative_ts)
     - 품질 vs 속도 최적화

  3. local-agent-deployment:
     - Python Daemon (systemd)
     - NAS 로컬 네트워크 최적화
     - GCS 업로드 (멀티파트)
     - Health Check & Auto-restart

  4. high-availability:
     - Primary + Standby Agent
     - Heartbeat 모니터링
     - Automatic Failover
     - 작업 상태 추적 (BigQuery)

사용 도구:
  - Pub/Sub (Publisher/Subscriber)
  - FFmpeg (서브클립 생성)
  - systemd (Daemon 관리)
  - GCS (업로드)
  - Redis (작업 상태 캐시)

파이프라인 설계:
  User Request
      ↓
  Pub/Sub Topic (clipping-requests)
      ↓
  Local Agent (Subscriber)
      ↓
  FFmpeg Clipping (NAS 로컬)
      ↓
  GCS Upload
      ↓
  Pub/Sub Topic (clipping-complete)
      ↓
  User Notification

예시 출력:
  "Local Clipping Agent 구현:

  # src/clipping_agent.py
  class ClippingAgent:
      def __init__(self):
          self.subscriber = pubsub.SubscriberClient()
          self.primary = True  # Primary Agent

      def callback(self, message):
          data = json.loads(message.data)

          try:
              # 1. FFmpeg 클리핑
              output = self.create_subclip(
                  nas_path=data['nas_path'],
                  start=data['start_seconds'],
                  end=data['end_seconds']
              )

              # 2. GCS 업로드
              gcs_path = self.upload_to_gcs(output)

              # 3. Signed URL 생성
              url = self.generate_signed_url(gcs_path, expires_in=86400)

              # 4. 완료 알림
              self.publish_complete(data['request_id'], url)

              message.ack()

          except Exception as e:
              self.publish_failed(data['request_id'], str(e))
              message.nack()  # 재시도

      def create_subclip(self, nas_path, start, end):
          output = f'/tmp/{uuid.uuid4()}.mp4'

          cmd = [
              'ffmpeg', '-ss', str(start), '-to', str(end),
              '-i', nas_path,
              '-c', 'copy',  # 빠른 복사
              '-avoid_negative_ts', 'make_zero',
              output
          ]

          subprocess.run(cmd, check=True)
          return output

  systemd 서비스:

  # /etc/systemd/system/clipping-agent.service
  [Unit]
  Description=POKER-BRAIN Clipping Agent
  After=network.target

  [Service]
  Type=simple
  User=clipping
  WorkingDirectory=/opt/clipping-agent
  ExecStart=/usr/bin/python3 agent.py
  Restart=always
  RestartSec=10

  [Install]
  WantedBy=multi-user.target"

성공 지표:
  - 클립 생성 성공률 > 99%
  - P95 처리 시간 < 5분
  - HA Failover 시간 < 1분
```

---

## 4. PM 에이전트 검토 및 개선

### 4.1 기존 에이전트 분석

#### taskmanager-planner (기존)

```yaml
현재 역할:
  - 태스크 계획 및 마일스톤 생성
  - MCP (Model Context Protocol) 활용
  - 프로젝트 분해 및 의존성 정의

강점:
  ✅ 태스크 분해 능력 우수
  ✅ 타임라인 관리 가능
  ✅ 체계적인 마일스톤 설정

약점:
  ❌ 마이크로서비스 특화 기능 부족
  ❌ API 계약 관리 경험 없음
  ❌ 모듈 간 의존성 시각화 부족
  ❌ OpenAPI 스펙 검토 능력 없음

결론:
  ⚠️ 일반 프로젝트 관리는 가능하나,
  마이크로서비스 아키텍처에는 부족
```

---

### 4.2 신규 에이전트: Microservices PM

```yaml
Agent ID: microservices-pm
Model: Sonnet (복잡한 의존성 관리)
Tokens: ~1600

전문 분야:
  - 마이크로서비스 프로젝트 관리
  - API 계약 (OpenAPI) 관리 및 검증
  - 모듈 간 의존성 매핑 및 시각화
  - 통합 일정 조율
  - 리스크 관리 (의존성 체인 분석)

핵심 스킬:
  1. api-contract-management:
     - OpenAPI 3.0 스펙 검토 및 승인
     - Breaking Change 감지
     - API 버전 관리 (/v1, /v2)
     - Mock API 서버 구축 지원

  2. dependency-mapping:
     - 모듈 간 의존성 그래프 생성
     - 순환 의존성 감지
     - Critical Path 분석
     - 병렬 개발 가능 모듈 식별

  3. integration-scheduling:
     - 통합 타임라인 관리
     - Stub/Mock 사용 시점 결정
     - E2E 테스트 일정 조율

  4. risk-management:
     - 의존성 체인 리스크 분석
     - 단일 장애점 (SPOF) 식별
     - 완화 전략 제시

사용 도구:
  - OpenAPI Validator
  - Mermaid (다이어그램)
  - taskmanager MCP
  - BigQuery (진행 추적)

워크플로우:
  Week 1: API 계약 설계
    - 각 모듈의 OpenAPI 스펙 작성 독촉
    - 스펙 리뷰 및 피드백
    - 의존성 그래프 생성
    - Mock API 서버 구축

  Week 2: 병렬 개발 시작
    - 독립 모듈 (M1, M2) 우선 시작
    - 의존 모듈 (M3, M4) Mock 사용
    - 주간 Sync-up 주최

  Week 3-6: 진행 추적
    - API 변경 사항 모니터링
    - Breaking Change 알림
    - 블로커 해결 지원

  Week 7: 통합 준비
    - 모든 모듈 Staging 배포
    - E2E 테스트 조율
    - 버그 우선순위 관리

예시 출력:
  "모듈 의존성 분석 결과:

  graph TD
      M1[M1: Data Ingestion] --> BQ[(BigQuery)]
      M2[M2: Video Metadata] --> BQ
      M3[M3: Validation] --> M1
      M3 --> M2
      M4[M4: RAG Search] --> M1
      M5[M5: Clipping] --> M2
      M6[M6: Web UI] --> M4
      M6 --> M5

  Critical Path:
  1. M1 (Data Ingestion) → 가장 먼저 시작 필수
  2. M2 (Video Metadata) → M1과 병렬 가능
  3. M3 (Validation) → M1, M2 완료 후 시작
  4. M4 (RAG Search) → M1 완료 후 시작 가능
  5. M5, M6 → 나중에 통합

  병렬 개발 전략:
  - Week 3: M1 + M2 동시 시작 (의존성 없음)
  - Week 4: M4 시작 (M1 Mock 사용)
  - Week 5: M3 시작 (M1, M2 Mock 사용)
  - Week 6: M5, M6 시작

  리스크:
  - M1 지연 시 M3, M4 블로킹 → 완화: M1 우선순위 최상
  - API Breaking Change → 완화: 버전 관리 강제"

성공 지표:
  - API 계약 준수율 100%
  - 통합 일정 지연 < 1주
  - Breaking Change 사전 감지 > 90%
```

---

### 4.3 기존 vs 신규 비교

| 항목 | taskmanager-planner (기존) | microservices-pm (신규) |
|------|---------------------------|------------------------|
| **태스크 분해** | ✅ 우수 | ✅ 우수 |
| **API 계약 관리** | ❌ 없음 | ✅ OpenAPI 검증 |
| **의존성 매핑** | ⚠️ 기본 | ✅ 고급 (그래프 분석) |
| **통합 조율** | ⚠️ 일반 | ✅ 마이크로서비스 특화 |
| **리스크 관리** | ⚠️ 기본 | ✅ 의존성 체인 분석 |
| **Mock API 지원** | ❌ 없음 | ✅ 구축 지원 |

**권장**: microservices-pm 신규 도입

---

## 5. QA 에이전트 검토 및 개선

### 5.1 기존 에이전트 분석

#### test-automator (기존)

```yaml
현재 역할:
  - 유닛 테스트 작성 (pytest, jest)
  - 통합 테스트 작성 (단순)
  - 테스트 커버리지 분석

강점:
  ✅ 유닛 테스트 생성 100% 성공률
  ✅ 빠른 실행 (<5초)
  ✅ Mock 사용 능력

약점:
  ❌ E2E 테스트는 playwright-engineer 별도 필요
  ❌ 모듈 간 통합 테스트 부족
  ❌ API 계약 테스트 없음
  ❌ 통합 테스트 오케스트레이션 없음
```

#### playwright-engineer (기존)

```yaml
현재 역할:
  - E2E 테스트 작성 (Playwright)
  - 브라우저 자동화
  - UI 테스트

강점:
  ✅ E2E 테스트 전문
  ✅ 크로스 브라우저 테스트

약점:
  ❌ UI 중심 (백엔드 API 통합은 약함)
  ❌ 모듈 간 계약 테스트 없음
```

**결론**: 통합 QA 오케스트레이터 필요

---

### 5.2 신규 에이전트: Integration QA Orchestrator

```yaml
Agent ID: integration-qa-orchestrator
Model: Sonnet (복잡한 통합 시나리오)
Tokens: ~1700

전문 분야:
  - 모듈 간 통합 테스트 설계 및 실행
  - API 계약 테스트 (Contract Testing)
  - E2E 시나리오 오케스트레이션
  - 테스트 환경 관리 (Staging)
  - 버그 트리아지 및 우선순위

핵심 스킬:
  1. contract-testing:
     - OpenAPI 스펙 vs 실제 API 검증
     - Pact/Spring Cloud Contract 활용
     - Provider/Consumer 테스트
     - Breaking Change 자동 감지

  2. integration-test-design:
     - 모듈 간 통신 시나리오 작성
     - Happy Path + Error Path
     - 타임아웃, 재시도 로직 검증
     - 데이터 일관성 검증

  3. e2e-orchestration:
     - 전체 플로우 시나리오:
       검색 → 미리보기 → 다운로드 (M6→M4→M5)
     - 각 단계 검증 포인트 정의
     - 실패 시 롤백 검증

  4. test-environment-management:
     - Staging 환경 구축 (Docker Compose)
     - 테스트 데이터 준비 (Fixture)
     - 환경 리셋 (Clean Slate)

  5. bug-triage:
     - 통합 버그 vs 모듈 버그 분류
     - 책임 모듈 식별
     - 우선순위 판단 (P0-P3)

사용 도구:
  - pytest + requests (API 통합 테스트)
  - Pact (Contract Testing)
  - Playwright (E2E)
  - Docker Compose (환경 구축)
  - BigQuery (테스트 데이터)

테스트 계층:
  L1: Unit Tests (각 모듈 내부)
      → test-automator 담당

  L2: Contract Tests (API 계약)
      → integration-qa-orchestrator 담당

  L3: Integration Tests (모듈 간 통신)
      → integration-qa-orchestrator 담당

  L4: E2E Tests (전체 플로우)
      → integration-qa-orchestrator + playwright-engineer

예시 출력:
  "통합 테스트 시나리오: 검색 → 다운로드

  # tests/integration/test_search_to_download.py
  import pytest
  import requests
  import time

  @pytest.mark.integration
  def test_full_workflow():
      '''검색부터 클립 다운로드까지 전체 플로우'''

      # Step 1: M4 (RAG Search) 호출
      search_response = requests.post(
          'http://rag-search-service:8080/v1/search',
          json={'query': 'Tom Dwan bluff'},
          headers={'Authorization': f'Bearer {get_test_token()}'}
      )
      assert search_response.status_code == 200
      results = search_response.json()
      assert len(results['results']) > 0

      hand_id = results['results'][0]['hand_id']

      # Step 2: M6 (Web UI) → Pub/Sub 클리핑 요청
      download_response = requests.post(
          'http://web-ui:3000/api/download',
          json={'hand_id': hand_id}
      )
      assert download_response.status_code == 200

      # Step 3: M5 (Clipping) 완료 대기
      max_wait = 300  # 5분
      for _ in range(max_wait // 5):
          time.sleep(5)

          # Pub/Sub 완료 메시지 확인
          status = check_clipping_status(hand_id)
          if status == 'completed':
              break

      assert status == 'completed', '클립 생성 타임아웃'

      # Step 4: 다운로드 URL 검증
      download_url = get_download_url(hand_id)
      assert download_url.startswith('https://storage.googleapis.com/')

      # Step 5: 파일 다운로드 및 검증
      file_response = requests.get(download_url)
      assert file_response.status_code == 200
      assert len(file_response.content) > 1024 * 1024  # > 1MB

      # Step 6: 영상 길이 검증 (ffprobe)
      temp_file = '/tmp/test_clip.mp4'
      with open(temp_file, 'wb') as f:
          f.write(file_response.content)

      duration = get_video_duration(temp_file)
      expected_duration = results['results'][0]['duration_seconds']
      assert abs(duration - expected_duration) < 2  # 2초 오차 허용

  검증 포인트:
  - M4 검색 응답 시간 < 10초
  - M5 클립 생성 시간 < 5분
  - 최종 파일 크기 및 길이 정확성
  - 에러 발생 시 적절한 에러 메시지

  Contract Test 예시:

  # tests/contract/test_m4_api_contract.py
  def test_search_api_matches_openapi_spec():
      '''M4 Search API가 OpenAPI 스펙과 일치하는지'''

      # OpenAPI 스펙 로드
      spec = load_openapi_spec('modules/rag-search/openapi.yaml')

      # 실제 API 호출
      response = requests.post(
          'http://rag-search-service:8080/v1/search',
          json={'query': 'test', 'limit': 20}
      )

      # 스펙 검증
      validate_response_against_spec(response, spec, '/v1/search', 'post')

      # 필수 필드 존재 확인
      assert 'results' in response.json()
      assert 'total_results' in response.json()
      assert 'processing_time_ms' in response.json()"

성공 지표:
  - 통합 테스트 커버리지 > 80%
  - API 계약 테스트 통과율 100%
  - E2E 성공률 > 95%
  - 버그 트리아지 정확도 > 90%
```

---

### 5.3 QA 에이전트 협업 구조

```
┌─────────────────────────────────────────┐
│  Integration QA Orchestrator (총괄)     │
│  - 통합 테스트 설계                      │
│  - API 계약 검증                         │
│  - E2E 시나리오 관리                     │
└────────────┬────────────────────────────┘
             ↓
    ┌────────┴────────┐
    ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│test-automator│  │playwright-engineer│
│(유닛 테스트)  │  │(E2E 테스트)       │
└──────────────┘  └──────────────────┘
    ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│code-reviewer │  │security-auditor  │
│(코드 리뷰)    │  │(보안 검증)        │
└──────────────┘  └──────────────────┘
```

**역할 분담**:
- **Integration QA**: 전략 수립, 통합 테스트, 계약 테스트
- **test-automator**: 유닛 테스트 작성 지원
- **playwright-engineer**: E2E 스크립트 작성
- **code-reviewer**: 테스트 코드 품질 검토
- **security-auditor**: 보안 취약점 검증

---

## 6. 에이전트 스킬 정의

### 6.1 공통 스킬 (모든 에이전트)

```yaml
기본 도구:
  - Read: 파일 읽기
  - Write: 파일 쓰기
  - Edit: 파일 수정
  - Bash: 명령어 실행
  - Grep: 코드 검색

코드 품질:
  - 1:1 테스트 페어링 준수
  - OpenAPI 스펙 작성
  - 에러 처리 표준화
  - 로깅 표준 준수
```

### 6.2 모듈별 전문 스킬

#### M1: data-engineer

```yaml
전문 도구:
  - Apache Beam SDK
  - BigQuery Python Client
  - Dataflow API

핵심 패턴:
  - ETL 파이프라인 설계
  - 데이터 품질 검증
  - 스키마 진화 (Schema Evolution)
  - 파티셔닝 최적화
```

#### M2: video-processing-engineer

```yaml
전문 도구:
  - FFmpeg/FFprobe
  - PyAV (Python Video Library)
  - google-cloud-storage
  - PyFilesystem2

핵심 패턴:
  - 비디오 메타데이터 추출
  - 트랜스코딩 최적화
  - 대용량 파일 스트리밍
  - 병렬 처리 (multiprocessing)
```

#### M3: validation-engineer

```yaml
전문 도구:
  - Google Cloud Vision API
  - NumPy/Pandas (통계)
  - Matplotlib (시각화)
  - FFmpeg (프레임 추출)

핵심 패턴:
  - Vision API 배치 처리
  - 통계 기반 신뢰도 계산
  - Offset 탐색 알고리즘
  - 예외 케이스 분류
```

#### M4: ai-engineer

```yaml
전문 도구:
  - Vertex AI SDK
  - TextEmbedding API
  - Vector Search
  - BigQuery ML

핵심 패턴:
  - RAG 파이프라인 설계
  - Embedding 최적화
  - Re-ranking 알고리즘
  - 검색 품질 측정
```

#### M5: video-pipeline-engineer

```yaml
전문 도구:
  - Pub/Sub SDK
  - FFmpeg (클리핑)
  - systemd (Daemon)
  - Redis (캐싱)

핵심 패턴:
  - 비동기 큐 처리
  - HA (High Availability) 설계
  - 백프레셔 관리
  - Dead Letter Queue
```

#### M6: frontend-developer

```yaml
전문 도구:
  - Next.js 14
  - React Query
  - shadcn/ui
  - Tailwind CSS

핵심 패턴:
  - Server Components
  - API Routes (BFF)
  - Optimistic Updates
  - 무한 스크롤 (Infinite Scroll)
```

---

## 7. 에이전트 협업 워크플로우

### 7.1 Phase 0: API 설계 단계

```yaml
Week 1: API 계약 설계

참여 에이전트:
  - microservices-pm (주도)
  - 각 모듈 담당 에이전트 (6개)
  - architect-reviewer (검토)

워크플로우:
  1. microservices-pm:
     - 모듈 간 의존성 분석
     - API 설계 가이드라인 배포
     - OpenAPI 템플릿 제공

  2. 각 모듈 에이전트:
     - 담당 모듈의 OpenAPI 스펙 작성
     - 예시 Request/Response 작성
     - 에러 코드 정의

  3. architect-reviewer:
     - 전체 API 아키텍처 검토
     - RESTful 원칙 준수 확인
     - 일관성 검증

  4. microservices-pm:
     - 피드백 통합
     - Mock API 서버 구축
     - API 계약 승인

산출물:
  - 6개 OpenAPI YAML 파일
  - Mock API 서버 (Postman/Prism)
  - API 계약 문서
```

### 7.2 Phase 1: 병렬 개발 단계

```yaml
Week 3-6: 독립 개발

모듈별 워크플로우:

M1 (data-engineer):
  1. BigQuery 스키마 생성
  2. Dataflow 파이프라인 구현
  3. test-automator: 유닛 테스트 작성
  4. code-reviewer: 코드 리뷰
  5. deployment-engineer: Cloud Run 배포

M2 (video-processing-engineer):
  1. FFmpeg 메타데이터 추출 구현
  2. 프록시 생성 로직
  3. test-automator: 유닛 테스트
  4. performance-engineer: 성능 최적화
  5. deployment-engineer: 배포

... (나머지 모듈 동일)

주간 Sync-up (microservices-pm 주최):
  - 진행 상황 공유
  - API 변경 사항 공지
  - 블로커 해결
  - 의존성 조율
```

### 7.3 Phase 2: 통합 테스트 단계

```yaml
Week 7-8: 통합 및 테스트

참여 에이전트:
  - integration-qa-orchestrator (주도)
  - test-automator (유닛 테스트)
  - playwright-engineer (E2E)
  - security-auditor (보안)
  - all module agents (버그 수정)

워크플로우:
  1. integration-qa-orchestrator:
     - 통합 테스트 시나리오 작성
     - Contract Test 실행
     - E2E 테스트 계획

  2. Staging 배포:
     - deployment-engineer: 모든 모듈 배포
     - Docker Compose 환경 구축

  3. 테스트 실행:
     - L2: Contract Tests
     - L3: Integration Tests
     - L4: E2E Tests (playwright-engineer)

  4. 버그 수정:
     - integration-qa-orchestrator: 트리아지
     - 각 모듈 에이전트: 버그 수정
     - code-reviewer: 수정 코드 리뷰

  5. 회귀 테스트:
     - 모든 테스트 재실행
     - 성공률 > 95% 달성 시 Production 승인

산출물:
  - 통합 테스트 리포트
  - 버그 목록 및 수정 내역
  - Production 배포 승인 문서
```

---

## 8. 에이전트 성능 지표

### 8.1 모듈 에이전트 KPI

| 에이전트 | 성공 지표 | 목표 |
|---------|----------|------|
| **data-engineer** | ETL 성공률 | > 99% |
| **video-processing-engineer** | 프록시 생성 성공률 | > 99% |
| **validation-engineer** | 자동 매칭 성공률 | > 95% |
| **ai-engineer** | 검색 정확도 (Precision@5) | > 80% |
| **video-pipeline-engineer** | 클립 생성 성공률 | > 99% |
| **frontend-developer** | UI 반응 시간 | < 100ms |

### 8.2 PM/QA 에이전트 KPI

| 에이전트 | 성공 지표 | 목표 |
|---------|----------|------|
| **microservices-pm** | API 계약 준수율 | 100% |
| **microservices-pm** | 일정 지연 | < 1주 |
| **integration-qa-orchestrator** | 통합 테스트 커버리지 | > 80% |
| **integration-qa-orchestrator** | 버그 트리아지 정확도 | > 90% |

---

## 9. 에이전트 비용 분석

### 9.1 토큰 사용량 (Phase 1, 6주)

```yaml
모듈 에이전트 (각 4주 활동):
  - data-engineer: 1400 tokens × 100회 = 140K
  - video-processing-engineer: 1500 × 150 = 225K
  - validation-engineer: 1400 × 200 = 280K
  - ai-engineer: 1500 × 100 = 150K
  - video-pipeline-engineer: 1500 × 120 = 180K
  - frontend-developer: 1300 × 100 = 130K
  소계: 1,105K tokens

PM 에이전트 (6주 활동):
  - microservices-pm: 1600 × 50 = 80K

QA 에이전트 (Week 7-8):
  - integration-qa-orchestrator: 1700 × 100 = 170K
  - test-automator: 600 × 200 = 120K
  - playwright-engineer: 1500 × 50 = 75K
  소계: 365K tokens

총 토큰: ~1.5M tokens
예상 비용: ~$20 (Claude Sonnet 기준)
```

**결론**: 에이전트 비용은 매우 저렴 (인건비 대비 < 0.01%)

---

## 10. 다음 단계

### 10.1 즉시 실행

1. **신규 에이전트 구현**:
   - video-processing-engineer 프롬프트 작성
   - validation-engineer 프롬프트 작성
   - video-pipeline-engineer 프롬프트 작성
   - microservices-pm 프롬프트 작성 (기존 taskmanager 확장)
   - integration-qa-orchestrator 프롬프트 작성

2. **기존 에이전트 매핑**:
   - data-engineer → M1
   - ai-engineer → M4
   - frontend-developer → M6

3. **테스트**:
   - 각 에이전트에 샘플 태스크 부여
   - 출력 품질 검증
   - 협업 시나리오 테스트

### 10.2 Phase 0 적용

```bash
# M1 (Data Ingestion) 개발 시작
Task: data-engineer
Prompt: "M1 (Data Ingestion Service) 구현:
- NSUS ATI JSON 데이터를 BigQuery로 ETL
- OpenAPI 스펙: docs/architecture_modular.md 참고
- 1:1 테스트 페어링 필수"

# API 계약 관리
Task: microservices-pm
Prompt: "6개 모듈의 OpenAPI 스펙 검토:
- 일관성 검증
- Breaking Change 확인
- Mock API 서버 구축 가이드"

# 통합 테스트 준비
Task: integration-qa-orchestrator
Prompt: "M1, M2 통합 테스트 시나리오 작성:
- Contract Test (OpenAPI vs 실제 API)
- 데이터 일관성 검증"
```

---

**문서 작성자**: Claude (AI Agent Designer)
**최종 검토**: aiden.kim@ggproduction.net
**버전**: 1.0
**상태**: Ready for Implementation

---

## 부록 A: 에이전트 프롬프트 템플릿

### video-processing-engineer 프롬프트

```
You are a Video Processing Engineer specializing in FFmpeg, video metadata extraction, and transcoding optimization.

Your expertise:
- FFmpeg command generation and optimization
- Video metadata extraction (resolution, codec, bitrate, duration)
- Proxy video generation (transcoding)
- NAS/GCS file system integration
- Large video file processing optimization

Your tools:
- FFmpeg/FFprobe
- Python: subprocess, multiprocessing
- google-cloud-storage
- PyFilesystem2

Your responsibilities for M2 (Video Metadata Service):
- Scan NAS directories for video files
- Extract metadata using ffprobe
- Generate 720p H.264 proxy videos
- Upload to GCS
- Ensure 1:1 test pairing

API endpoints to implement:
- POST /v1/scan
- POST /v1/generate-proxy
- GET /v1/files/{file_id}/metadata

Success criteria:
- Metadata extraction accuracy: 100%
- Proxy generation success rate: > 99%
- Processing speed: 8-10x realtime

Always provide:
1. Optimized FFmpeg commands with explanations
2. Error handling strategies
3. Performance optimization tips
4. Test code (1:1 pairing)
```

### validation-engineer 프롬프트

```
You are a Validation Engineer specializing in data quality validation, Vision API integration, and timecode synchronization.

Your expertise:
- Timecode accuracy validation (ATI data vs video)
- Google Cloud Vision API for poker scene detection
- Offset calculation algorithms
- Statistical confidence scoring
- Exception handling (manual matching decision)

Your tools:
- Google Cloud Vision API
- FFmpeg (frame extraction)
- NumPy/Pandas (statistical analysis)
- BigQuery

Your responsibilities for M3 (Timecode Validation Service):
- Validate ATI timestamps against video timecode
- Use Vision API to detect poker scenes
- Calculate sync score (0-100)
- Auto-calculate offset if needed (±30 seconds)
- Determine auto vs manual matching

API endpoints to implement:
- POST /v1/validate
- POST /v1/validate/batch
- GET /v1/validate/{id}/result

Algorithm:
sync_score = vision_confidence(50%) + duration_match(30%) + player_count(20%)

Success criteria:
- Auto-matching success rate: > 95%
- Vision API accuracy: > 90%
- Offset calculation success: > 70%

Always provide:
1. Statistical validation logic
2. Vision API optimization (batch processing)
3. Error case handling
4. Test code with mock Vision responses
```

---

## 부록 B: 에이전트 호출 예시

```python
# M2 개발 시작
from claude_code import Task

# 1. API 스펙 작성
Task(
    agent="video-processing-engineer",
    task="M2 Video Metadata Service의 OpenAPI 스펙 작성",
    context={
        "module": "M2",
        "reference": "docs/architecture_modular.md section 3.2"
    }
)

# 2. 메타데이터 추출 구현
Task(
    agent="video-processing-engineer",
    task="NAS 영상 파일 메타데이터 추출 로직 구현 (src/metadata_extractor.py)",
    context={
        "nas_path": "/nas/poker/2024/wsop/",
        "output": "BigQuery prod.video_files"
    }
)

# 3. 테스트 작성
Task(
    agent="test-automator",
    task="metadata_extractor.py에 대한 유닛 테스트 작성 (1:1 pairing)",
    context={
        "implementation_file": "src/metadata_extractor.py",
        "test_file": "tests/test_metadata_extractor.py"
    }
)

# 4. 코드 리뷰
Task(
    agent="code-reviewer",
    task="M2 코드 품질 리뷰",
    context={
        "files": ["src/metadata_extractor.py", "tests/test_metadata_extractor.py"]
    }
)
```

완성! 🎉
