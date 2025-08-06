# Poker MAM 테스트 환경 가이드

## 1. 필수 소프트웨어 설치

### Windows 환경 기준

1. **Python 3.8+**
   - https://www.python.org/downloads/

2. **Redis (WSL 또는 Docker 사용)**
   ```bash
   # WSL에서 Redis 설치
   sudo apt update
   sudo apt install redis-server
   ```

3. **FFmpeg**
   - https://ffmpeg.org/download.html
   - PATH에 추가 필요

4. **Tesseract OCR**
   - https://github.com/UB-Mannheim/tesseract/wiki
   - 설치 후 `src/detect_pot_size.py`의 9번째 줄 주석 해제하고 경로 설정

5. **Node.js 18+**
   - https://nodejs.org/

## 2. 백엔드 설정

### 2.1 Python 가상환경 생성
```bash
cd C:\claude\Archive-MAM
python -m venv venv
venv\Scripts\activate
```

### 2.2 패키지 설치
```bash
pip install -r requirements.txt
```

### 2.3 데이터베이스 초기화
```bash
# Python 콘솔에서
python
>>> from src.database import create_db_tables
>>> create_db_tables()
>>> exit()
```

## 3. 시스템 실행

### 터미널 1: Redis 서버
```bash
# WSL 터미널에서
redis-server
```

### 터미널 2: Celery Worker
```bash
cd C:\claude\Archive-MAM
venv\Scripts\activate
python run_celery.py
```

### 터미널 3: FastAPI 서버
```bash
cd C:\claude\Archive-MAM
venv\Scripts\activate
python run_api.py
```

### 터미널 4: React 프론트엔드
```bash
cd C:\claude\Archive-MAM\frontend
npm install  # 첫 실행 시만
npm start
```

## 4. 테스트 방법

### 4.1 API 문서 확인
- http://localhost:8000/docs 접속
- Swagger UI에서 API 테스트 가능

### 4.2 프론트엔드 접속
- http://localhost:3000 접속

### 4.3 샘플 비디오 생성 (선택사항)
```bash
cd C:\claude\Archive-MAM
python -m src.generate_sample_video
```
- `videos/sample_poker_video.mp4` 생성됨

### 4.4 테스트 시나리오

1. **영상 업로드 테스트**
   - 프론트엔드에서 "영상 업로드" 메뉴 클릭
   - 샘플 비디오 또는 실제 포커 영상 업로드
   - "영상 관리"에서 처리 상태 확인

2. **핸드 검색 테스트**
   - "핸드 라이브러리" 메뉴 클릭
   - 팟 사이즈, 플레이어 이름으로 필터링
   - 핸드 카드 클릭하여 상세 정보 확인

3. **클립 생성 테스트**
   - 핸드 상세 페이지에서 "클립 다운로드" 클릭
   - 생성 완료 후 자동 다운로드 확인

## 5. 문제 해결

### Redis 연결 실패
```
Error: [Errno 10061] No connection could be made...
```
- Redis 서버가 실행 중인지 확인
- `redis-cli ping` 명령으로 테스트

### Tesseract OCR 오류
```
TesseractNotFoundError: tesseract is not installed...
```
- Tesseract 설치 확인
- `detect_pot_size.py`에서 경로 설정

### FFmpeg 오류
```
FFmpeg error: ffmpeg: command not found
```
- FFmpeg 설치 및 PATH 설정 확인
- `ffmpeg -version` 명령으로 테스트

### 포트 충돌
- FastAPI: 8000 포트
- React: 3000 포트
- 다른 프로그램이 사용 중이면 포트 변경 필요

## 6. 테스트 데이터

### 기존 분석 결과 확인
```bash
# analysis_results/poker_hands_analysis.json
# 1000개의 샘플 핸드 데이터 포함
```

### 데이터베이스 직접 확인
```bash
# SQLite 브라우저 사용 또는
sqlite3 sql_app.db
.tables
SELECT * FROM videos;
SELECT * FROM hands LIMIT 10;
```

## 7. 로그 확인

### Celery 로그
- Celery Worker 터미널에서 실시간 로그 확인

### FastAPI 로그
- API 서버 터미널에서 요청/응답 로그 확인

### 브라우저 콘솔
- F12 개발자 도구에서 네트워크 탭 확인