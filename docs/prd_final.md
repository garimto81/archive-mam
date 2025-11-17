# PRD: POKER-BRAIN Archive System

**문서 버전**: 1.0 (Final)
**작성일**: 2025-11-17
**대상**: GG Production 사내 전용
**상태**: FINAL

---

## 1. 개요

**POKER-BRAIN**은 GG Production의 **포커 영상 아카이브 관리 및 검색 시스템**입니다.

**핵심 목적**:
- WSOP 인수로 확보한 **수십년치 방대한 포커 영상 데이터**를 효율적으로 아카이빙
- NSUS ATI 팀의 핸드 데이터를 활용한 **초고속 RAG 검색** 시스템 구축
- 기획자/편집자가 "찾을 수 없던" 영상을 **10초 이내 검색 가능**하게 만듦

---

## 2. 배경 및 Pain Points

### 2.1 WSOP 인수의 영향

```
2023년 GG Production, WSOP 영상 아카이브 인수
├── 1970년대부터 현재까지 약 50년치 영상
├── 총 영상 시간: 추정 100,000+ 시간
├── 이벤트 수: 5,000+ 토너먼트
└── 핸드 수: 추정 10,000,000+ 핸드
```

**문제**: 이 엄청난 양의 데이터를 **어떻게 관리하고 검색할 것인가?**

### 2.2 현재 Pain Points

| 문제 | 현재 상황 | 영향 |
|------|----------|------|
| **영상 검색 불가능** | "Tom Dwan의 2008년 블러프" 같은 장면을 찾을 수 없음 | 콘텐츠 제작 불가 |
| **데이터-영상 분리** | ATI 팀의 정확한 핸드 데이터가 있어도 영상과 연결 안 됨 | 데이터 사장(死藏) |
| **수동 탐색** | 편집자가 10시간 영상을 눈으로 스캔 | 1개 클립 찾는데 2-4시간 |
| **아카이브 방치** | 수십년치 영상이 NAS에만 저장, 활용도 제로 | 자산 낭비 |

**핵심**:
> "영상은 있는데 찾을 수가 없다" → **검색 불가능 = 존재하지 않는 것과 동일**

---

## 3. 목표

### 3.1 시스템 목표

**사내 운영 효율성 극대화** (외부 판매 아님)

| 목표 | 측정 지표 | 현재 | 목표 |
|------|----------|------|------|
| **영상 검색 가능화** | 검색 성공률 | 5% 미만 | **95% 이상** |
| **검색 속도** | 핸드 검색 시간 | 2-4시간 | **10초 이내** |
| **클립 생성** | 서브클립 생성 시간 | 1-2시간 | **5분 이내** |
| **아카이브 활용도** | 월간 검색 횟수 | 거의 없음 | **1,000+ 검색/월** |

**성공 정의**:
- ✅ 기획자가 "개떡같이 말해도" RAG가 "찰떡같이" 검색
- ✅ 50년치 아카이브가 살아있는 자산으로 전환
- ✅ 콘텐츠 제작 활성화: 월 100+ 클립 활용

---

## 4. 사용자 페르소나

### 4.1 한PD (콘텐츠 기획자)

**니즈**:
- "Tom Dwan이 2008년 WSOP에서 J4o로 블러프한 장면" 같은 스토리 클립을 즉시 찾고 싶음
- 과거 명장면을 활용한 기획안 작성

**현재 페인 포인트**:
- ATI 데이터: "2008_wsop_me_day3_hand154, Tom Dwan, J4o, all-in bluff"
- 하지만 이게 **어느 영상 파일의 몇 분 몇 초**인지 알 수 없음
- 결국 기획 포기 또는 수작업으로 2-4시간 소요

**시스템 사용 후**:
```
한PD: "Tom Dwan 2008 블러프"
시스템: [10초 후]
  - Hand #154 (2008 WSOP ME Day 3)
  - J4o all-in on river, won $450K pot
  - [미리보기 재생] [고화질 클립 다운로드]
```

---

### 4.2 김편집 (영상 편집자)

**니즈**:
- 한PD가 요청한 핸드 ID 리스트를 NAS 원본에서 정확히 클리핑
- 편집 타임라인에 바로 투입

**현재 페인 포인트**:
- NAS: `/poker/2008/wsop/main_event/day3_raw_footage.mp4` (10시간 분량)
- 이 안에서 Hand #154를 찾으려면 타임코드 정보 없이 눈으로 스캔
- FFmpeg로 클리핑해도 타임코드를 모르니 시행착오 반복

**시스템 사용 후**:
```
김편집: 한PD가 보낸 링크 클릭
시스템:
  - Hand #154
  - NAS path: /poker/2008/.../day3_raw.mp4
  - Timecode: 03:24:15 - 03:26:45
  - [고화질 다운로드] → 5분 내 완료
```

---

### 4.3 박팀장 (아카이브 관리자)

**니즈**:
- 50년치 영상 데이터가 제대로 보관되고 있는지 확인
- 핸드 데이터 ↔ 영상 타임코드 매핑 100% 달성

**현재 페인 포인트**:
- NAS에 영상만 쌓여있고 메타데이터 없음
- 어떤 영상이 어떤 이벤트인지 파일명으로만 추측
- 데이터 무결성 검증 불가능

**시스템 사용 후**:
- 모든 영상 파일의 메타데이터 BigQuery에 저장
- 타임코드 동기화 대시보드로 품질 모니터링
- 문제 영상 자동 감지 및 알림

---

## 5. 시스템 아키텍처

### 5.1 전체 구조

```
┌─────────────────────────────────────────────────────┐
│              Google Cloud Platform                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐         ┌──────────────────┐     │
│  │ NSUS ATI     │────────→│ BigQuery         │     │
│  │ Hand Data    │         │ - Hand Summary   │     │
│  └──────────────┘         │ - Timecode Map   │     │
│                           └────────┬─────────┘     │
│                                    ↓                │
│  ┌───────────────────────────────────────────┐     │
│  │   Vertex AI RAG Engine                    │     │
│  │   ┌─────────────────────────────────┐     │     │
│  │   │ Gemini: Summarization           │     │     │
│  │   │ "Tom Dwan all-in bluff J4o..."  │     │     │
│  │   └─────────────────────────────────┘     │     │
│  │   ┌─────────────────────────────────┐     │     │
│  │   │ TextEmbedding-004: Vector       │     │     │
│  │   │ 자연어 쿼리 → Embedding          │     │     │
│  │   └─────────────────────────────────┘     │     │
│  │   ┌─────────────────────────────────┐     │     │
│  │   │ Vector Search: 유사도 검색       │     │     │
│  │   │ "블러프" → 관련 핸드 100개       │     │     │
│  │   └─────────────────────────────────┘     │     │
│  └───────────────────┬───────────────────────┘     │
│                      ↓                              │
│  ┌──────────────────────────────────────┐          │
│  │   Cloud Run (Internal Web App)       │          │
│  │   - IAP 인증 (GG Production 임직원만)│          │
│  │   - 검색 UI + 미리보기                │          │
│  │   - 클립 다운로드 요청                │          │
│  └───────────────────┬──────────────────┘          │
│                      ↓                              │
│  ┌──────────────────────────────────────┐          │
│  │   Pub/Sub (클리핑 작업 큐)            │          │
│  └───────────────────┬──────────────────┘          │
│                      ↓                              │
└──────────────────────┼──────────────────────────────┘
                       ↓
         ┌─────────────────────────┐
         │  On-Premise NAS         │
         │  ┌──────────────────┐   │
         │  │ 50년치 영상 원본  │   │
         │  │ - 1970s ~ 2024   │   │
         │  │ - 100,000+ 시간  │   │
         │  └──────────────────┘   │
         │  ┌──────────────────┐   │
         │  │ Local Agent      │   │
         │  │ - Pub/Sub 구독   │   │
         │  │ - FFmpeg 클리핑  │   │
         │  │ - GCS 업로드     │   │
         │  └──────────────────┘   │
         └─────────────────────────┘
```

---

## 6. 핵심 기능

### 6.1 Phase 1: RAG 검색 + 클리핑 (사내 전용)

#### F-1.1: 자연어 검색

**Input**:
```
"Tom Dwan이 2008년 메인 이벤트에서 블러프한 장면"
```

**Processing**:
1. Gemini가 쿼리 이해 및 요약 생성
2. TextEmbedding-004로 벡터화
3. Vector Search로 유사 핸드 검색
4. BigQuery에서 메타데이터 필터링:
   - `player = "Tom Dwan"`
   - `year = 2008`
   - `event_type = "Main Event"`
   - `hand_category = "bluff"`

**Output**:
```json
{
  "results": [
    {
      "hand_id": "wsop2008_me_day3_hand154",
      "summary": "Tom Dwan, J4o, river all-in bluff vs Phil Hellmuth, won $450K pot",
      "timestamp_start": "2008-07-15T15:24:15Z",
      "timestamp_end": "2008-07-15T15:26:45Z",
      "nas_path": "/nas/poker/2008/wsop/main_event/day3_raw.mp4",
      "timecode_offset": "+3:24:15",
      "proxy_url": "gs://gg-proxy/wsop2008_me_d3_h154.mp4",
      "relevance_score": 0.94
    }
  ],
  "total": 12
}
```

---

#### F-1.2: 실시간 미리보기

**Flow**:
```
사용자 검색 결과 클릭
    ↓
Cloud Run이 GCS Proxy 영상 URL 서명
    ↓
HTML5 Video Player로 스트리밍 재생
    ↓
사용자가 정확한 장면인지 확인
```

**Proxy 스펙**:
- Resolution: 720p
- Bitrate: 2Mbps
- Codec: H.264
- 목적: 빠른 미리보기 (고화질은 다운로드로)

---

#### F-1.3: 고화질 클립 다운로드

**Flow**:
```
사용자 [다운로드] 버튼 클릭
    ↓
Cloud Run → Pub/Sub 메시지 발행
{
  "hand_id": "wsop2008_me_d3_h154",
  "nas_path": "/nas/.../day3_raw.mp4",
  "start_sec": 12255,  # 03:24:15
  "end_sec": 12405,    # 03:26:45
  "user_email": "han.pd@gg.com"
}
    ↓
NAS의 Local Agent가 메시지 수신
    ↓
FFmpeg 실행:
ffmpeg -ss 12255 -to 12405 \
       -i /nas/.../day3_raw.mp4 \
       -c copy -avoid_negative_ts make_zero \
       /tmp/wsop2008_me_d3_h154.mp4
    ↓
GCS에 업로드:
gs://gg-subclips/wsop2008_me_d3_h154.mp4
    ↓
사용자에게 다운로드 링크 제공 (Signed URL, 24시간 유효)
```

**타겟 성능**:
- 클립 생성 시간: **P95 < 5분**
- 동시 클리핑: 최대 10개 병렬 처리

---

### 6.2 Phase 2: 글로벌 확장 (선택적)

**목적**: 해외 지사(런던, LA)에서도 동일한 시스템 사용

**변경사항**:
- Proxy 영상: GCS Multi-region 버킷 (us, eu, asia)
- CDN: Media CDN (Google) 또는 CloudFront
- 서브클립: GCS에 저장 후 CDN으로 배포

**추가 비용 없는 이유**: GCS는 이미 글로벌

---

### 6.3 Phase 3: AI 자동화 (미래)

#### F-3.1: AI 큐레이션

**Input**:
```
"Tom Dwan의 베스트 블러프 10개를 타임라인으로 만들어줘"
```

**Processing**:
1. Vertex AI가 Tom Dwan의 모든 블러프 핸드 검색
2. 통계 분석: Pot size, Win rate, Opponent 등
3. 상위 10개 자동 선별
4. FFmpeg concat으로 단일 영상 생성
5. 챕터 마커 + 자막 자동 추가

**Output**:
- `tom_dwan_best_bluffs_2024.mp4` (15분 하이라이트)

---

#### F-3.2: Vision-Based Highlight

**목적**: 핸드 데이터 없이도 극적인 순간 자동 감지

**Process**:
```
2시간 파이널 테이블 영상 Input
    ↓
Video Intelligence API (Google)
    ↓
감지:
- 플레이어 표정 변화 (놀람, 흥분)
- Chip movement (all-in 감지)
- Audio peaks (관중 환호)
    ↓
극적 순간 20개 추출
    ↓
자동 클립 생성 + Thumbnail
```

---

## 7. 데이터 모델

### 7.1 BigQuery Schema

#### Table: `prod.hand_summary`

```sql
CREATE TABLE prod.hand_summary (
  -- 핸드 식별
  hand_id STRING NOT NULL PRIMARY KEY,
  event_id STRING,
  event_name STRING,  -- "2008 WSOP Main Event"
  tournament_day INT64,

  -- 타임스탬프
  timestamp_start_utc TIMESTAMP,
  timestamp_end_utc TIMESTAMP,
  duration_seconds FLOAT64,

  -- 영상 매핑 ⭐ 핵심
  nas_master_path STRING,  -- "/nas/poker/2008/.../day3.mp4"
  timecode_offset_seconds FLOAT64,  -- 12255 (03:24:15)
  proxy_gcs_path STRING,  -- "gs://gg-proxy/..."

  -- RAG 검색용
  searchable_summary_text STRING,  -- Gemini 생성 자연어 요약
  embedding ARRAY<FLOAT64>,  -- TextEmbedding-004 벡터

  -- 메타데이터
  players ARRAY<STRING>,
  pot_size_usd NUMERIC,
  hand_category STRING,  -- "bluff", "cooler", "suckout" 등

  -- 품질 관리
  timecode_sync_score FLOAT64,  -- 0-100 (Phase 0에서 계산)
  last_accessed TIMESTAMP,
  access_count INT64
);
```

---

#### Table: `prod.video_files`

```sql
CREATE TABLE prod.video_files (
  -- 파일 식별
  file_id STRING NOT NULL PRIMARY KEY,
  nas_path STRING,
  file_name STRING,

  -- 메타데이터
  event_id STRING,
  recording_date DATE,
  duration_seconds FLOAT64,
  file_size_bytes INT64,
  resolution STRING,  -- "1920x1080"
  codec STRING,

  -- 상태
  is_archived BOOL,  -- GCS에 백업 여부
  created_at TIMESTAMP
);
```

---

## 8. Phase 로드맵

### Phase 0: 타임코드 검증 (3개월)

**목표**: ATI 핸드 데이터 ↔ NAS 영상 타임코드 100% 동기화

**산출물**:
- 1,000개 샘플 핸드로 검증 시스템 구축
- Vision AI로 포커 장면 자동 검증
- Offset 자동 계산 알고리즘
- 수동 매칭 UI (예외 처리)

**성공 기준**: 95% 이상 자동 매칭, 98% 최종 성공률

---

### Phase 1: RAG 검색 + 클리핑 (6개월)

**범위**: 사내 전용 시스템 구축

**Epic**:
1. BigQuery ETL 파이프라인 (NSUS ATI → BigQuery)
2. Vertex AI RAG 엔진 구축
3. Cloud Run 웹 앱 (검색 UI)
4. NAS Local Agent (클리핑)

**산출물**:
- 사내 임직원 100명 사용 가능
- 월 1,000+ 검색
- 월 100+ 클립 생성

---

### Phase 2: 글로벌 확장 (3개월)

**범위**: 해외 지사 접근 가능

**변경**:
- GCS Multi-region
- Media CDN
- Global IAP 설정

---

### Phase 3: AI 자동화 (3개월)

**범위**: AI 큐레이션 + Vision Highlight

---

## 9. 기술 스택

| 영역 | 기술 | 이유 |
|------|------|------|
| **AI/RAG** | Vertex AI (GCP) | 관리형, 한글 지원, GCP 네이티브 통합 |
| **LLM** | Gemini 1.5 Pro | Summarization, 자연어 이해 |
| **Embedding** | TextEmbedding-004 | 다국어, 성능 우수 |
| **Vector DB** | Vertex AI Vector Search | 관리형, BigQuery 통합 |
| **Data** | BigQuery | 페타바이트급 스케일, SQL 친화적 |
| **Compute** | Cloud Run | 서버리스, Auto-scaling |
| **Storage (Master)** | NAS (On-prem) | 저비용, 빠른 Random Access |
| **Storage (Proxy)** | GCS Multi-region | 글로벌 접근 |
| **Messaging** | Pub/Sub | 비동기 클리핑 작업 큐 |
| **Clipping** | FFmpeg (Local Agent) | 산업 표준 |
| **Auth** | IAP (Identity-Aware Proxy) | GG Production 임직원만 접근 |

---

## 10. 비기능 요구사항

### 10.1 성능

| 지표 | 목표 |
|------|------|
| 검색 응답 시간 | P95 < 10초 |
| 클립 생성 시간 | P95 < 5분 |
| 동시 사용자 | 100명 |
| 동시 클리핑 | 10개 |

---

### 10.2 가용성

| 지표 | 목표 |
|------|------|
| Uptime | 99.5% (사내 도구 수준) |
| Local Agent HA | Primary + Standby |
| 백업 | 일간 BigQuery 스냅샷 |

---

### 10.3 보안

| 항목 | 구현 |
|------|------|
| 인증 | IAP (Google Workspace 계정) |
| 권한 | IAM Role-Based Access Control |
| 데이터 암호화 | GCS 자동 암호화 |
| 네트워크 | Cloud VPN (NAS ↔ GCP) |
| 감사 | Cloud Logging (모든 검색/다운로드 기록) |

---

## 11. 성공 지표

### 11.1 Phase 1 KPI

| 지표 | 측정 방법 | 목표 |
|------|----------|------|
| **검색 성공률** | (관련 결과 있는 검색 / 전체 검색) × 100 | **95%** |
| **검색 정확도** | Precision@5 (상위 5개 결과 관련성) | **80%** |
| **시스템 사용률** | 월간 Active Users | **50명** |
| **클립 생성량** | 월간 다운로드 클립 수 | **100개** |
| **아카이브 활용도** | 검색된 영상 파일 수 / 전체 파일 수 | **30%** |

---

### 11.2 사용자 만족도

| 측정 | 방법 | 목표 |
|------|------|------|
| NPS | 분기별 설문 | > 50 |
| 검색 품질 | 👍/👎 피드백 | 👍 > 80% |
| 재사용률 | 동일 사용자 월 2회 이상 사용 | > 70% |

---

## 12. 제약사항 및 가정

### 12.1 제약사항

1. **NAS 네트워크**:
   - GCP와 안정적인 VPN 필요
   - 대역폭: 최소 1Gbps

2. **ATI 데이터 품질**:
   - 타임스탬프 정확도 100% 가정
   - 스키마 변경 시 사전 공유 필수

3. **영상 파일 포맷**:
   - MP4/MOV 표준 코덱만 지원
   - 비표준 포맷은 사전 변환 필요

---

### 12.2 가정

1. ✅ NSUS ATI 데이터는 지속적으로 업데이트됨
2. ✅ NAS 저장 공간은 충분함 (현재 500TB, 확장 가능)
3. ✅ GG Production 임직원 100명이 주요 사용자
4. ✅ 월 1,000+ 검색 예상 (Phase 1)

---

## 13. 리스크 및 완화

| 리스크 | 영향 | 확률 | 완화 전략 |
|--------|------|------|----------|
| **타임코드 불일치** | 🔴 Critical | 30% | **Phase 0 검증 시스템** 필수 |
| **Local Agent SPOF** | 🟡 High | 20% | Primary + Standby 이중화 |
| **NAS 네트워크 장애** | 🟡 High | 15% | 샘플 영상 GCS 백업 |
| **RAG 검색 품질** | 🟡 Medium | 25% | 피드백 시스템 + 지속 개선 |
| **ATI 데이터 지연** | 🟢 Low | 10% | 더미 데이터로 개발 진행 |

---

## 14. 예산 및 리소스

### 14.1 GCP 비용 (Phase 1, 월간)

| 서비스 | 사용량 | 비용 |
|--------|--------|------|
| BigQuery | 1TB 저장, 10TB 쿼리 | $500 |
| Vertex AI Search | 10M embeddings | $1,000 |
| Cloud Run | 100 users, 10K requests | $200 |
| GCS Storage | 10TB (Proxy + Subclips) | $300 |
| Pub/Sub | 10K messages/day | $50 |
| Cloud VPN | 1 tunnel | $300 |
| **총합** |  | **$2,350/월** |

**연간**: ~$28K

---

### 14.2 인력

| 역할 | 인원 | 기간 |
|------|------|------|
| Tech Lead | 1명 | 9개월 (Phase 0-1) |
| Backend Engineer | 1명 | 9개월 |
| Data Engineer | 0.5명 | 6개월 (Phase 0-1) |
| QA | 0.5명 | 3개월 (Phase 1) |

---

## 15. 다음 단계

### Week 1 (즉시)

- [ ] PRD 최종 승인
- [ ] GCP 프로젝트 생성
- [ ] NSUS ATI 팀 킥오프 미팅
- [ ] NAS 접근 권한 확보

### Week 2 (Phase 0 시작)

- [ ] ATI 샘플 데이터 1,000개 수신
- [ ] BigQuery 테이블 설계
- [ ] Vision AI POC (10개 샘플)

### Month 3 (Phase 0 완료)

- [ ] 타임코드 검증 시스템 완성
- [ ] 98% 동기화 성공률 달성
- [ ] Phase 1 Go/No-Go 결정

---

**문서 작성자**: Claude (GG Production AI Assistant)
**최종 검토**: aiden.kim@ggproduction.net
**승인 대기 중**
