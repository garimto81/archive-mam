개발팀, 데이터 엔지니어, 그리고 AI 엔지니어에게 즉시 전달하여 프로젝트를 착수할 수 있도록, \*\*GG PRODUCTION MAM (Code: The Nuts)\*\*의 최종 확정된 PRD(제품 요구사항 정의서)를 작성해 드립니다.

이 문서는 지금까지 논의된 모든 요구사항(포커 특화 로직, 하이브리드 검색, 태그 정제, 자동 클리핑 등)을 기술적으로 구체화한 **Master Specification**입니다.

-----

# Product Requirements Document (PRD)

## Project: GG PRODUCTION MAM - "The Nuts"

| 문서 정보 | 상세 내용 |
| :--- | :--- |
| **프로젝트명** | **GG PRODUCTION MAM** (Code Name: **The Nuts**) |
| **버전** | **v2.0 (Final Development Spec)** |
| **작성일** | 2025-11-19 |
| **작성자** | Global Production Lead & Tech Architect |
| **목표** | WSOP 아카이브의 **포커 핸드 단위 데이터화**, **의미/논리 복합 검색**, **초고속 자동 클리핑** 시스템 구축 |

-----

## 1\. 개요 (Executive Summary)

본 프로젝트는 단순한 영상 보관소가 아니다. 수십 년간 축적된 WSOP 포커 영상에서 \*\*"게임의 데이터(Game Logic)"\*\*와 \*\*"드라마(Narrative)"\*\*를 추출하여, 검색 즉시 편집 및 2차 가공이 가능한 **Intelligent Production Pipeline**을 구축하는 것을 목표로 한다.

### 핵심 목표

1.  **Deep Poker Understanding:** 영상 내 카드를 OCR로 인식하고, 베팅 액션을 분석하여 구조화된 데이터(JSON)로 변환.
2.  **Smart Hybrid Search:** "블러핑(Semantic)"과 "A♠K♠ 핸드(Logic)"를 동시에 검색하며, 오타/별명("pil") 입력 시 표준 태그("Phil Hellmuth")로 자동 보정.
3.  **Zero-Wait Production:** 검색 결과에서 원본 다운로드 없이 즉시 **구간 미리보기** 및 **무손실 고속 클리핑(Stream Copy)** 지원.

-----

## 2\. 시스템 아키텍처 (System Architecture)

Google Cloud Native 환경에서 **Event-Driven Serverless** 구조로 설계하여 확장성과 비용 효율성을 확보한다.

### 2.1. 데이터 파이프라인 흐름

1.  **Ingest:** `User` → **GCS (Raw Bucket)** 업로드 (Resumable Upload).
2.  **Trigger:** `Object Finalize` 이벤트 → **Cloud Functions** 실행.
3.  **Processing (Parallel):**
      * **Transcoding:** `Media API` → 미리보기용 `HLS(.m3u8)` 및 `Proxy(.mp4)` 생성.
      * **AI Analysis:** `Vertex AI (Gemini 1.5 Pro)` → 포커 룰 기반 프레임 분석 → **JSON Extraction**.
4.  **Storage (Dual Store):**
      * **Firestore:** 영상 메타데이터, 핸드 로직, 엔티티(선수) 정보 저장.
      * **Vertex AI Vector Search:** 상황 요약문, 감정 태그의 임베딩 벡터 저장.
5.  **Service:** `Cloud Run (Backend)` + `Next.js (Frontend)`.
6.  **Delivery:** `FFmpeg (Cloud Run)` → GCS 원본 **Stream Copy** → 사용자 다운로드.

-----

## 3\. 상세 기능 요구사항 (Functional Specifications)

### 3.1. 포커 인텔리전스 (AI Analysis)

Gemini 1.5 Pro의 멀티모달 기능을 활용하여 비정형 영상을 정형 데이터로 변환한다.

  * **Card Recognition:** 화면의 Hole Cards와 Board Cards를 인식하여 표준 표기법(`Rank+Suit`, 예: `As`, `Td`)으로 변환.
  * **Game Context:** 현재 스트리트(Flop/Turn/River), 팟 사이즈, 블라인드 레벨, 올인 여부 자동 추출.
  * **Timeline Segmentation:** 핸드의 시작(Pre-flop)부터 끝(Showdown/Fold)까지 정확한 타임코드(`start_ms`, `end_ms`) 기록.

### 3.2. 지능형 검색 (Smart Search UX)

  * **Entity Tagging (Autocomplete):**
      * 사용자가 `pil`, `poker brat` 입력 시 → `entities` 컬렉션 조회 → **"Phil Hellmuth"** 태그 추천 및 선택 유도.
  * **Hybrid Search Logic:**
      * **Query:** `Tag: Phil Hellmuth` + `Text: "Bluffing"` + `Filter: Hand Pair: AA`
      * **Execution:** (Vector Search for "Bluffing") ∩ (Firestore Filter for `entity_id` & `hole_cards`)
  * **Visual Card Selector:** 텍스트 입력 없이 GUI에서 `[A♠]`, `[A♣]`를 클릭하여 해당 핸드 필터링.

### 3.3. 자동화된 프로덕션 (Automated Production)

  * **Instant Preview:** 검색 결과 클릭 시, 전체 영상이 아닌 **해당 핸드 구간만** HLS 스트리밍으로 즉시 재생.
  * **Lossless Clipping:** "다운로드" 요청 시, FFmpeg `-c copy` 옵션을 사용하여 재인코딩 없이 5초 이내에 원본 화질 클립 생성.
  * **Shorts Metadata:** AI가 분석한 \*\*"Hero Face 좌표"\*\*와 \*\*"Board Card 좌표"\*\*를 제공하여, 추후 자동 9:16 크롭 기능 지원.

-----

## 4\. 데이터 스키마 (Database Schema) - **Critical**

**Firestore** NoSQL 설계를 기준으로 하며, 개발팀은 아래 스키마를 엄격히 준수해야 한다.

### 4.1. Collection: `hands` (검색 및 분석의 핵심 단위)

  * **Document ID:** `h_{video_id}_{start_timestamp}`
  * **Note:** 논리적 필터링(`players`, `game_logic`)과 미디어 참조(`media_refs`)가 통합된 구조.

<!-- end list -->

```json
{
  "hand_id": "h_wsop24_ev1_17150020",
  "video_ref_id": "wsop24_ev1_part1",
  
  // [1. Media & Clipping Source] - 즉시 재생/다운로드용
  "media_refs": {
    "master_gcs_uri": "gs://wsop-raw/2024/ev1/part1.mxf", 
    "time_range": {
      "start_seconds": 1420.500, // 소수점 3자리(ms) 필수
      "end_seconds": 1580.250,
      "duration_seconds": 159.750
    }
  },

  // [2. Game Logic Data] - 필터 검색용
  "game_logic": {
    "stage": "Final Table", 
    "is_showdown": true,
    "winning_hand_rank": "Full House", // Enum
    "pot_final": 25000000,
    // 보드 카드 (커뮤니티 카드) - 표준 표기법 준수
    "board": {
      "flop": ["As", "Td", "2h"], 
      "turn": ["Kh"],
      "river": ["2c"]
    }
  },

  // [3. Players Data] - 선수별 필터링용
  "players": [
    {
      "entity_id": "player_phil_hellmuth", // entities 컬렉션 참조 ID
      "display_name": "Phil Hellmuth",
      "position": "BTN",
      "hole_cards": ["Ah", "Ac"], // Pocket Aces
      "hand_strength_final": 0.98, 
      "is_winner": false,
      "is_aggressor": true
    },
    {
      "entity_id": "player_unknown_01",
      "display_name": "New Kid",
      "position": "BB",
      "hole_cards": ["7d", "2s"],
      "is_winner": true
    }
  ],

  // [4. Semantic Analysis] - 벡터 검색용
  "semantics": {
    "summary_text": "Phil Hellmuth traps with Pocket Aces but gets cracked by 7-2 offsuit. Hellmuth goes on a massive tilt.",
    "mood_tags": ["Tilt", "Bad Beat", "High Tension"], 
    "vector_embedding": [0.015, -0.221, ...] // Vertex AI Embedding 값
  }
}
```

### 4.2. Collection: `entities` (태그 정제 및 자동완성용)

  * **Document ID:** `entity_id` (예: `player_phil_hellmuth`)
  * **Role:** 오타, 별명, 부분 일치 검색어를 표준 ID로 매핑하는 사전(Dictionary).

<!-- end list -->

```json
{
  "entity_id": "player_phil_hellmuth",
  "type": "PLAYER", 
  "canonical_name": "Phil Hellmuth", // UI 표시 표준 이름
  
  // [검색 키워드 인덱스] - Fuzzy Search 대상
  "search_keywords": [
    "phil hellmuth", 
    "phil helmuth", // 오타
    "pil",          // Prefix
    "poker brat",   // 별명
    "17 bracelets"
  ],
  
  "metadata": {
    "nationality": "USA",
    "total_winnings": 29000000
  },
  "avatar_url": "gs://assets/players/hellmuth.jpg"
}
```

### 4.3. Collection: `videos` (파일 자산 관리)

  * **Document ID:** `video_id` (예: `wsop24_ev1_part1`)

<!-- end list -->

```json
{
  "video_id": "wsop24_ev1_part1",
  "title": "2024 WSOP Event #1 - Part 1",
  "gcs_paths": {
    "raw": "gs://wsop-raw/2024/ev1/part1.mxf",
    "hls": "gs://wsop-proxy/2024/ev1/part1/playlist.m3u8"
  },
  "metadata": {
    "fps": 29.97, 
    "duration_frames": 450000
  },
  "status": "READY"
}
```

-----

## 5\. UI/UX 가이드라인 (Frontend)

### 5.1. Dashboard Layout

  * **Framework:** React (Next.js) + **Mantine UI** (Dark Mode).
  * **3-Column Structure:**
    1.  **Left (Filter):** 태그 검색창(Autocomplete), 카드 선택기(Grid UI), 게임 스테이지 필터.
    2.  **Center (Player):** 메인 비디오 플레이어, 타임라인(이벤트 마커 표시).
    3.  **Right (Result List):** 검색된 핸드 리스트 (썸네일 + 요약 텍스트).

### 5.2. Search Interaction Flow

1.  사용자가 검색창에 `pil` 입력.
2.  드롭다운에 **"Phil Hellmuth (Player)"** 추천 표시.
3.  사용자가 클릭 시 `Tag: Phil Hellmuth` 칩 생성.
4.  추가로 `Bluffing` 입력 (텍스트 검색).
5.  결과 리스트에 "Phil Hellmuth가 블러핑하는 핸드"만 필터링되어 표시.

### 5.3. Instant Download Flow

1.  결과 리스트에서 핸드 선택.
2.  플레이어 하단 **[Clip Download]** 버튼 클릭.
3.  "Processing..." (약 3\~5초 소요).
4.  `mp4` 파일 다운로드 시작 (파일명: `hand_{id}_{player_names}.mp4`).

-----

## 6\. 비기능 요구사항 (Non-Functional Requirements)

  * **Performance:**
      * 검색 결과 반환 속도: **200ms 이내**.
      * 클리핑(5분 길이 기준) 생성 속도: **10초 이내**.
  * **Cost Optimization:**
      * GCS Lifecycle 정책 적용: 업로드 30일 후 `Standard` → `Coldline` 자동 전환 (Raw 파일).
      * Vector Search: 쿼리 빈도에 따른 스케일링 정책 적용.
  * **Security:**
      * 모든 비디오 URL은 **Signed URL**로 제공하여 외부 무단 접근 차단.

