# 🌐 포커 MAM 온라인 테스트 환경

## 📋 목차
1. [온라인 테스트 옵션](#온라인-테스트-옵션)
2. [GitHub Codespaces](#github-codespaces)
3. [Gitpod](#gitpod)
4. [GitHub Actions](#github-actions)
5. [Docker 환경](#docker-환경)
6. [온라인 데모](#온라인-데모)

---

## 🚀 온라인 테스트 옵션

로컬 환경 설정 없이 브라우저에서 바로 테스트할 수 있는 여러 옵션을 제공합니다.

### 빠른 시작 버튼

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?template=your-username/Archive-MAM)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/your-username/Archive-MAM)

[![Run on Repl.it](https://repl.it/badge/github/your-username/Archive-MAM)](https://repl.it/github/your-username/Archive-MAM)

---

## 💻 GitHub Codespaces

### 1. Codespaces 시작
1. 이 리포지토리 페이지에서 `Code` 버튼 클릭
2. `Codespaces` 탭 선택
3. `Create codespace on main` 클릭

### 2. 자동 설정
Codespace가 시작되면 자동으로:
- Python 환경 설정
- 필수 패키지 설치
- 샘플 비디오 생성
- 테스트 환경 준비

### 3. 웹 서버 실행
```bash
# 터미널에서 실행
python run_poker_app.py
```

### 4. 웹 UI 접속
- 포트 5000이 자동으로 포워딩됨
- 알림에서 "Open in Browser" 클릭

### 5. 테스트 실행
```bash
# 고속 분석 테스트
python test_fast_detector.py

# 빠른 환경 테스트
python quick_test.py
```

---

## 🚢 Gitpod

### 1. Gitpod 시작
위의 "Open in Gitpod" 버튼 클릭 또는:
```
https://gitpod.io/#https://github.com/your-username/Archive-MAM
```

### 2. 자동 실행
- 환경이 자동으로 설정됨
- Flask 서버가 자동 시작
- 포트 5000이 공개됨

### 3. 테스트 명령어
```bash
# 새 터미널 열기 (Ctrl+`)
# 샘플 비디오 확인
ls test_videos/

# 고속 분석 실행
python test_fast_detector.py test_videos/sample_poker_tournament.mp4
```

---

## 🔄 GitHub Actions

### 1. 자동 테스트 확인
- Pull Request 생성 시 자동 테스트 실행
- Actions 탭에서 테스트 결과 확인

### 2. 수동 테스트 실행
1. Actions 탭 이동
2. "Poker MAM Tests" 워크플로우 선택
3. "Run workflow" 클릭

### 3. 테스트 결과 다운로드
- 테스트 완료 후 Artifacts 섹션에서 결과 다운로드
- `test-results-3.9.zip` 파일 확인

---

## 🐳 Docker 환경

### 1. Docker로 실행
```bash
# 리포지토리 클론
git clone https://github.com/your-username/Archive-MAM.git
cd Archive-MAM

# Docker 컨테이너 빌드 및 실행
docker-compose up
```

### 2. 브라우저 접속
```
http://localhost:5000
```

### 3. Docker 명령어
```bash
# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

---

## 🌟 온라인 데모

### GitHub Pages 데모
- URL: `https://your-username.github.io/Archive-MAM/`
- 프로젝트 소개 및 데모 링크 제공

### 온라인 IDE 비교

| 플랫폼 | 장점 | 단점 | 추천 용도 |
|--------|------|------|-----------|
| **Codespaces** | VS Code 환경, 4코어 제공 | 월 60시간 무료 | 풀 개발 환경 |
| **Gitpod** | 빠른 시작, 50시간 무료 | 제한된 리소스 | 빠른 테스트 |
| **Repl.it** | 간단한 UI | 느린 성능 | 코드 보기 |
| **Docker** | 로컬 성능 | 설치 필요 | 프로덕션 테스트 |

---

## 📱 모바일 테스트

### 1. Gitpod 모바일
- 모바일 브라우저에서 Gitpod 접속
- 터치 친화적 인터페이스

### 2. 테스트 URL 공유
- Gitpod/Codespaces에서 생성된 공개 URL 공유
- 다른 기기에서 접속 가능

---

## 🔧 환경 설정 팁

### 1. 더 빠른 시작
```bash
# 미리 빌드된 이미지 사용
docker pull your-dockerhub/poker-mam:latest
docker run -p 5000:5000 your-dockerhub/poker-mam
```

### 2. 리소스 최적화
```python
# Codespaces/Gitpod에서 워커 수 조정
detector = FastHandDetector(sampling_rate=60, num_workers=2)
```

### 3. 샘플 데이터
```bash
# 작은 테스트 비디오 생성 (1분)
python -c "from src.generate_sample_video import create_sample_video; create_sample_video(duration=60)"
```

---

## 🎯 테스트 시나리오

### 시나리오 1: 빠른 확인 (2분)
```bash
# 1. 환경 테스트
python quick_test.py

# 2. 웹 서버 확인
curl http://localhost:5000
```

### 시나리오 2: 전체 테스트 (10분)
```bash
# 1. 샘플 비디오 생성
python src/generate_sample_video.py

# 2. 고속 분석 실행
python test_fast_detector.py

# 3. 웹 UI 테스트
python run_poker_app.py
```

### 시나리오 3: CI/CD 확인
1. Fork 리포지토리
2. 작은 변경사항 커밋
3. Pull Request 생성
4. Actions에서 테스트 결과 확인

---

## 💡 문제 해결

### Codespaces/Gitpod 느림
```bash
# 가벼운 모드로 실행
export FLASK_ENV=production
python run_poker_app.py
```

### 포트 접속 불가
```bash
# 다른 포트로 변경
python run_poker_app.py --port 8080
```

### 메모리 부족
```python
# 샘플링 비율 증가
detector = FastHandDetector(sampling_rate=120, num_workers=1)
```

---

## 📊 성능 비교

| 환경 | CPU | RAM | 10분 영상 분석 시간 |
|------|-----|-----|-------------------|
| 로컬 (i7) | 8코어 | 16GB | 1-2분 |
| Codespaces | 4코어 | 8GB | 2-3분 |
| Gitpod | 2코어 | 4GB | 3-4분 |
| Docker | 호스트 의존 | 호스트 의존 | 1-3분 |

---

## 🚀 다음 단계

1. **프로덕션 배포**
   - AWS/GCP에 Docker 배포
   - Kubernetes 클러스터 설정

2. **API 서비스**
   - REST API 엔드포인트
   - 인증 시스템 추가

3. **모니터링**
   - Prometheus/Grafana 설정
   - 로그 수집 시스템

---

**문서 버전**: 1.0  
**최종 수정**: 2025년 7월 31일

## 지원 및 문의

- 📧 이메일: support@pokermam.com
- 💬 Discord: [참여하기](https://discord.gg/pokermam)
- 🐛 이슈: [GitHub Issues](https://github.com/your-username/Archive-MAM/issues)