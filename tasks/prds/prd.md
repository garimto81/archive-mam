# GGProduction 포커 아카이브 자연어 검색 시스템 PRD

(ATI 분석 + 자체 PostgreSQL 기반, 외부 MAM(Media Asset Management, 미디어 자산 관리 시스템) 미사용)

---

## 0. 문서 개요

* 문서명: GGProduction 포커 아카이브 자연어 검색 시스템 PRD
* 버전: v1.0
* 작성: ChatGPT (초안), 최종 책임: GGProduction Trey
* 주요 이해관계자

  * **GGProduction**: 포커 대회 방송/아카이브 운영 주체
  * **ATI 팀**: NSUS 산하 AI 컨설팅/엔지니어링 팀, 포커 영상 분석 솔루션 제공
* 핵심 전제

  * 외부 MAM(Media Asset Management, 미디어 자산 관리 시스템) 솔루션 **사용하지 않음**
  * GGProduction 자체 스토리지 + **PostgreSQL(포스트그레스, 오픈소스 관계형 데이터베이스)** + ATI 분석 메타데이터만으로 시스템 완결
  * 자연어 검색은 **GGProduction 고유 솔루션**으로 자체 개발

---

## 1. 배경 및 문제 정의

### 1.1 배경

GGProduction은 WSOP, MPP, APL 등 장기 포커 대회 방송을 제작하며, 한 이벤트당 수백 시간, 연간 수천 시간의 포커 VOD(Video On Demand, 주문형 영상)를 생산하고 있다. 이 영상들은:

* 향후 **하이라이트/리캡/소셜 클립/리뷰 콘텐츠** 제작의 핵심 자산이며,
* 내부 회의/교육/세일즈 자료로도 활용 가치를 지닌다.

NSUS의 ATI 팀은 GGProduction을 위해:

* 포커 특화 영상 분석 솔루션을 이미 설계/개발했고,
* 이 솔루션은 **핸드 단위 구분, 플레이어 인식, 칩 스택 변화, 액션(콜/레이즈/폴드 등) 추출**이 가능하다.

현재 상황:

* ATI 분석 결과(메타데이터)는 존재하나,
* 이를 **통합적으로 저장/검색/활용**할 수 있는 GGProduction 전용 아카이브 시스템은 부재.
* 특히, 아래와 같은 “자연어 리퀘스트”를 만족시키는 도구가 없음:

  * “정글맨 미친 리버 콜 모아서 보여줘”
  * “헬뮤스 빡쳐서 욕한 핸드들”
  * “버블 직전 30bb 이상 올인해서 탈락한 핸드만 뽑아줘”

### 1.2 문제

1. **핸드/플레이어/상황 단위로 검색이 불가능**

   * 파일 단위 접근이라 원하는 핸드를 찾는 데 시간이 많이 걸림.
2. **별명/오타/슬랭/한·영 혼합 검색 불가**

   * `정글맨`, `jungelman`, `정글맨12` 등 다양한 표현을 통합해서 인식하는 구조가 없음.
3. **메타데이터 저장소가 통합되어 있지 않음**

   * ATI 분석 결과가 JSON/로그/임시 저장소에 흩어져 있을 가능성.
4. **외부 MAM 솔루션 도입 시 비용/락인 문제**

   * 라이선스, 장기 비용, 커스터마이징 제약 등을 회피하고 싶음.

---

## 2. 목표

### 2.1 최상위 목표

> **“개떡같이 말해도 찰떡같이 찾아주는,
> 포커 업계 최고의 자연어 기반 아카이브 검색 시스템을
> GGProduction 내부 자산(PostgreSQL + ATI 메타데이터)만으로 구축한다.”**

### 2.2 구체 목표

1. **자연어 검색 지원**

   * 한국어/영어/별명/오타/포커 슬랭이 섞인 문장으로 검색 가능
   * 예: `정글맨 미친 콜`, `헬무스 빡친 핸드`, `버블 직전 올인 상황`
2. **핸드/클립 단위 검색**

   * ‘영상 파일’이 아닌, **핸드(Hand)/클립(Clip)** 단위로 검색 결과 제공
3. **자체 메타데이터 허브 구축**

   * PostgreSQL를 중심으로 모든 메타데이터를 통합 관리
4. **자체 영상 재생**

   * NAS/클라우드 스토리지에 저장된 영상을 자체 웹 플레이어로 재생
5. **확장 가능한 구조**

   * 초기에는 키워드 + Query Rewrite 기반
   * 향후 임베딩(Embedding, 문장 벡터)을 이용한 시멘틱 검색으로 확장 가능

### 2.3 비범위(이번 버전에서 제외)

* 외부 MAM 솔루션 연동 (명시적으로 **사용하지 않음**)
* 실시간 라이브 스트림에 대한 실시간 검색
* 완전 자동 하이라이트/요약 영상 생성
* 프리미어/다빈치 리졸브와의 플러그인 수준 통합 (향후 단계에서 고려)

---

## 3. 시스템 전반 구조

### 3.1 상위 아키텍처

```text
[포커 대회 영상 촬영본] 
      ↓ (파일 업로드/인제스트)

[스토리지 계층]
- 온프레 NAS(Network Attached Storage, 네트워크 연결 스토리지)
- 또는 클라우드 스토리지(AWS S3, GCP Storage 등)

      ↓ (파일 경로/ID 전달)

[ATI 포커 분석 파이프라인]
- 핸드 구분(start/end time)
- 플레이어 인식(좌석별 누구인지)
- 칩 변화 파악(stack before/after)
- 액션 시퀀스(call/raise/bet/fold/all-in)
- 주요 이벤트 태그(hero call, big pot, bubble 등)

      ↓ (Raw Metadata: JSON/Firestore/기타 → ETL)

[GGProduction 메타데이터 허브: PostgreSQL]
- tournaments
- players
- hands
- hand_players
- clips
- actions
- tags

      ↓ (정기 인덱싱 배치)

[검색 엔진: Typesense (오픈소스 검색엔진)]
- players 인덱스
- hands 인덱스
- clips 인덱스

      ↓

[자연어 검색 브레인]
- Query Rewrite(별명/동의어/슬랭/오타 처리)
- 검색 쿼리 → Typesense 호출
- 필터 조건(pot_size, 태그 등) 반영

      ↓

[검색 UI: React + Ant Design 기반 웹앱]
- 검색창 + 자동완성
- 필터 패널
- 결과 리스트
- 세부 정보 + 자체 플레이어(HLS 등) 재생
```

---

## 4. 주요 컴포넌트별 설명

### 4.1 스토리지 계층

* 옵션 1: 온프레 NAS(Network Attached Storage, 네트워크 스토리지)
* 옵션 2: 클라우드 오브젝트 스토리지(AWS S3, GCP Cloud Storage 등)
* 시스템 기준 요구사항:

  * 각 영상 파일에 대해 **고유 식별자(video_id)** 부여
  * 파일 경로/URL이 PostgreSQL에 저장되어 검색 결과와 연결될 수 있어야 함
  * HLS(HTTP Live Streaming) 혹은 MP4 progressive 재생 지원 준비

### 4.2 ATI 포커 분석 파이프라인

* 입력: 스토리지에 저장된 영상의 경로/ID
* 출력(핵심 메타데이터):

  * 핸드 단위:

    * hand_id (생성 규칙 협의)
    * start_time_sec, end_time_sec
    * 관련 플레이어 seat 정보
    * board 카드 정보
    * pot_size(칩 기준, BB 단위 변환 포함)
    * hero call 여부, all-in 여부 등
  * 액션 로그:

    * 액션 순서
    * player_id
    * 액션 종류(BET, CALL, FOLD, RAISE, ALL-IN 등)
    * 베팅 사이즈(칩/BB)
  * 리액션/클립 후보:

    * big pot 이후 리액션
    * 플레이어 표정/제스처
    * 테이블 전체 리액션 등
* 저장 방식:

  * 초기에는 JSON/Firestore/전용 DB 등 ATI 쪽 포맷 그대로 유지 가능
  * 이후 GG 측 ETL 파이프라인에서 PostgreSQL로 통합

### 4.3 PostgreSQL 메타데이터 허브

**이 계층이 ‘진짜’ MAM 역할을 한다.**
핵심 테이블:

#### 4.3.1 tournaments 테이블

```text
tournaments
- id            (PK)   예: 'wsop_2025_sc_cyprus'
- name          (text) 예: 'WSOP Super Circuit Cyprus 2025'
- location      (text)
- start_date    (date)
- end_date      (date)
- created_at    (timestamp)
- updated_at    (timestamp)
```

#### 4.3.2 players 테이블

```text
players
- id            (PK)   예: 'daniel_cates'
- name          (text) 예: 'Daniel Cates'
- name_kor      (text) 예: '다니엘 케이츠'
- aliases       (text[]) 예: ['Jungleman', '정글맨', 'Jungle', 'Jungleman12']
- country       (text, nullable)
- notes         (text, nullable)
- created_at    (timestamp)
- updated_at    (timestamp)
```

#### 4.3.3 hands 테이블

```text
hands
- id                (PK)  예: 'hand_wsop2025_ft_000123'
- tournament_id     (FK → tournaments.id)
- day_label         (text)   예: 'Day 3', 'Final'
- table_name        (text)   예: 'Feature Table', 'Outer 1'
- level             (text)   예: 'Level 28'
- blind_info        (text)   예: '40k/80k/80k'

- video_id          (text)   스토리지 내 영상 식별자
- video_path        (text)   파일 또는 HLS URL 경로

- start_time_sec    (int)
- end_time_sec      (int)

- pot_size_bb       (float)
- tags              (text[]) 예: ['ALL_IN', 'BIG_POT', 'HERO_CALL', 'BUBBLE']

- description       (text)   자연어 요약 (ATI or 편집자가 작성/보정)
- language_tokens   (text)   검색용 문자열(본명/별명/슬랭/상황 설명 등 한·영 합쳐서)

- created_at        (timestamp)
- updated_at        (timestamp)
```

#### 4.3.4 hand_players 테이블

```text
hand_players
- id               (PK, serial)
- hand_id          (FK → hands.id)
- player_id        (FK → players.id)
- seat_no          (int, nullable)
- starting_stack   (int, nullable)  칩 수
- ending_stack     (int, nullable)
- is_hero          (boolean, nullable)
```

#### 4.3.5 clips 테이블

```text
clips
- id               (PK)
- hand_id          (FK → hands.id, nullable)  핸드에 속한 경우
- tournament_id    (FK → tournaments.id, nullable)
- video_id         (text)
- video_path       (text)
- start_time_sec   (int)
- end_time_sec     (int)
- tags             (text[])  예: ['REACTION', 'TILT', 'PROFANITY']
- description      (text)
- language_tokens  (text)
- created_at       (timestamp)
- updated_at       (timestamp)
```

#### 4.3.6 actions 테이블

```text
actions
- id               (PK)
- hand_id          (FK → hands.id)
- order_index      (int)       액션 순서
- player_id        (FK → players.id)
- action_type      (text)      예: 'BET', 'CALL', 'FOLD', 'RAISE', 'ALL_IN'
- amount_bb        (float, nullable)
- timestamp_sec    (int)       영상 내 상대적 시간 (필요 시)
```

---

## 5. 검색 인덱스 설계 (Typesense)

Typesense는 텍스트 기반 검색엔진.
이번 버전에서는 **벡터/임베딩 없이**, 키워드 + 오타 허용 + Facet 필터 수준으로 사용.

### 5.1 players 인덱스

문서 예시:

```json
{
  "id": "daniel_cates",
  "name": "Daniel Cates",
  "name_kor": "다니엘 케이츠",
  "aliases": ["Jungleman", "정글맨", "Jungleman12"],
  "search_tokens": "Daniel Cates 다니엘 케이츠 Jungleman 정글맨 Jungleman12"
}
```

* `search_tokens`: 이름 + 한글 이름 + alias 전부 합친 문자열
* `query_by`: `search_tokens`
* 용도: 플레이어 자동완성/추천

### 5.2 hands 인덱스

문서 예시:

```json
{
  "id": "hand_wsop2025_ft_000123",
  "tournament_id": "wsop_2025_sc_cyprus",
  "tournament_name": "WSOP Super Circuit Cyprus 2025",
  "day_label": "Final",
  "table_name": "Feature Table",
  "level": "Level 28",
  "player_ids": ["daniel_cates", "phil_hellmuth"],
  "player_names": ["Daniel Cates", "Phil Hellmuth"],
  "tags": ["HERO_CALL", "BIG_POT"],
  "pot_size_bb": 78,
  "description": "Daniel Cates river hero call vs bluff",
  "language_tokens": "Daniel Cates 다니엘 케이츠 Jungleman 정글맨 hero call 미친 콜 big pot 올인 river",
  "video_id": "wsop2025_ft_main",
  "video_path": "/videos/wsop2025/ft_main.m3u8",
  "start_time_sec": 12345,
  "end_time_sec": 12420
}
```

* `query_by`: `"language_tokens,description"`
* `filter_by`:

  * `tournament_id:=...`
  * `player_ids:=[daniel_cates]`
  * `tags:=[HERO_CALL]`
  * `pot_size_bb:>40`

### 5.3 clips 인덱스

hands와 유사, 다만 `hand_id` nullable, 태그가 주로 리액션/감정 위주.

---

## 6. 자연어 검색 브레인 (Query Rewrite 레이어)

### 6.1 역할

* 사용자가 “개떡같이” 입력한 텍스트를:

  * **별명/오타/슬랭/한·영 혼합**을 정규화하고,
  * 검색 엔진이 다루기 좋은 텍스트 + 구조화된 필터로 쪼개는 계층.

### 6.2 기능

1. **별명(Alias) 맵핑**

   * `정글맨`, `jungelman`, `정글맨12`, `jungle` 등 → `Daniel Cates Jungleman`
   * `헬뮤스`, `헬무스`, `헬뮤쓰`, `hellmuth` → `Phil Hellmuth 헬뮤스`
2. **포커 슬랭/표현 맵핑**

   * `미친 콜`, `지린 콜`, `말도 안 되는 콜` → `hero call`
   * `빡친`, `화난`, `열받은` → `tilt`, `angry reaction`
   * `쿠올`, `콜박`, 등 구어체도 지원 가능
3. **숫자 조건 추출**

   * `30bb 이상`, `50bb 넘는` → `min_pot_size_bb = 30/50`
4. **상황 표현 추출**

   * `버블 직전` → `tags`에 `'BUBBLE'` 포함 AND 시간/레벨 조건
   * `파이널테이블` → `day_label = 'Final' OR tags=['FT']`

### 6.3 처리 흐름 예시

입력:

> “정글맨 미친 리버 콜 보여줘”

1. 토큰화: `['정글맨', '미친', '리버', '콜', '보여줘']`
2. 별명 정규화:

   * `정글맨` → `"Daniel Cates Jungleman"`
3. 슬랭 정규화:

   * `미친 콜` → `hero call`
4. 최종 검색 문자열:

   * `"Daniel Cates Jungleman hero call river"`
5. 필터 추출:

   * `player_ids:=['daniel_cates']` (선택적 적용)

---

## 7. 검색 API 설계

백엔드는 Node.js/TypeScript 기준으로 설계.

### 7.1 `/api/suggestPlayer` (GET)

* 목적: 검색창에서 플레이어 자동완성 제공
* 파라미터:

  * `q`: string (사용자 입력 일부)
* 처리:

  * 필요 시 간단한 Query Rewrite
  * Typesense `players` 인덱스에 `query_by=search_tokens`로 검색
* 응답 예시:

```json
[
  {
    "player_id": "daniel_cates",
    "display_name": "Daniel Cates",
    "match_label": "정글맨 (Jungleman)"
  },
  {
    "player_id": "daniel_cates",
    "display_name": "Daniel Cates",
    "match_label": "Jungleman12"
  }
]
```

### 7.2 `/api/searchHands` (POST)

* 요청 Body 예시:

```json
{
  "queryText": "정글맨 미친 리버 콜",
  "playerId": "daniel_cates",
  "tournamentId": "wsop_2025_sc_cyprus",
  "dayLabel": "Final",
  "tags": ["HERO_CALL"],
  "minPotSizeBB": 30
}
```

* 처리 흐름:

  1. `queryText` → Query Rewrite
  2. Typesense `hands` 인덱스에 검색

     * `q = rewrittenText`
     * `query_by = "language_tokens,description"`
     * `filter_by` = playerId, tournamentId, tags, pot_size 조건
  3. 결과를 DTO 형태로 정제 후 반환

* 응답 예시:

```json
{
  "total": 5,
  "hits": [
    {
      "handId": "hand_wsop2025_ft_000123",
      "tournamentName": "WSOP Super Circuit Cyprus 2025",
      "dayLabel": "Final",
      "tableName": "Feature Table",
      "players": ["Daniel Cates", "Player B"],
      "tags": ["HERO_CALL", "BIG_POT"],
      "potSizeBB": 78,
      "videoPath": "/videos/wsop2025/ft_main.m3u8",
      "startTimeSec": 12345,
      "endTimeSec": 12420,
      "description": "Daniel Cates river hero call vs bluff"
    }
  ]
}
```

### 7.3 `/api/searchClips` (POST)

* 구조는 `searchHands`와 유사, 대상 인덱스만 `clips`.

---

## 8. 검색 UI (React + Ant Design)

### 8.1 요구사항 요약

* 상단:

  * 메인 검색창 (자연어 입력)
  * 플레이어 자동완성(dropdown)
* 좌측:

  * 필터 패널:

    * Tournament
    * Day
    * Tags
    * Pot Size (BB slider)
* 중앙:

  * 검색 결과 리스트 (Card/Grid)
* 우측/Drawer:

  * 선택된 핸드/클립 상세 정보
  * 자체 플레이어로 재생 버튼

### 8.2 UX 플로우 예시

1. 사용자가 검색창에 `정글맨 미친 콜` 입력
2. 아래 자동완성에 `정글맨 – Daniel Cates` 제안
3. 사용자가 제안 클릭 → 내부 state에 `playerId = daniel_cates` 저장
4. “검색” 클릭 → `/api/searchHands` 호출
5. 결과 리스트에서 카드 클릭 → 오른쪽 Drawer에 상세 정보 + 재생 버튼
6. 재생 버튼 클릭 → HLS 플레이어가 `/videos/...m3u8` 로드, `startTimeSec`부터 재생

---

## 9. 비기능 요구사항

* 성능:

  * 일반 검색 요청에 대해 500ms 이내 응답(검색 엔진 + API)
* 동시 사용자:

  * 내부용 기준 5~20명
* 안정성:

  * PostgreSQL/Typesense는 일 1회 이상 백업
* 보안:

  * 시스템은 사내망 또는 VPN을 통해서만 접속 가능
* 비용:

  * PostgreSQL: Supabase/자체 호스팅 저비용 플랜
  * Typesense: 1vCPU/2GB RAM 정도의 VM에서 Docker 실행

---

## 10. GCS 영상 관리 대시보드 (신규 기능)

### 10.1 배경 및 목적

**문제**:
- GCS 버킷에 업로드된 영상들의 현황 파악 어려움
- 어떤 영상이 분석 완료되었는지, 어떤 영상이 대기 중인지 확인 불가
- qwen_hand_analysis 분석 파이프라인 진행 상황 모니터링 필요

**목적**:
- **영상 자산 가시성 확보**: GCS 버킷 내 모든 영상 파일 리스트 조회
- **분석 진행 상태 추적**: 각 영상의 분석 완료/대기/실패 여부 실시간 확인
- **관리 효율성 향상**: 미분석 영상 우선순위 지정 및 재분석 트리거

### 10.2 핵심 기능

#### 10.2.1 GCS 버킷 영상 리스트 조회

**API 엔드포인트**: `GET /api/videos/list`

**쿼리 파라미터**:
```json
{
  "bucket": "poker-videos-prod",
  "prefix": "wsop_2024/",
  "limit": 50,
  "page_token": "next_page_token"
}
```

**응답 예시**:
```json
{
  "total": 127,
  "videos": [
    {
      "video_id": "wsop_2024_main_event_day1_table1.mp4",
      "gcs_path": "gs://poker-videos-prod/wsop_2024/day1/table1.mp4",
      "file_size_mb": 4850,
      "upload_date": "2024-07-15T10:30:00Z",
      "analysis_status": "completed",
      "analysis_date": "2024-07-15T14:20:00Z",
      "hand_count": 42,
      "metadata_available": true
    },
    {
      "video_id": "wsop_2024_main_event_day2_table3.mp4",
      "gcs_path": "gs://poker-videos-prod/wsop_2024/day2/table3.mp4",
      "file_size_mb": 5120,
      "upload_date": "2024-07-16T09:15:00Z",
      "analysis_status": "pending",
      "analysis_date": null,
      "hand_count": 0,
      "metadata_available": false
    },
    {
      "video_id": "wsop_2024_main_event_day2_table5.mp4",
      "gcs_path": "gs://poker-videos-prod/wsop_2024/day2/table5.mp4",
      "file_size_mb": 4920,
      "upload_date": "2024-07-16T09:20:00Z",
      "analysis_status": "failed",
      "analysis_date": "2024-07-16T12:30:00Z",
      "hand_count": 0,
      "metadata_available": false,
      "error_message": "Video format not supported"
    }
  ],
  "next_page_token": "CiAKGGx..."
}
```

**분석 상태 (analysis_status)**:
- `completed`: qwen_hand_analysis 분석 완료, BigQuery에 메타데이터 저장됨
- `pending`: 영상 업로드 완료, 분석 대기 중
- `processing`: 현재 분석 진행 중
- `failed`: 분석 실패 (오류 메시지 포함)
- `unknown`: 상태 불명 (GCS에 있으나 분석 이력 없음)

#### 10.2.2 분석 상태 확인 로직

**데이터 소스 통합**:
```sql
-- BigQuery에서 분석 완료 영상 조회
SELECT
  video_url,
  COUNT(*) as hand_count,
  MAX(created_at) as analysis_date
FROM `poker_archive.hands`
GROUP BY video_url

-- GCS Storage API로 버킷 파일 리스트 조회
-- Python: storage_client.list_blobs('poker-videos-prod')

-- 두 데이터 조인하여 분석 상태 판단
IF video_id IN bigquery_results THEN
  status = 'completed'
ELSE IF video_id IN analysis_queue THEN
  status = 'processing'
ELSE
  status = 'pending'
```

#### 10.2.3 대시보드 UI 컴포넌트

**위치**: `frontend/src/app/admin/videos/page.tsx`

**주요 섹션**:

1. **통계 요약 카드** (상단)
   ```tsx
   <div className="grid grid-cols-4 gap-4">
     <StatCard
       title="전체 영상"
       value={127}
       icon={<VideoIcon />}
     />
     <StatCard
       title="분석 완료"
       value={85}
       percentage={67}
       status="success"
     />
     <StatCard
       title="대기 중"
       value={38}
       percentage={30}
       status="warning"
     />
     <StatCard
       title="실패"
       value={4}
       percentage={3}
       status="error"
     />
   </div>
   ```

2. **필터 패널** (좌측/상단)
   ```tsx
   <FilterPanel>
     <Select label="분석 상태">
       <Option value="all">전체</Option>
       <Option value="completed">완료</Option>
       <Option value="pending">대기</Option>
       <Option value="failed">실패</Option>
     </Select>
     <Select label="대회">
       <Option value="all">전체 대회</Option>
       <Option value="wsop_2024">WSOP 2024</Option>
       <Option value="mpp_2024">MPP 2024</Option>
     </Select>
     <DateRangePicker label="업로드 기간" />
   </FilterPanel>
   ```

3. **영상 리스트 테이블** (중앙)
   ```tsx
   <Table>
     <thead>
       <tr>
         <th>영상 ID</th>
         <th>파일 크기</th>
         <th>업로드 일시</th>
         <th>분석 상태</th>
         <th>핸드 수</th>
         <th>작업</th>
       </tr>
     </thead>
     <tbody>
       {videos.map(video => (
         <tr key={video.video_id}>
           <td>{video.video_id}</td>
           <td>{video.file_size_mb} MB</td>
           <td>{formatDate(video.upload_date)}</td>
           <td>
             <StatusBadge status={video.analysis_status} />
           </td>
           <td>{video.hand_count}</td>
           <td>
             <ActionMenu>
               <MenuItem>상세 보기</MenuItem>
               <MenuItem disabled={video.analysis_status === 'completed'}>
                 재분석 요청
               </MenuItem>
               <MenuItem>영상 미리보기</MenuItem>
             </ActionMenu>
           </td>
         </tr>
       ))}
     </tbody>
   </Table>
   ```

4. **상태 배지 컴포넌트**
   ```tsx
   function StatusBadge({ status }: { status: string }) {
     const config = {
       completed: { color: 'green', text: '완료', icon: <CheckIcon /> },
       pending: { color: 'yellow', text: '대기', icon: <ClockIcon /> },
       processing: { color: 'blue', text: '분석 중', icon: <LoadingIcon /> },
       failed: { color: 'red', text: '실패', icon: <ErrorIcon /> },
       unknown: { color: 'gray', text: '불명', icon: <QuestionIcon /> }
     };

     const { color, text, icon } = config[status];

     return (
       <Badge color={color} icon={icon}>
         {text}
       </Badge>
     );
   }
   ```

### 10.3 백엔드 구현

#### 10.3.1 API 엔드포인트

**파일**: `backend/app/api/videos.py`

```python
from fastapi import APIRouter, Query
from google.cloud import storage, bigquery
from app.models import VideoListResponse, VideoItem

router = APIRouter()

@router.get("/api/videos/list", response_model=VideoListResponse)
async def list_videos(
    bucket: str = Query("poker-videos-prod"),
    prefix: str = Query(""),
    limit: int = Query(50, le=100),
    page_token: str = Query(None)
):
    """GCS 버킷 영상 리스트 + 분석 상태 조회"""

    # 1. GCS에서 파일 리스트 가져오기
    storage_client = storage.Client()
    bucket_obj = storage_client.bucket(bucket)
    blobs = bucket_obj.list_blobs(
        prefix=prefix,
        max_results=limit,
        page_token=page_token
    )

    # 2. BigQuery에서 분석 완료 영상 조회
    bq_client = bigquery.Client()
    query = """
        SELECT
            video_url,
            COUNT(*) as hand_count,
            MAX(created_at) as analysis_date
        FROM `poker_archive.hands`
        GROUP BY video_url
    """
    analyzed_videos = {
        row.video_url: {
            'hand_count': row.hand_count,
            'analysis_date': row.analysis_date
        }
        for row in bq_client.query(query).result()
    }

    # 3. 데이터 조합
    videos = []
    for blob in blobs:
        video_path = f"gs://{bucket}/{blob.name}"
        analyzed = analyzed_videos.get(video_path)

        videos.append(VideoItem(
            video_id=blob.name.split('/')[-1],
            gcs_path=video_path,
            file_size_mb=round(blob.size / (1024*1024), 2),
            upload_date=blob.time_created,
            analysis_status='completed' if analyzed else 'pending',
            analysis_date=analyzed['analysis_date'] if analyzed else None,
            hand_count=analyzed['hand_count'] if analyzed else 0,
            metadata_available=bool(analyzed)
        ))

    return VideoListResponse(
        total=len(videos),
        videos=videos,
        next_page_token=blobs.next_page_token
    )
```

#### 10.3.2 재분석 트리거 API

**엔드포인트**: `POST /api/videos/{video_id}/reanalyze`

```python
@router.post("/api/videos/{video_id}/reanalyze")
async def trigger_reanalysis(video_id: str):
    """영상 재분석 요청 (qwen_hand_analysis 파이프라인 트리거)"""

    # 1. qwen_hand_analysis 큐에 작업 추가
    # 또는 GCS Pub/Sub 메시지 발행

    # 2. 분석 상태 업데이트
    # 예: Firestore에 status = 'processing' 기록

    return {
        "message": "재분석 요청이 접수되었습니다",
        "video_id": video_id,
        "status": "processing"
    }
```

### 10.4 통합 시나리오

**시나리오 1: 새 영상 업로드 후 모니터링**
```
1. 사용자가 GCS에 영상 업로드
2. 관리자가 대시보드 접속
3. "대기 중" 필터로 미분석 영상 확인
4. qwen_hand_analysis 자동 트리거 (또는 수동 트리거)
5. 분석 진행 상황 실시간 모니터링
6. 분석 완료 시 "완료" 상태로 자동 업데이트
7. archive-mam 검색에서 즉시 사용 가능
```

**시나리오 2: 실패한 영상 재분석**
```
1. 대시보드에서 "실패" 상태 영상 확인
2. 오류 메시지 확인 (예: "Video format not supported")
3. 영상 포맷 변환 후 재업로드
4. "재분석 요청" 버튼 클릭
5. qwen_hand_analysis 파이프라인 재실행
6. 성공 시 "완료"로 상태 변경
```

### 10.5 기술 스택

**백엔드**:
- FastAPI (Python 3.11)
- Google Cloud Storage Client Library
- Google Cloud BigQuery Client Library

**프론트엔드**:
- Next.js 16 App Router
- React 19
- shadcn/ui Table, Badge, Select 컴포넌트
- TanStack Table (정렬, 필터링, 페이지네이션)

**데이터 동기화**:
- GCS Pub/Sub (영상 업로드 이벤트)
- Cloud Scheduler (주기적 상태 동기화, 예: 1시간마다)

### 10.6 성능 요구사항

- **리스트 조회**: 100개 영상 기준 <2초
- **상태 확인**: BigQuery 조인 최적화 (인덱스 활용)
- **실시간성**: 5분 내 상태 업데이트 반영
- **페이지네이션**: 50개 단위 (GCS API 제한 고려)

### 10.7 보안 및 권한

- **접근 제어**: 관리자 전용 (RBAC)
- **GCS 권한**: `storage.objects.list`, `storage.objects.get`
- **BigQuery 권한**: `bigquery.jobs.create`, `bigquery.tables.get`

---

## 11. 단계별 구축 계획 (업데이트)

### Phase 1 – 코어 MVP (✅ 완료)

* ~~PostgreSQL 스키마 구축~~ → **BigQuery 스키마 구축** (완료)
* ~~ATI 분석 결과 → PostgreSQL 적재~~ → **qwen_hand_analysis → BigQuery ETL** (완료)
* ~~Typesense 설치~~ → **Vertex AI Vector Search** (완료)
* `/api/search` API 구현 (완료)
* Next.js 16 기반 검색 UI + 비디오 플레이어 (완료)

### Phase 2 – 클립/리액션 확장 (일부 완료)

* `clips`, `actions` 테이블 및 인덱스 구축
* `/api/searchClips` 추가
* 리액션/감정 태그 기반 검색 기능 추가
* Query Rewrite 룰 확장(버블, FT, 3bet pot 등)

### Phase 3 – Video Archive Management UI (🚧 진행 중)

* **GCS 버킷 영상 리스트 조회 API** (신규)
* **분석 상태 확인 대시보드 UI** (신규)
* **재분석 트리거 기능** (신규)
* 영상 업로드 UI (선택)
* 분석 진행 상황 실시간 모니터링 (WebSocket, 선택)

### Phase 4 – 시멘틱 검색/추천

* 텍스트 임베딩(Embedding, 문장 벡터) 도입 → **Vertex AI TextEmbedding-004 사용 중**
* ~~PostgreSQL + pgvector~~ → **Vertex AI Vector Search 활용** (완료)
* "비슷한 핸드 추천", "이 핸드와 유사한 상황" 기능 추가
* RAG 기반 자연어 답변 (Qwen3-8B) - 완료

---

## 12. 요약 (업데이트)

* 외부 MAM 솔루션 **전혀 사용하지 않고**,
* **qwen_hand_analysis(Gemini AI 분석) + GCS + Vertex AI Vector Search + BigQuery + Next.js 16** 만으로
* **자연어 기반 포커 아카이브 검색 시스템**을 구축
* **Phase 3**에서 **GCS 영상 관리 대시보드** 추가:
  - 영상 자산 가시성 확보
  - 분석 진행 상태 실시간 추적
  - 미분석 영상 관리 및 재분석 트리거

### 주요 변경사항 (v1.0 → v2.0)

**아키텍처**:
- PostgreSQL → **BigQuery** (확장성, GCP 네이티브)
- Typesense → **Vertex AI Vector Search** (하이브리드 검색, Auto-scaling)
- ATI 자체 분석 → **qwen_hand_analysis (Gemini 2.5 Flash)** (정확도 향상)

**신규 기능**:
- RAG 기반 자연어 답변 (Qwen3-8B via Ollama)
- GCS 영상 관리 대시보드 (Phase 3)
- 실시간 분석 상태 모니터링
- 재분석 트리거 기능

**기술 스택**:
- Frontend: React/Ant Design → **Next.js 16 + React 19 + shadcn/ui**
- Backend: Node.js → **FastAPI (Python 3.11)**
- Search: Typesense → **Vertex AI Vector Search**
- Database: PostgreSQL → **BigQuery**
- LLM: 없음 → **Qwen3-8B (RAG)**

---

**문서 버전**: v2.0
**최종 업데이트**: 2025-11-20
**변경사항**: GCS 영상 관리 대시보드 기능 추가 (Section 10)

