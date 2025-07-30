# Poker MAM (Media Asset Management) System

포커 영상 분석 및 핸드 아카이빙 시스템

> YouTube Shorts와 같은 포커 콘텐츠 제작을 위한 자동화된 영상 분석 및 관리 시스템

## 프로젝트 개요

YouTube Shorts와 같은 포커 콘텐츠 제작 시, 수많은 핸드 중에서 흥미로운 특정 핸드를 찾아내는 과정을 자동화하는 지능형 미디어 자산 관리(MAM) 시스템입니다.

## 주요 기능

- **자동 핸드 감지**: 영상에서 개별 핸드의 시작과 끝을 자동으로 감지
- **팟 사이즈 분석**: OCR을 통한 팟 사이즈 자동 추출
- **플레이어 식별**: 각 핸드에 참여한 플레이어 자동 분류
- **검색 및 필터링**: 팟 사이즈, 플레이어 등으로 핸드 검색
- **클립 추출**: 특정 핸드만 잘라낸 비디오 클립 생성

## 설치 방법

### 1. 필수 요구사항

- Python 3.8+
- Redis (Celery 작업 큐용)
- FFmpeg (비디오 처리용)
- Tesseract OCR

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. Tesseract OCR 설치

Windows:
- https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드
- 설치 후 `detect_pot_size.py`의 경로 설정 필요

### 4. Redis 설치

Windows:
- WSL을 통해 설치하거나 Docker 사용 권장

## 실행 방법

### 1. Redis 서버 시작
```bash
redis-server
```

### 2. Celery Worker 시작
```bash
python run_celery.py
```

### 3. FastAPI 서버 시작
```bash
python run_api.py
```

API 문서는 http://localhost:8000/docs 에서 확인 가능

## API 사용 예시

### 영상 업로드
```bash
curl -X POST "http://localhost:8000/videos/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@poker_video.mp4"
```

### 핸드 검색
```bash
curl -X POST "http://localhost:8000/hands/search" \
  -H "Content-Type: application/json" \
  -d '{
    "min_pot_size": 1000,
    "player_name": "Player 1"
  }'
```

### 클립 생성
```bash
curl -X POST "http://localhost:8000/clips/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "hand_id": 1
  }'
```

## 프로젝트 구조

```
Archive-MAM/
├── src/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── database.py          # 데이터베이스 모델
│   ├── schemas.py           # Pydantic 스키마
│   ├── celery_app.py        # Celery 설정
│   ├── tasks.py             # 비동기 작업
│   ├── detect_hands.py      # 핸드 감지 모듈
│   ├── detect_pot_size.py   # 팟 사이즈 OCR 모듈
│   ├── detect_players.py    # 플레이어 감지 모듈
│   └── integrate_analysis.py # 통합 분석 모듈
├── uploads/                 # 업로드된 영상 저장
├── clips/                   # 생성된 클립 저장
├── analysis_results/        # 분석 결과 JSON
└── videos/                  # 샘플 비디오
```

## 빠른 시작 (테스트용)

### 간단한 테스트 서버 (Redis/Celery 불필요)
```bash
# 백엔드 테스트 서버 실행
run_test_server.bat

# 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm start
```

### 전체 시스템 실행
```bash
# 1. 환경 확인
quick_test.bat

# 2. Redis 시작 (WSL)
redis-server

# 3. 백엔드 시작
start_backend.bat

# 4. 프론트엔드 시작
start_frontend.bat
```

## 접속 URL
- **프론트엔드**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs

## 개발 현황

### 완료된 기능
- [x] **Phase 1**: 핵심 분석 엔진 개발
  - 핸드 시작/종료 감지
  - 팟 사이즈 OCR 분석
  - 참여 플레이어 식별
  - 통합 분석 파이프라인

- [x] **Phase 2**: 백엔드 시스템 및 API 구축
  - FastAPI 기반 REST API
  - SQLAlchemy ORM 데이터베이스
  - Celery 비동기 작업 처리
  - 영상 업로드 및 분석 API
  - 핸드 검색/필터링 API
  - 클립 생성 및 다운로드 API

- [x] **Phase 3**: 프론트엔드 UI/UX 개발
  - React 18 기반 SPA
  - Ant Design UI 컴포넌트
  - 반응형 디자인
  - 실시간 처리 상태 모니터링
  - 직관적인 핸드 검색 인터페이스

### 다음 단계
- [ ] **Phase 4**: 통합, 테스트 및 배포
  - 성능 최적화
  - 단위/통합 테스트
  - Docker 컨테이너화
  - 프로덕션 배포 가이드

## 기술 스택

### 백엔드
- **Framework**: FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **Task Queue**: Celery + Redis
- **Video Processing**: OpenCV, FFmpeg
- **OCR**: Tesseract

### 프론트엔드
- **Framework**: React 18
- **UI Library**: Ant Design
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Video Player**: React Player

### DevOps
- **Environment**: Python venv
- **Package Manager**: pip, npm
- **Testing**: Pytest (백엔드), Jest (프론트엔드)