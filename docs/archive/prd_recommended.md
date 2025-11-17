# 📄 PRD: POKER-BRAIN v3.0 (Recommended Architecture)

**문서 버전**: 3.0 (Hybrid Best-of-Both)
**작성일**: 2025-11-17
**상태**: RECOMMENDED
**기반**: prd_gemini.md v2.2 + prd_gpt.md v1.2의 장점 결합

---

## 🎯 Executive Summary

**핵심 전략**: "Start Simple, Scale Smart"

1. **Phase 0 (준비)**: 타임코드 동기화 검증 시스템 구축
2. **Phase 1 (MVP)**: GCP All-In + NAS Hybrid (비용 최소화)
3. **Phase 2 (확장)**: Smart Tiering + CDN (글로벌 접근)
4. **Phase 3 (자동화)**: AI 큐레이션 + 자동 하이라이트

**차별점**:
- ✅ 단일 클라우드(GCP) → 운영비 년 $211K 절감
- ✅ NAS 활용 → 원본 영상 접근 지연 최소화
- ✅ 점진적 확장 → 다운타임 제로, Rollback 가능
- ✅ AI 품질 모니터링 → 지속적 개선

---

## 1. 문제 정의

### 1.1 현재 Pain Points

| 문제 | 영향 | 비용 |
|------|------|------|
| **수동 영상 검색** | 기획자 1개 클립 찾는데 2-4시간 소요 | **$150/클립** (인건비) |
| **핸드 데이터-영상 분리** | ATI 데이터 있어도 영상 못 찾음 | 콘텐츠 제작 지연 |
| **글로벌 접근 불가** | 해외 지사에서 NAS 접근 불가 | 협업 차단 |
| **수동 클리핑** | 편집자가 10시간 영상에서 30초 찾기 | **$50/클립** (편집 시간) |

**총 비용**: 월 100개 클립 × $200 = **$20,000/월** = **$240K/년**

### 1.2 목표

**ROI 목표**: 시스템 구축 비용 대비 **6개월 내 회수**

| 지표 | 현재 | 목표 | 개선율 |
|------|------|------|--------|
| 클립 검색 시간 | 2-4시간 | **10초** | **99.9%↓** |
| 클립 생성 시간 | 1-2시간 | **5분** | **97.5%↓** |
| 인건비 | $200/클립 | **$5/클립** | **97.5%↓** |
| 글로벌 접근 | 불가 | **가능** | ∞ |

---

## 2. 시스템 아키텍처

### 2.1 전체 구조 (Phase 1-3)

```
┌─────────────────────────────────────────────────────┐
│                  Google Cloud Platform              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐    ┌──────────────────┐           │
│  │ NSUS ATI    │───→│ BigQuery         │           │
│  │ Raw Data    │    │ (Hand Summary)   │           │
│  └─────────────┘    └────────┬─────────┘           │
│                               ↓                      │
│  ┌──────────────────────────────────────┐           │
│  │   Vertex AI RAG Engine               │           │
│  │   - Gemini Summarization             │           │
│  │   - TextEmbedding-004                │           │
│  │   - Vector Search                    │           │
│  └───────────────────┬──────────────────┘           │
│                      ↓                               │
│  ┌──────────────────────────────────────┐           │
│  │   Cloud Run (Web App)                │           │
│  │   - IAP Auth (내부만 접근)            │           │
│  │   - Search UI                        │           │
│  │   - Feedback System ⭐               │           │
│  └───────────┬──────────────────────────┘           │
│              ↓                                       │
│  ┌──────────────────────────────────────┐           │
│  │   Video Pipeline                     │           │
│  │   ┌─────────┐      ┌─────────┐      │           │
│  │   │ Proxy   │      │ Subclip │      │           │
│  │   │ (GCS)   │      │ (GCS)   │      │           │
│  │   └─────────┘      └─────────┘      │           │
│  └──────────────────────────────────────┘           │
│                                                      │
└──────────────────┬───────────────────────────────────┘
                   ↓
         ┌─────────────────┐
         │  On-Prem NAS    │
         │  (Master Video) │
         │  - Direct Access │
         │  - Local Agent  │
         └─────────────────┘
```

**핵심 원칙**:
1. **AI는 클라우드** (Vertex AI) - 무한 확장
2. **원본은 NAS** - 저비용 대용량 저장
3. **배포는 GCS** - 글로벌 CDN

---

## 3. Phase 로드맵

### **Phase 0: 기반 검증 (3개월)** ⭐ NEW

**목표**: 타임코드 동기화 100% 보장

#### Epic 0.1: 타임코드 검증 시스템

```yaml
Features:
  - name: "ATI-Video Sync Validator"
    description: "ATI 데이터와 NAS 영상의 타임코드 일치 여부 자동 검증"

    components:
      1. Sync Check Script:
         - Input: hand_id, timestamp_start, timestamp_end
         - Process: NAS 영상에서 해당 구간 추출
         - Validation: 화면에 테이블/플레이어 존재 확인 (Vision AI)
         - Output: Match Score (0-100%)

      2. Mismatch Handler:
         - Score < 90%일 때 자동 알림
         - 수동 매칭 UI 제공
         - Offset 계산 후 DB 업데이트

      3. Quality Dashboard:
         - 일간 동기화 성공률 모니터링
         - 문제 핸드 리스트 자동 생성

Success Criteria:
  - ✅ 1,000개 샘플 핸드 중 95% 이상 자동 매칭
  - ✅ 나머지 5%는 수동 매칭 후 Offset 저장
  - ✅ Phase 1 시작 전 100% 검증 완료
```

**예상 비용**: $5K (개발) + $1K (Vision AI)

---

### **Phase 1: MVP (6개월)**

**범위**: 본사 내부용 RAG 검색 + 클리핑

#### Epic 1.1: RAG 시스템

```yaml
Components:
  - BigQuery:
      Schema:
        - hand_id (PK)
        - searchable_text (RAG용 자연어 요약)
        - video_nas_path (예: //nas01/poker/ft1_day3.mp4)
        - video_proxy_gcs (예: gs://gg-proxy/ft1_day3_h264.mp4)
        - timestamp_start (초 단위)
        - timestamp_end (초 단위)
        - players (ARRAY<STRING>)
        - pot_size (NUMERIC)

  - Vertex AI:
      - Data Store: BigQuery 커넥터
      - Embedding: textembedding-004 (다국어)
      - LLM: Gemini 1.5 Pro

  - Search API:
      Endpoint: /api/v1/search
      Request:
        {
          "query": "Tom Dwan 블러프 100K 이상",
          "limit": 20,
          "filters": {
            "pot_size_min": 100000,
            "players": ["Tom Dwan"]
          }
        }
      Response:
        {
          "results": [
            {
              "hand_id": "wsop2024_me_d3_h154",
              "summary": "Tom Dwan이 J4o로 올인 블러프...",
              "relevance_score": 0.94,
              "proxy_url": "gs://...",
              "nas_path": "//nas01/..."
            }
          ],
          "total": 156
        }
```

#### Epic 1.2: 검색 UI + Feedback

```yaml
Features:
  1. Search Interface:
     - 단일 검색창 (자연어)
     - 고급 필터 (선수, 팟 사이즈, 날짜)
     - 실시간 Preview (GCS Proxy)

  2. Feedback System ⭐:
     UI: [👍 관련있음] [👎 관련없음] [⭐ 즐겨찾기]
     Backend:
       - 피드백 → BigQuery 저장
       - 일간 품질 리포트 자동 생성
       - Precision@5, CTR 자동 계산

  3. Smart Ranking:
     - 초기: Vertex AI 기본 랭킹
     - 1개월 후: 피드백 기반 Re-ranking
     - 공식: final_score = 0.7 * ai_score + 0.3 * feedback_score
```

#### Epic 1.3: 클리핑 시스템 (NAS Local Agent)

```yaml
Architecture:
  1. Cloud Run → Pub/Sub 메시지 발행:
     {
       "hand_id": "wsop2024_me_d3_h154",
       "nas_path": "//nas01/poker/ft1_day3.mp4",
       "start_sec": 12345,
       "end_sec": 12375,
       "user_email": "han.pd@gg.com"
     }

  2. Local Agent (NAS 서버에 설치):
     - Python Daemon (systemd)
     - Pub/Sub Subscriber
     - FFmpeg 실행:
       ```bash
       ffmpeg -ss 12345 -to 12375 \
              -i /nas/poker/ft1_day3.mp4 \
              -c copy -avoid_negative_ts make_zero \
              /tmp/wsop2024_me_d3_h154.mp4
       ```
     - GCS 업로드:
       gsutil cp /tmp/wsop2024_me_d3_h154.mp4 \
                 gs://gg-subclips/wsop2024_me_d3_h154.mp4
     - Pub/Sub 완료 메시지:
       {
         "hand_id": "...",
         "status": "completed",
         "download_url": "https://storage.googleapis.com/..."
       }

  3. High Availability:
     - Primary + Standby Agent (2대)
     - Health Check (1분마다)
     - Dead Letter Queue (재시도 3회)
```

**KPI**:
- 검색 속도: **10초 이내** (P95)
- 클립 생성: **5분 이내** (P95)
- 검색 정확도: **Precision@5 > 75%** (1개월 내 달성)

---

### **Phase 2: 글로벌 확장 (3개월)**

**범위**: Smart Tiering + CDN

#### Epic 2.1: Smart Tiering

```python
# 자동 티어링 정책
def get_video_tier(hand):
    """핸드의 인기도 기반 저장 위치 결정"""

    # 최근 30일 접근 횟수
    access_count = db.get_access_count(hand.id, days=30)

    if access_count > 10:  # 인기 클립
        tier = "HOT"  # GCS Standard (즉시 접근)
        location = f"gs://gg-hot/{hand.id}.mp4"

    elif access_count > 2:  # 중간
        tier = "WARM"  # GCS Nearline (3초 검색)
        location = f"gs://gg-warm/{hand.id}.mp4"

    else:  # 거의 안 쓰임
        tier = "COLD"  # NAS only
        location = hand.nas_path

    # 백그라운드 마이그레이션
    if tier != hand.current_tier:
        schedule_migration(hand, tier, location)

    return location
```

#### Epic 2.2: Global CDN

```yaml
CDN Setup:
  - Service: Media CDN (Google) 또는 CloudCDN
  - Regions: us, eu, asia
  - Cache TTL:
      Hot Clips: 7 days
      Normal: 24 hours

  - Signed URLs:
      Expiry: 1 hour (기본)
      Max Downloads: 5회

Cost Optimization:
  - Proxy 영상: 720p H.264 (2Mbps) → 500MB/hour
  - CDN Egress: $0.08/GB (Google) vs $0.12/GB (AWS)
  - 예상: 1TB/월 egress = $80/월
```

**KPI**:
- 글로벌 접근 속도: **5초 이내** (다운로드 시작)
- CDN 히트율: **80% 이상**
- 비용: **<$0.50/클립**

---

### **Phase 3: AI 자동화 (3개월)**

#### Epic 3.1: AI 큐레이션

```yaml
Feature: "스토리 어시스턴트"

Input Examples:
  - "Tom Dwan의 베스트 블러프 5개"
  - "어제 메인 이벤트 하이라이트 3분"
  - "Phil Ivey vs Tom Dwan 대결 모음"

Processing:
  1. Natural Language Understanding (Gemini):
     - Extract: player_names, hand_types, time_range

  2. Multi-Stage Retrieval:
     - Stage 1: Vertex AI RAG (텍스트 검색)
     - Stage 2: 통계 분석 (pot_size, win_rate)
     - Stage 3: 극적 요소 점수 (all-in, river bluff)

  3. Auto Sequencing:
     - 선택된 5개 핸드를 스토리 순서로 배열
     - 전환 효과 자동 추가 (FFmpeg concat)

Output:
  - 단일 MP4 파일 (5분 하이라이트)
  - 챕터 마커 포함
  - 자막 자동 생성 (Gemini)
```

#### Epic 3.2: Vision-Based Auto Highlight

```yaml
Feature: "자동 리액션 감지"

Pipeline:
  1. Video AI Analysis:
     - Input: 2시간 파이널 테이블 영상
     - Process: Video Intelligence API (Google)
     - Detect:
         - Player facial expressions (surprise, excitement)
         - Chip movements (all-in detection)
         - Audio peaks (crowd reactions)

  2. Highlight Scoring:
     - Vision Score × Audio Score × Hand Importance
     - 상위 20개 순간 추출

  3. Auto Clipping:
     - 각 순간 전후 10초 클립 생성
     - Thumbnail 자동 선택 (가장 극적인 프레임)
```

---

## 4. 비용 분석

### 4.1 Phase 1 비용 (년간)

| 항목 | 비용 | 설명 |
|------|------|------|
| **GCP 인프라** |  |  |
| - BigQuery | $500/월 | 1TB 데이터, 10TB 쿼리/월 |
| - Vertex AI Search | $1,000/월 | 10M embeddings |
| - Cloud Run | $200/월 | 내부 100명 사용 |
| - GCS Storage | $300/월 | 10TB proxy + subclips |
| - Pub/Sub | $50/월 | 10K messages/day |
| **NAS** |  |  |
| - Local Agent | $0 | 기존 서버 활용 |
| - VPN/Interconnect | $300/월 | Cloud VPN |
| **인건비** |  |  |
| - GCP Engineer | $10K/월 | 1명 (풀타임) |
| **총 Phase 1** | **$147K/년** |  |

### 4.2 ROI 계산

```
현재 비용: $240K/년 (수동 클리핑)
Phase 1 비용: $147K/년
순 절감: $93K/년

Phase 1 개발 비용: $50K (6개월)
회수 기간: 6.5개월
```

**결론**: ✅ **7개월 내 투자금 회수**

---

## 5. 리스크 관리

### 5.1 기술 리스크

| 리스크 | 영향 | 완화 전략 |
|--------|------|----------|
| **타임코드 불일치** | 🔴 Critical | Phase 0 검증 시스템 필수 |
| **Local Agent SPOF** | 🟡 High | Primary + Standby 이중화 |
| **RAG 검색 품질** | 🟡 High | 피드백 시스템 + 지속 개선 |
| **NAS 네트워크 지연** | 🟢 Medium | GCS 캐싱 + Smart Tiering |

### 5.2 비상 계획

```yaml
Scenario 1: Local Agent Down
  - Standby Agent 자동 전환 (1분)
  - Slack 알림 → 즉시 재시작

Scenario 2: 타임코드 불일치 발견
  - 자동 Offset 계산 시도
  - 실패 시 수동 매칭 UI로 이동
  - 매칭 결과 DB 저장 (재사용)

Scenario 3: RAG 품질 저하
  - Precision@5 < 70%일 때 알림
  - A/B 테스트로 모델 비교
  - 피드백 데이터 재학습
```

---

## 6. 성공 지표

### 6.1 Phase 1 KPI

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| **검색 속도** | P95 < 10초 | Cloud Monitoring |
| **클립 생성** | P95 < 5분 | Pub/Sub latency |
| **검색 정확도** | Precision@5 > 75% | 사용자 피드백 분석 |
| **시스템 가용성** | 99.5% | Uptime monitoring |
| **사용자 만족도** | NPS > 50 | 월간 설문 |
| **비용 효율** | <$0.50/clip | BigQuery 비용 분석 |

### 6.2 Phase 2 KPI

| 지표 | 목표 |
|------|------|
| **글로벌 속도** | 전세계 어디서나 5초 내 재생 |
| **CDN 히트율** | 80% 이상 |
| **해외 지사 사용** | 3개 이상 지사 활성화 |

---

## 7. 기술 스택 최종 확정

```yaml
AI/ML:
  - LLM: Vertex AI Gemini 1.5 Pro
  - Embedding: textembedding-004
  - RAG: Vertex AI Search
  - Vision: Video Intelligence API (Phase 3)

Data:
  - Warehouse: BigQuery
  - ETL: Dataflow (또는 Cloud Composer)
  - Messaging: Pub/Sub

Compute:
  - Web App: Cloud Run (Python Flask)
  - Clipping: Local Agent (NAS) + Cloud Functions (Phase 2)
  - Batch: Cloud Batch (대량 프록시 생성)

Storage:
  - Master: NAS (On-prem)
  - Proxy: GCS Multi-region
  - Subclips: GCS Standard → Nearline (Smart Tiering)

Networking:
  - VPN: Cloud VPN (NAS ↔ GCP)
  - CDN: Media CDN (Phase 2)

Security:
  - Auth: IAP (Identity-Aware Proxy)
  - Secrets: Secret Manager
  - Audit: Cloud Logging
```

---

## 8. 다음 단계

### 즉시 실행 (Week 1)

1. ✅ **PRD 최종 승인**
2. ✅ **Phase 0 프로젝트 킥오프**
3. ✅ **GCP 프로젝트 생성**
4. ✅ **NSUS ATI 팀과 데이터 스키마 협의**

### Phase 0 (Week 2-12)

1. 타임코드 검증 시스템 개발
2. 1,000개 샘플 핸드로 검증
3. Offset 매핑 DB 구축
4. Phase 1 Go/No-Go 결정

---

## 부록 A: prd_gemini vs prd_gpt 비교

| 요소 | Gemini v2.2 | GPT v1.2 | Recommended v3.0 |
|------|-------------|----------|------------------|
| **클라우드 전략** | GCP + AWS | GCP + NAS | **GCP + NAS** ✅ |
| **비용** | 높음 ($358K/년) | 적정 ($147K/년) | **$147K/년** ✅ |
| **복잡도** | 높음 (멀티) | 중간 | **중간** ✅ |
| **글로벌 확장** | 명확 | 모호 | **명확 (Phase 2)** ✅ |
| **타임코드 검증** | ❌ 없음 | ❌ 없음 | **✅ Phase 0** |
| **품질 모니터링** | ❌ 없음 | ❌ 없음 | **✅ Feedback** |
| **AI 자동화** | ❌ 없음 | ⚠️ Phase 3 언급 | **✅ Phase 3 상세** |

---

## 부록 B: 예상 타임라인

```
2026 Q1           Q2              Q3              Q4
├─────────────┼───────────────┼───────────────┼──────────────┤
Phase 0       Phase 1         Phase 2         Phase 3
(3개월)       (6개월)         (3개월)         (3개월)

│             │               │               │
│ 타임코드    │ RAG 검색      │ Global CDN    │ AI 큐레이션
│ 검증        │ + 클리핑      │ + Tiering     │ + 자동화
│             │               │               │
└─────────────┴───────────────┴───────────────┴──────────────┘
             ↑                ↑               ↑
         MVP Launch      Global Launch    Full Auto
```

---

**결론**: 이 PRD는 **비용 효율성**과 **기술 안정성**을 모두 달성하며, **7개월 내 ROI**를 실현합니다.

**승인 요청**: GG Production 경영진 검토 후 Phase 0 착수 승인 요청
