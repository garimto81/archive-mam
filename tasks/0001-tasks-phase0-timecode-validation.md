# Task List: Phase 0 - 타임코드 검증 시스템 (PRD-0001)

**PRD**: prd_recommended.md Phase 0
**Duration**: 3개월 (12주)
**Goal**: ATI 데이터와 NAS 영상의 타임코드 100% 동기화 보장
**Success Criteria**: 1,000개 샘플 핸드 중 95% 이상 자동 매칭

---

## Task 0.0: Setup

**Duration**: Week 1 (5일)

- [ ] 0.0.1: Create feature branch: `feature/PRD-0001-phase0-timecode-validation`
- [ ] 0.0.2: GCP 프로젝트 생성 및 기본 설정
  - IAM 권한 설정 (개발팀 접근)
  - Billing 계정 연결
  - Secret Manager 활성화
- [ ] 0.0.3: NSUS ATI 팀과 킥오프 미팅
  - 데이터 스키마 최종 확인
  - 샘플 데이터 1,000개 요청
  - 타임스탬프 포맷 협의
- [ ] 0.0.4: NAS 서버 접근 권한 획득
  - VPN 설정
  - SMB/NFS 마운트 테스트
  - 샘플 영상 파일 10개 다운로드
- [ ] 0.0.5: 개발 환경 세팅
  - Python 3.11 venv
  - 필수 라이브러리: `ffmpeg-python`, `google-cloud-storage`, `google-cloud-vision`
  - Git pre-commit hook 설정

---

## Task 1.0: Phase 0 - 데이터 수집 및 분석

**Duration**: Week 2-3 (10일)

### 1.1 ATI 샘플 데이터 수집

- [ ] 1.1.1: NSUS ATI 팀으로부터 1,000개 핸드 샘플 데이터 수신
  - Format: JSON 또는 CSV
  - 필수 필드: `hand_id`, `event_name`, `timestamp_start_utc`, `timestamp_end_utc`, `video_file_name`
- [ ] 1.1.2: BigQuery 테이블 생성: `dev.ati_sample_hands`
  ```sql
  CREATE TABLE dev.ati_sample_hands (
    hand_id STRING NOT NULL,
    event_name STRING,
    timestamp_start_utc TIMESTAMP,
    timestamp_end_utc TIMESTAMP,
    duration_seconds FLOAT64,
    video_file_name STRING,
    players ARRAY<STRING>,
    pot_size NUMERIC
  );
  ```
- [ ] 1.1.3: 샘플 데이터 BigQuery에 로드
- [ ] 1.1.4: **테스트**: `tests/test_ati_data_loader.py` 작성 (1:1 pair with 1.1.3)
  - 1,000개 row 로드 검증
  - 필수 필드 null 체크
  - 타임스탬프 포맷 검증

**Acceptance Criteria**:
- ✅ 1,000개 핸드 데이터가 BigQuery에 정상 로드됨
- ✅ 모든 필수 필드가 채워져 있음
- ✅ `timestamp_end > timestamp_start` 검증 통과

---

### 1.2 NAS 영상 파일 매핑

- [ ] 1.2.1: NAS 영상 파일 목록 스캔 스크립트 작성: `src/nas_scanner.py`
  - 디렉토리: `/nas/poker/2024/wsop/`
  - 파일 포맷: `.mp4`, `.mov`
  - 메타데이터 추출: 파일명, 크기, 생성일, 길이(초)
- [ ] 1.2.2: **테스트**: `tests/test_nas_scanner.py` (1:1 pair)
  - Mock NAS 디렉토리로 스캔 테스트
  - 파일명 파싱 검증
- [ ] 1.2.3: NAS 파일 메타데이터를 BigQuery에 저장: `dev.nas_video_files`
  ```sql
  CREATE TABLE dev.nas_video_files (
    file_path STRING NOT NULL,
    file_name STRING,
    size_bytes INT64,
    duration_seconds FLOAT64,
    created_at TIMESTAMP
  );
  ```
- [ ] 1.2.4: **테스트**: `tests/test_nas_to_bigquery.py` (1:1 pair)

**Acceptance Criteria**:
- ✅ NAS의 모든 영상 파일이 BigQuery에 매핑됨
- ✅ 파일 길이(초) 정보가 정확함

---

### 1.3 초기 매칭 로직 구현

- [ ] 1.3.1: ATI `video_file_name` ↔ NAS `file_path` 매칭 스크립트: `src/matcher.py`
  ```python
  def match_hand_to_video(hand: Hand) -> Optional[str]:
      """ATI 핸드 데이터를 NAS 영상 파일과 매칭"""
      # Example: hand.video_file_name = "wsop2024_me_day3"
      # NAS file: /nas/poker/2024/wsop/main_event_day3.mp4
      pass
  ```
- [ ] 1.3.2: **테스트**: `tests/test_matcher.py` (1:1 pair)
  - 정확한 매칭 케이스 10개
  - 모호한 케이스 5개
  - 매칭 실패 케이스 3개
- [ ] 1.3.3: 매칭 결과를 BigQuery에 저장: `dev.hand_video_mapping`
  ```sql
  CREATE TABLE dev.hand_video_mapping (
    hand_id STRING NOT NULL,
    nas_file_path STRING,
    match_confidence FLOAT64,  -- 0.0 ~ 1.0
    match_method STRING  -- "exact", "fuzzy", "manual"
  );
  ```

**Acceptance Criteria**:
- ✅ 1,000개 핸드 중 최소 80%가 `match_confidence > 0.8`
- ✅ 나머지 20%는 수동 매칭 대상으로 플래그

---

## Task 2.0: Phase 0 - 타임코드 검증 엔진

**Duration**: Week 4-7 (20일)

### 2.1 FFmpeg 타임코드 추출

- [ ] 2.1.1: FFmpeg 래퍼 클래스 구현: `src/ffmpeg_utils.py`
  ```python
  class FFmpegUtils:
      def extract_frame(self, video_path: str, timestamp_sec: float) -> bytes:
          """특정 타임스탬프의 프레임을 JPG로 추출"""
          pass

      def extract_subclip(self, video_path: str, start_sec: float,
                          end_sec: float) -> str:
          """서브클립 생성 및 임시 파일 경로 반환"""
          pass
  ```
- [ ] 2.1.2: **테스트**: `tests/test_ffmpeg_utils.py` (1:1 pair)
  - 샘플 영상으로 프레임 추출 테스트
  - 서브클립 생성 및 길이 검증
  - Edge case: 파일 없음, 잘못된 타임스탬프

**Acceptance Criteria**:
- ✅ 프레임 추출 성공률 100% (유효한 입력 기준)
- ✅ 서브클립 길이 오차 < 0.5초

---

### 2.2 Vision AI 검증 시스템

- [ ] 2.2.1: Vision AI 통합: `src/vision_validator.py`
  ```python
  class VisionValidator:
      def validate_poker_scene(self, frame_jpg: bytes) -> dict:
          """
          프레임이 포커 장면인지 검증
          Returns:
              {
                  "is_poker": bool,
                  "confidence": float,
                  "detected_objects": ["table", "cards", "chips", "players"],
                  "player_count": int
              }
          """
          # Google Vision API: Object Detection
          # 기대 객체: "table", "playing card", "poker chip", "person"
          pass
  ```
- [ ] 2.2.2: **테스트**: `tests/test_vision_validator.py` (1:1 pair)
  - 실제 포커 장면 10개 → `is_poker=True` 검증
  - 비포커 장면 10개 (광고, 인터뷰) → `is_poker=False` 검증
- [ ] 2.2.3: 검증 결과를 BigQuery에 저장: `dev.timecode_validation_results`
  ```sql
  CREATE TABLE dev.timecode_validation_results (
    hand_id STRING NOT NULL,
    check_timestamp TIMESTAMP,
    extracted_frame_gcs STRING,  -- gs://dev-frames/hand_123.jpg
    is_poker_scene BOOL,
    confidence FLOAT64,
    detected_objects ARRAY<STRING>,
    validation_status STRING  -- "PASS", "FAIL", "REVIEW"
  );
  ```

**Acceptance Criteria**:
- ✅ Vision API 정확도 > 90% (포커 장면 vs 비포커 장면)
- ✅ API 호출 비용 < $100 (1,000개 샘플 기준)

---

### 2.3 타임코드 동기화 점수 계산

- [ ] 2.3.1: 동기화 점수 알고리즘 구현: `src/sync_scorer.py`
  ```python
  def calculate_sync_score(hand: Hand, validation_result: dict) -> float:
      """
      타임코드 동기화 점수 계산 (0-100)

      Factors:
      - Vision API confidence (50%)
      - 핸드 길이 vs 영상 클립 길이 차이 (30%)
      - 예상 플레이어 수 vs 감지된 플레이어 수 (20%)
      """
      score = 0.0

      # Vision confidence
      if validation_result['is_poker']:
          score += validation_result['confidence'] * 50

      # Duration match
      expected_duration = hand.timestamp_end - hand.timestamp_start
      actual_duration = get_clip_duration(...)
      duration_diff = abs(expected_duration - actual_duration)
      if duration_diff < 5:  # 5초 이내
          score += 30
      elif duration_diff < 10:
          score += 15

      # Player count (if available)
      if 'player_count' in validation_result:
          expected_players = len(hand.players)
          if abs(expected_players - validation_result['player_count']) <= 1:
              score += 20

      return score
  ```
- [ ] 2.3.2: **테스트**: `tests/test_sync_scorer.py` (1:1 pair)
  - Perfect match 케이스 → score = 100
  - Good match 케이스 → score > 80
  - Poor match 케이스 → score < 50

**Acceptance Criteria**:
- ✅ 1,000개 샘플 중 95% 이상이 score > 80
- ✅ score < 50인 케이스는 수동 검토 대상

---

### 2.4 Offset 자동 계산

- [ ] 2.4.1: Offset 계산 로직 구현: `src/offset_calculator.py`
  ```python
  def calculate_offset(hand: Hand, video_path: str) -> Optional[float]:
      """
      타임코드 불일치 시 Offset 자동 계산

      Strategy:
      1. 예상 구간 ±30초 범위에서 5초 간격으로 샘플링
      2. 각 샘플을 Vision API로 검증
      3. 가장 높은 confidence를 보이는 구간의 offset 반환
      """
      best_offset = None
      best_confidence = 0.0

      for offset in range(-30, 31, 5):  # -30 ~ +30초
          adjusted_start = hand.timestamp_start + offset
          frame = extract_frame(video_path, adjusted_start)
          result = vision_validate(frame)

          if result['confidence'] > best_confidence:
              best_confidence = result['confidence']
              best_offset = offset

      if best_confidence > 0.8:
          return best_offset
      else:
          return None  # 자동 계산 실패 → 수동 매칭 필요
  ```
- [ ] 2.4.2: **테스트**: `tests/test_offset_calculator.py` (1:1 pair)
  - 인위적으로 +10초 offset 적용한 샘플 → offset = 10 검출
  - 랜덤 offset 10개 케이스 → 정확도 검증
- [ ] 2.4.3: Offset을 BigQuery에 저장: `dev.hand_timecode_offsets`
  ```sql
  CREATE TABLE dev.hand_timecode_offsets (
    hand_id STRING NOT NULL,
    calculated_offset_seconds FLOAT64,
    confidence FLOAT64,
    calculation_method STRING  -- "auto", "manual"
  );
  ```

**Acceptance Criteria**:
- ✅ Offset 자동 계산 성공률 > 70% (score < 80인 케이스 중)
- ✅ 계산된 offset 적용 후 score > 90

---

## Task 3.0: Phase 0 - 수동 매칭 UI

**Duration**: Week 8-10 (15일)

### 3.1 Web UI 기본 구조

- [ ] 3.1.1: Flask 앱 초기화: `src/web/app.py`
  - Cloud Run 배포 설정
  - IAP 인증 통합
  - BigQuery 클라이언트 초기화
- [ ] 3.1.2: **테스트**: `tests/test_web_app.py` (1:1 pair)
  - Health check endpoint: `/health`
  - Auth 테스트 (Mock IAP)
- [ ] 3.1.3: 배포: Cloud Run (dev 환경)
  ```bash
  gcloud run deploy timecode-validator-dev \
    --source . \
    --region us-central1 \
    --allow-unauthenticated  # 나중에 IAP 설정
  ```

**Acceptance Criteria**:
- ✅ Cloud Run URL 접근 가능
- ✅ `/health` → 200 OK

---

### 3.2 수동 매칭 인터페이스

- [ ] 3.2.1: 매칭 대기 목록 페이지: `src/web/templates/review_queue.html`
  - BigQuery에서 `sync_score < 80`인 핸드 목록 조회
  - 각 핸드의 예상 구간 영상 미리보기
  - [Accept] [Adjust Offset] [Report Issue] 버튼
- [ ] 3.2.2: Offset 조정 UI: `src/web/templates/adjust_offset.html`
  ```html
  <video id="player" src="..."></video>
  <input type="range" min="-60" max="60" step="1" id="offset-slider">
  <span id="current-offset">0</span> seconds

  <script>
    // Slider 변경 시 영상 재생 위치 조정
    // 사용자가 정확한 시작점을 찾을 때까지 반복
  </script>

  <button onclick="saveOffset()">Save Offset</button>
  ```
- [ ] 3.2.3: Offset 저장 API: `POST /api/v1/save-offset`
  ```python
  @app.route('/api/v1/save-offset', methods=['POST'])
  def save_offset():
      hand_id = request.json['hand_id']
      offset = request.json['offset']  # seconds
      reviewer = request.json['reviewer_email']

      # BigQuery에 저장
      query = f"""
      INSERT INTO dev.hand_timecode_offsets
      VALUES ('{hand_id}', {offset}, 1.0, 'manual')
      """
      client.query(query)

      return {"status": "ok"}
  ```
- [ ] 3.2.4: **테스트**: `tests/test_manual_matching.py` (1:1 pair)
  - UI 로드 테스트
  - Offset 저장 API 테스트

**Acceptance Criteria**:
- ✅ 수동 매칭 UI에서 영상 재생 가능
- ✅ Offset 조정 후 저장 → BigQuery 반영

---

### 3.3 검토 워크플로우

- [ ] 3.3.1: 리뷰어 할당 시스템
  - 매칭 실패 핸드를 팀원에게 자동 할당
  - Slack 알림: "10개 핸드가 수동 매칭 대기 중입니다"
- [ ] 3.3.2: 진행률 대시보드: `src/web/templates/dashboard.html`
  ```html
  <h2>Phase 0 Progress</h2>
  <p>Total Hands: 1,000</p>
  <p>Auto Matched (score > 80): <strong>950 (95%)</strong></p>
  <p>Manual Review Pending: <strong>30 (3%)</strong></p>
  <p>Completed: <strong>20 (2%)</strong></p>

  <div class="progress-bar">
    <div style="width: 97%">97% Complete</div>
  </div>
  ```
- [ ] 3.3.3: **테스트**: `tests/test_review_workflow.py` (1:1 pair)

**Acceptance Criteria**:
- ✅ 대시보드에서 실시간 진행률 확인 가능
- ✅ 팀원 3명이 수동 매칭 완료

---

## Task 4.0: Phase 0 - 품질 검증 및 리포트

**Duration**: Week 11-12 (10일)

### 4.1 최종 검증

- [ ] 4.1.1: 1,000개 핸드 전체 재검증 스크립트: `src/final_validator.py`
  ```python
  def final_validation():
      """
      모든 핸드에 대해:
      1. Offset 적용 (있는 경우)
      2. 타임코드로 서브클립 생성
      3. Vision AI 재검증
      4. 최종 점수 계산
      """
      for hand in get_all_hands():
          offset = get_offset(hand.id) or 0
          adjusted_start = hand.timestamp_start + offset
          adjusted_end = hand.timestamp_end + offset

          clip = create_subclip(hand.nas_path, adjusted_start, adjusted_end)
          result = vision_validate(clip)
          final_score = calculate_final_score(result)

          save_final_result(hand.id, final_score, result)
  ```
- [ ] 4.1.2: **테스트**: `tests/test_final_validator.py` (1:1 pair)
- [ ] 4.1.3: 최종 결과 BigQuery 저장: `dev.phase0_final_results`

**Acceptance Criteria**:
- ✅ 1,000개 핸드 중 **95% 이상이 final_score > 90**
- ✅ 나머지 5%는 이슈 리포트 작성

---

### 4.2 Phase 0 리포트 작성

- [ ] 4.2.1: 데이터 분석 및 시각화: Looker Studio 대시보드
  - 동기화 성공률 (by event, by day)
  - Offset 분포 히스토그램
  - Vision AI confidence 분포
- [ ] 4.2.2: Phase 0 완료 리포트 작성: `docs/phase0_report.md`
  ```markdown
  # Phase 0 완료 리포트

  ## 요약
  - 총 핸드: 1,000개
  - 자동 매칭: 950개 (95%)
  - 수동 매칭: 50개 (5%)
  - 최종 성공률: **98%** (final_score > 90)

  ## 발견된 이슈
  1. ATI 타임스탬프가 UTC인데 NAS 영상은 PST → 8시간 offset
  2. 일부 이벤트에서 프리플랍 구간이 누락됨
  3. ...

  ## 권장사항
  - Phase 1에서 자동 Offset 적용 로직 추가
  - ATI 팀과 타임존 표준화 협의
  ```
- [ ] 4.2.3: 경영진 보고: Go/No-Go 결정 회의
  - Phase 1 진행 여부 결정
  - 예산 최종 승인 요청

**Acceptance Criteria**:
- ✅ 98% 동기화 성공률 → **Phase 1 Go** 결정
- ✅ < 95% → No-Go, 추가 개선 필요

---

## Task 5.0: Phase 1 준비

**Duration**: Week 12 (5일)

- [ ] 5.0.1: Phase 0 코드 정리 및 문서화
  - README.md 업데이트
  - API 문서 작성
  - 코드 리뷰 완료
- [ ] 5.0.2: Production 환경 설정
  - GCP Project: `gg-poker-brain-prod`
  - BigQuery dataset: `prod.*`
  - Cloud Run: production 배포
- [ ] 5.0.3: Phase 1 PRD 상세화
  - Epic 1.1, 1.2, 1.3의 Task List 생성
- [ ] 5.0.4: Phase 1 팀 확대
  - Backend 개발자 1명 추가
  - QA 엔지니어 할당

---

## 리소스 및 의존성

### 팀

| 역할 | 인원 | 주요 업무 |
|------|------|----------|
| Tech Lead | 1명 | 아키텍처, 코드 리뷰 |
| Backend Dev | 1명 | Python, FFmpeg, Vision AI |
| Data Engineer | 0.5명 | BigQuery, ETL |
| QA | 0.5명 | 테스트, 검증 |

### 예산 (3개월)

| 항목 | 비용 |
|------|------|
| GCP (BigQuery, Vision API, Cloud Run) | $2,000 |
| 인건비 (2.5명 × $10K/월) | $75,000 |
| 총합 | **$77,000** |

### 외부 의존성

- ✅ NSUS ATI 팀: 샘플 데이터 제공 (Week 2)
- ✅ IT 팀: NAS 접근 권한 (Week 1)
- ✅ GCP Admin: Project 생성 및 권한 (Week 1)

---

## 리스크 및 완화 전략

| 리스크 | 영향 | 확률 | 완화 전략 |
|--------|------|------|----------|
| **ATI 데이터 지연** | 🔴 High | 30% | Week 2까지 미수신 시 더미 데이터로 우선 개발 |
| **Vision API 정확도 낮음** | 🟡 Medium | 20% | Fallback: 수동 매칭 비율 증가 허용 (5% → 10%) |
| **NAS 네트워크 불안정** | 🟡 Medium | 15% | 샘플 영상 GCS에 백업 |
| **타임존 불일치** | 🟢 Low | 40% | Week 3에 발견 → 자동 Offset 로직으로 해결 |

---

## 다음 단계

Phase 0 완료 후:
1. ✅ **Go 결정** → Phase 1 Task List 생성 및 구현 시작
2. ❌ **No-Go 결정** → Phase 0 개선 사이클 반복

---

**마지막 업데이트**: 2025-11-17
**상태**: Ready for Review
