# Week 1-9 상세 타임라인

**프로젝트**: POKER-BRAIN (WSOP Archive System)
**기간**: 9주
**목표**: Production 배포
**작성일**: 2025-11-17

---

## Week 1: API 설계 및 킥오프

### 목표
- OpenAPI 스펙 확정
- 개발 환경 설정
- Mock API 구축

### 일정

#### Day 1 (월요일)
- ✅ 킥오프 미팅 (전체 팀, 10:00-12:00)
  - 프로젝트 소개
  - 팀 역할 분담
  - 타임라인 공유
- Alice (M1): OpenAPI 스펙 작성
- Bob (M2): OpenAPI 스펙 작성
- Charlie (M3): OpenAPI 스펙 작성
- David (M4): OpenAPI 스펙 작성
- Eve (M5): OpenAPI 스펙 작성
- Frank (M6): OpenAPI 스펙 작성

#### Day 2-3 (화-수)
- 전체: OpenAPI 스펙 작성 계속
- PM: 스펙 리뷰 준비

#### Day 4 (목요일)
- ✅ PM API 스펙 리뷰 (14:00-17:00)
  - 6개 스펙 발표 (각 20분)
  - 일관성 검증
  - Breaking Change 확인
  - 피드백 정리

#### Day 5 (금요일)
- 전체: 피드백 반영
- PM: Mock API 서버 구축 (Prism)
- ✅ Week 1 Review (16:00-17:00)
  - 진행률: 100%
  - 다음 주 계획: Mock API 완성, 개발 환경 설정

---

## Week 2: Mock API 완성 및 개발 준비

### 목표
- Mock API 서버 완성
- 개발 환경 설정 완료
- BigQuery 테이블 생성

### 일정

#### Day 1-2 (월-화)
- PM: Mock API 서버 완성
  - Prism 설정
  - Docker Compose 구성
  - Pub/Sub Emulator 설정
- Alice: BigQuery 테이블 생성 (hand_summary)
- Bob: BigQuery 테이블 생성 (video_files)
- 전체: 로컬 개발 환경 설정
  - Python 3.11
  - Node.js 18
  - gcloud CLI
  - Docker Desktop

#### Day 3-4 (수-목)
- Alice: Dataflow 템플릿 학습
- Bob: FFmpeg 학습
- Charlie: Vision API 학습
- David: Vertex AI 학습
- Eve: Pub/Sub 학습
- Frank: Next.js 14 학습

#### Day 5 (금요일)
- ✅ Week 2 킥오프 미팅 (14:00-16:00)
  - Mock API 데모
  - 개발 환경 확인
  - Week 3 우선순위 확정
  - **개발 공식 시작 선언** 🚀

---

## Week 3: 완전 병렬 개발 시작 (6명 동시) 🚀

### 목표
- **전체 6개 모듈 동시 개발 시작** ⭐
- 30% 진행률 달성
- Mock 데이터 활용으로 100% 팀 활용률

### 일정

#### Day 1 (월요일)
- **Alice (M1)**:
  - Dataflow 파이프라인 기본 구조
  - GCS → BigQuery ETL 로직
- **Bob (M2)**:
  - NAS 스캔 로직 구현
  - FFmpeg 메타데이터 추출
- **Charlie (M3)**: ⭐ Mock 데이터로 시작
  - Mock BigQuery 연동 (`dev.hand_summary_mock`)
  - Vision API 통합 시작
- **David (M4)**: ⭐ Mock 데이터로 시작
  - Mock BigQuery + Embeddings 연동
  - Vertex AI 파이프라인 구조 설계
- **Eve (M5)**:
  - Pub/Sub Emulator 연동
  - Local Agent 기본 구조
- **Frank (M6)**:
  - Next.js 프로젝트 초기화
  - UI 레이아웃 구현

#### Day 2-4 (화-목)
- Alice: Dataflow 변환 로직 구현
- Bob: 프록시 생성 로직 구현
- **Charlie: sync_score 알고리즘 구현 (Mock 데이터)**
- **David: Mock Embedding 검색 구현**
- Eve: FFmpeg 클리핑 로직
- Frank: 검색 UI + Mock M4 연동

#### Day 5 (금요일)
- ✅ Week 3 Review
  - M1: 50% (ETL 로직 완료)
  - M2: 40% (스캔 로직 완료)
  - M3: 30% (Vision API 통합, Mock 연동) ⭐
  - M4: 30% (Embedding 파이프라인, Mock 연동) ⭐
  - M5: 30% (Mock Pub/Sub 연동)
  - M6: 20% (UI 스켈레톤)
  - **Overall: 30%** ✅
  - **팀 활용률: 100%** (6/6 팀원 활발) 🎉

---

## Week 4: 전체 모듈 병렬 개발 계속

### 목표
- M1 완료
- M2, M3, M4, M5, M6 모두 진행 중
- 50% 진행률 달성

### 일정

#### Day 1-3 (월-수)
- **Alice (M1)**:
  - 에러 핸들링
  - API 서버 구현 (Flask)
  - 유닛 테스트
- **Bob (M2)**:
  - GCS 업로드 구현
  - API 서버 구현
- **Charlie (M3)**: Mock 데이터 계속
  - sync_score 알고리즘 완성
  - Offset 계산 로직
- **David (M4)**: Mock 데이터 계속
  - Re-ranking 알고리즘 구현
  - 자동 완성 API
- **Eve (M5)**:
  - GCS 업로드 구현
  - Signed URL 생성
- **Frank (M6)**:
  - 검색 결과 표시
  - 비디오 미리보기

#### Day 4 (목요일)
- **Alice (M1)**: ✅ M1 완료
  - Cloud Run 배포
  - 통합 테스트 (샘플 데이터)
- Charlie, David: 계속 Mock 데이터로 개발

#### Day 5 (금요일)
- ✅ Week 4 Review
  - M1: ✅ 100% (완료)
  - M2: 70% (프록시 생성 완료)
  - M3: 60% (sync_score 알고리즘 완료, Mock) ⭐
  - M4: 50% (Re-ranking 구현, Mock) ⭐
  - M5: 60% (클리핑 로직 완료)
  - M6: 50% (UI 기능 50%)
  - **Overall: 50%** ✅
  - **팀 활용률: 100%** (6/6 팀원 활발) 🎉

---

## Week 5: Mock → Real 전환 시작

### 목표
- M2 완료
- M3, M4 Mock → Real BigQuery 전환 ⭐
- M5 Real Pub/Sub 통합
- 70% 진행률 달성

### 일정

#### Day 1 (월요일)
- **Charlie (M3)**: Mock → Real 전환 ⭐
  - `dev.hand_summary_mock` → `prod.hand_summary` (M1 완료)
  - `dev.video_files_mock` → `prod.video_files` (M2 거의 완료)
  - Real 데이터로 통합 테스트
- **David (M4)**: Mock → Real 전환 ⭐
  - `dev.hand_summary_mock` → `prod.hand_summary` (M1 완료)
  - Vertex AI Embedding 파이프라인 실제 실행
- **Bob (M2)**: 완료 준비
- **Eve (M5)**: Real Pub/Sub 통합 시작

#### Day 2-4 (화-목)
- Charlie: Real 데이터로 sync_score 재검증
- David: Vector Search 실제 인덱스 구축
- Bob: M2 완료 (API 서버, 문서화)
- Eve: Real Pub/Sub Topic 연동
- Frank: 다운로드 UI 구현

#### Day 5 (금요일)
- ✅ Week 5 Review
  - M1: ✅ 100%
  - M2: ✅ 100% (완료)
  - M3: 70% (Real 데이터 전환 완료) ⭐
  - M4: 60% (Real Embedding 진행 중) ⭐
  - M5: 80% (Real Pub/Sub 연동)
  - M6: 65% (다운로드 UI)
  - **Overall: 70%** ✅
  - **팀 활용률: 100%** 🎉

---

## Week 6: 모든 백엔드 모듈 완료

### 목표
- M3, M4, M5 완료 (Real 데이터 전환 완료)
- M6 Real API 통합 준비
- 85% 진행률 달성

### 일정

#### Day 1-4 (월-목)
- **Charlie (M3)**:
  - Real 데이터 성능 최적화
  - 수동 매칭 API 완성
  - 배치 검증 API
  - Cloud Run 배포
- **David (M4)**:
  - Vector Search 최적화
  - 피드백 시스템 구현
  - 자동 완성 API
  - Cloud Run 배포
- **Eve (M5)**:
  - HA 설정 (Primary + Standby)
  - Failover 구현
  - systemd 등록
  - Production 배포
- **Frank (M6)**:
  - Real API 통합 준비 (M3, M4, M5 URL 확인)
  - 인증 테스트 (IAP)

#### Day 5 (금요일)
- ✅ Week 6 Review
  - M1: ✅ 100%
  - M2: ✅ 100%
  - M3: ✅ 100% (완료, Real 데이터) ⭐
  - M4: ✅ 100% (완료, Real 데이터) ⭐
  - M5: ✅ 100% (완료, Real Pub/Sub) ⭐
  - M6: 75% (Real API 준비)
  - **Overall: 85%** ✅
  - **팀 활용률: 100%** 🎉
  - **M6 통합 준비 완료** 🚀

---

## Week 7: 통합 테스트

### 목표
- M6 Real API 통합
- E2E 테스트
- 90% 진행률 달성

### 일정

#### Day 1-2 (월-화)
- **Frank (M6)**:
  - Mock → Real API 전환
  - M4 통합 (검색)
  - M5 통합 (다운로드)
  - M3 통합 (관리자)

#### Day 3-4 (수-목)
- 전체: 통합 테스트
  - M1 → M3 (데이터 수집 → 검증)
  - M1 → M4 (데이터 → 검색)
  - M6 → M4 → M5 (검색 → 다운로드)

#### Day 5 (금요일)
- E2E 테스트 (Playwright)
- 버그 수정
- ✅ Week 7 Review
  - M6: ✅ 95% (통합 완료)
  - E2E: 80%
  - **Overall: 90%** ✅

---

## Week 8: 버그 수정 및 최적화

### 목표
- 버그 수정
- 성능 최적화
- 95% 진행률 달성

### 일정

#### Day 1-3 (월-수)
- 전체: 버그 수정
  - Critical Bugs: 즉시 수정
  - Minor Bugs: 백로그

#### Day 4-5 (목-금)
- 성능 최적화
  - M4: 검색 속도 (<500ms)
  - M5: 클리핑 속도 (<1분)
- 문서화
- ✅ Week 8 Review
  - 모든 모듈: ✅ 100%
  - E2E: ✅ 100%
  - **Overall: 95%** ✅
  - **Production 배포 준비** 🚀

---

## Week 9: Production 배포

### 목표
- Staging 배포
- Production 배포
- 100% 완료

### 일정

#### Day 1-2 (월-화)
- Staging 환경 배포
  - 전체 모듈 배포
  - Staging E2E 테스트

#### Day 3 (수요일)
- 사용성 테스트 (내부 사용자)
- 피드백 수집 및 반영

#### Day 4 (목요일)
- Production 배포
  - M1, M2, M3, M4, M5 배포
  - M6 배포
  - DNS 설정
  - 모니터링 설정

#### Day 5 (금요일)
- 안정화
- 모니터링
- ✅ **프로젝트 완료** 🎉
  - **Overall: 100%**
  - 런치 파티 🍾

---

## 리스크 대응 계획

### 리스크 1: M1 지연 (Week 4 → Week 5)

**영향**:
- M3, M4 시작 1주 지연
- 전체 일정 1주 지연

**대응**:
- M1 우선순위 최상
- Alice 전담 + 팀 지원
- 일일 진행률 체크

---

### 리스크 2: 통합 실패 (Week 7)

**영향**:
- E2E 테스트 실패
- Week 8 일정 압박

**대응**:
- Week 4부터 Contract Testing
- Weekly API 스펙 검토
- Mock API 사전 통합

---

### 리스크 3: NAS 접근 지연

**영향**:
- M2, M5 개발 블로킹

**대응**:
- Week 2에 NAS 준비 완료
- 샘플 영상 파일 준비
- 로컬 Mock NAS 구축

---

## 체크포인트

| Week | Milestone | 진행률 | 팀 활용률 | 상태 |
|------|-----------|--------|----------|------|
| 1 | API 스펙 확정 | 0% → 5% | - | ✅ |
| 2 | Mock API 완성 | 5% → 10% | - | ✅ |
| 3 | **6명 동시 시작** ⭐ | 10% → 30% | **100%** | 🟢 |
| 4 | 전체 병렬 개발 | 30% → 50% | **100%** | 🟢 |
| 5 | Mock → Real 전환 | 50% → 70% | **100%** | 🟢 |
| 6 | 백엔드 완료 | 70% → 85% | **100%** | 🟢 |
| 7 | 통합 테스트 | 85% → 93% | **100%** | 🟢 |
| 8 | 버그 수정 | 93% → 97% | **100%** | 🟢 |
| 9 | Production | 97% → 100% | **100%** | 🎉 |

**평균 팀 활용률**: **100%** (Week 3-9, 7주 연속) ✅
**개선**: 기존 89% → 신규 100% (**+11% 향상**)

---

**작성자**: microservices-pm (AI Agent)
**최종 업데이트**: 2025-11-17
**승인 필요**: aiden.kim@ggproduction.net
