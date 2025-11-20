# Quick Start Guide - 5분 빠른 시작

**목표**: 5분 안에 로컬 환경에서 프론트엔드 + 백엔드 실행

---

## 1단계: 필수 요구사항 확인 (1분)

### 설치 확인
```bash
# Node.js 18+ 확인
node --version

# Python 3.11+ 확인
python --version

# Git 확인
git --version
```

설치가 안 되어 있다면:
- **Node.js**: https://nodejs.org (LTS 버전)
- **Python**: https://python.org (3.11 이상)
- **Git**: https://git-scm.com

---

## 2단계: 프로젝트 설정 (2분)

### A. 백엔드 설정

```powershell
# 1. backend 폴더로 이동
cd backend

# 2. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate    # Mac/Linux

# 3. 의존성 설치
pip install -r ../requirements-poc.txt

# 4. 환경변수 파일 복사
copy ..\.env.poc .env  # Windows
# cp ../.env.poc .env  # Mac/Linux
```

### B. 프론트엔드 설정

```powershell
# 새 터미널 열기
cd frontend

# 1. 의존성 설치
npm install

# 2. 환경변수 파일 생성 (자동)
# start_frontend.ps1 스크립트가 자동 생성
```

---

## 3단계: 서버 실행 (1분)

### 방법 1: 자동 스크립트 (권장 ⭐)

```powershell
# 프로젝트 루트에서
.\START_SERVERS.ps1
```

**결과**: 백엔드와 프론트엔드가 각각 새 PowerShell 창에서 실행됩니다.

### 방법 2: 수동 실행

**터미널 1 - 백엔드**:
```powershell
cd backend
.\start_backend.ps1
```

**터미널 2 - 프론트엔드**:
```powershell
cd frontend
.\start_frontend.ps1
```

---

## 4단계: 확인 (1분)

### 백엔드 확인
- URL: http://localhost:9000/docs
- 예상: Swagger UI API 문서 페이지

### 프론트엔드 확인
- URL: http://localhost:9001
- 예상: Poker Archive Search 홈페이지

### API 연결 확인
```bash
# 헬스체크
curl http://localhost:9000/health

# 예상 응답:
# {"status":"healthy"}
```

---

## 5단계: 첫 검색 시도 (선택)

### API에서 직접 검색
```bash
curl "http://localhost:9000/api/search?query=Phil%20Ivey%20bluff&top_k=5"
```

### 프론트엔드에서 검색
1. http://localhost:9001 접속
2. 검색창에 "Phil Ivey bluff" 입력
3. 결과 확인

---

## 문제 해결

### 포트 충돌 (3000, 8000번 사용 중)
→ 이미 9000, 9001번 포트를 사용하도록 설정되어 있습니다.

### "uvicorn not found" 오류
```powershell
# 가상환경 활성화 확인
.\venv\Scripts\Activate.ps1

# 다시 설치
pip install -r ../requirements-poc.txt
```

### "Module not found @/" 오류 (프론트엔드)
```powershell
# 의존성 재설치
cd frontend
rm -rf node_modules
npm install
```

### Ollama 연결 오류
```powershell
# Ollama 설치 필요 (RAG 기능용)
# https://ollama.ai 에서 다운로드

# Qwen3-8B 모델 설치
ollama pull qwen3:8b

# Ollama 서버 시작
ollama serve
```

---

## 다음 단계

### 개발 시작
- **백엔드**: `backend/app/` 폴더에서 코드 수정
- **프론트엔드**: `frontend/src/` 폴더에서 코드 수정
- **자동 새로고침**: 코드 변경 시 자동으로 반영됨

### 테스트 실행
```bash
# 백엔드 테스트
cd backend
pytest tests/

# 프론트엔드 테스트
cd frontend
npm test
npm run e2e  # E2E 테스트
```

### 상세 가이드
- **개발자 가이드**: [CLAUDE.md](../CLAUDE.md)
- **프로젝트 개요**: [README.md](./README.md)
- **문제 해결**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## 빠른 명령어 참조

```bash
# 서버 시작
.\START_SERVERS.ps1

# 서버 중지
# 각 PowerShell 창에서 Ctrl+C

# 백엔드 API 문서
http://localhost:9000/docs

# 프론트엔드
http://localhost:9001

# 백엔드 테스트
cd backend && pytest

# 프론트엔드 테스트
cd frontend && npm test
```

---

**시작 완료! 🎉**

문제가 있으면 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)를 확인하세요.
