# 🧪 포커 MAM 테스트 가이드

## 📋 목차
1. [빠른 시작](#빠른-시작)
2. [테스트 환경 설정](#테스트-환경-설정)
3. [테스트 시나리오](#테스트-시나리오)
4. [문제 해결](#문제-해결)

---

## 🚀 빠른 시작

### 1분 안에 테스트 시작하기

```bash
# 1. 테스트 환경 설정
python setup_test_env.py

# 2. 웹 서버 실행
python run_poker_app.py

# 3. 브라우저에서 접속
http://localhost:5000
```

### Windows 사용자
```cmd
# 테스트 메뉴 실행
test_menu.bat
```

---

## 🛠️ 테스트 환경 설정

### 1. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

주요 패키지:
- Flask (웹 프레임워크)
- OpenCV (영상 처리)
- NumPy (수치 연산)
- yt-dlp (YouTube 다운로드)

### 2. 디렉토리 구조 생성
```
python setup_test_env.py
```

생성되는 디렉토리:
```
Archive-MAM/
├── videos/              # 원본 비디오
├── test_videos/         # 테스트 비디오
├── temp_videos/         # 임시 파일
├── analysis_results/    # 분석 결과
├── static/results/      # 웹 결과 파일
└── logs/               # 로그 파일
```

### 3. 샘플 비디오 생성
```bash
python src/generate_sample_video.py
```

생성되는 파일:
- `test_videos/sample_poker_tournament.mp4` (10분, 30fps)

---

## 🎮 테스트 시나리오

### 시나리오 1: 고속 분석 테스트

#### 목적
60프레임 샘플링 기반 고속 분석 성능 확인

#### 실행 방법
```bash
python test_fast_detector.py test_videos/sample_poker_tournament.mp4
```

#### 예상 결과
```
=== 성능 비교 테스트 ===
고속 감지기 (샘플링 비율: 60:1)
   - 60프레임마다 1개 분석
   - 병렬 처리 (4 워커)
   ✓ 소요 시간: 90.5초 (1.5분)
   ✓ 감지된 핸드: 15개
   ✓ 속도 향상: 800x
```

### 시나리오 2: 웹 UI 테스트

#### 목적
웹 인터페이스를 통한 전체 기능 테스트

#### 실행 단계
1. 웹 서버 시작
   ```bash
   python run_poker_app.py
   ```

2. 브라우저 접속: `http://localhost:5000`

3. 테스트 케이스:
   - **파일 업로드**: 샘플 비디오 업로드
   - **URL 스트리밍**: YouTube 포커 영상 URL 입력
   - **고속 모드**: 체크박스 선택 후 분석

#### 확인 사항
- [ ] 파일 업로드 정상 작동
- [ ] 진행률 표시 정확성
- [ ] 분석 결과 차트 표시
- [ ] JSON 다운로드 기능

### 시나리오 3: 정확도 비교 테스트

#### 목적
샘플링 비율별 정확도 확인

#### 실행 방법
```bash
# 다양한 샘플링 비율 테스트
python run_simple_test.py fast
```

#### 비교 항목
| 샘플링 | 속도 | 정확도 | 용도 |
|--------|------|--------|------|
| 15:1 | 4분 | 90% | 정밀 분석 |
| 30:1 | 2분 | 85% | 표준 분석 |
| 60:1 | 1분 | 80% | 빠른 분석 |
| 90:1 | 30초 | 70% | 미리보기 |

### 시나리오 4: 스트리밍 테스트

#### 목적
YouTube/Twitch 실시간 스트리밍 분석

#### 테스트 URL
```
https://www.youtube.com/watch?v=[포커_영상_ID]
```

#### 실행 방법
1. 웹 UI에서 URL 입력
2. "고속 분석 모드" 선택
3. 분석 시작

---

## 🔍 테스트 검증 체크리스트

### 기능 테스트
- [ ] 샘플 비디오 생성 성공
- [ ] 웹 서버 정상 시작
- [ ] 파일 업로드 기능
- [ ] URL 스트리밍 기능
- [ ] 고속 분석 모드
- [ ] 결과 시각화
- [ ] JSON 내보내기

### 성능 테스트
- [ ] 10분 영상 2분 내 분석
- [ ] CPU 사용률 확인
- [ ] 메모리 사용량 확인
- [ ] 병렬 처리 동작

### 정확도 테스트
- [ ] 핸드 시작점 감지
- [ ] 핸드 종료점 감지
- [ ] 핸드 길이 분류
- [ ] 오탐지율 확인

---

## 🐛 문제 해결

### 1. ImportError 발생
```bash
# 필수 패키지 재설치
pip install -r requirements.txt --upgrade
```

### 2. 비디오 생성 실패
```bash
# OpenCV 코덱 확인
python -c "import cv2; print(cv2.getBuildInformation())"

# FFmpeg 설치 (Windows)
# https://ffmpeg.org/download.html
```

### 3. 웹 서버 접속 불가
```bash
# 포트 확인
netstat -an | findstr :5000

# 다른 포트로 실행
python run_poker_app.py --port 8080
```

### 4. 메모리 부족
```python
# 워커 수 줄이기
detector = FastHandDetector(sampling_rate=60, num_workers=2)
```

### 5. GPU 사용 (선택사항)
```bash
# CUDA 버전 OpenCV 설치
pip install opencv-python-headless[cuda]
```

---

## 📊 테스트 결과 분석

### 로그 파일 위치
- 웹 서버: `logs/poker_app.log`
- 분석 결과: `analysis_results/`

### 성능 메트릭 확인
```python
# 테스트 결과 분석 스크립트
import json
import glob

for result_file in glob.glob("analysis_results/*.json"):
    with open(result_file) as f:
        data = json.load(f)
        print(f"파일: {result_file}")
        print(f"핸드 수: {len(data)}")
        print(f"평균 길이: {sum(h['duration'] for h in data)/len(data):.1f}초")
```

---

## 🎯 추가 테스트 옵션

### 대용량 파일 테스트
```bash
# 1시간 영상 테스트
python test_fast_detector.py large_tournament.mp4
```

### 배치 처리 테스트
```python
# 여러 영상 동시 분석
for video in videos:
    detector.analyze_video(video)
```

### 실시간 모니터링
```bash
# 분석 중 시스템 모니터링
# Windows: Task Manager
# Linux: htop
```

---

## 📝 테스트 보고서 템플릿

```markdown
### 테스트 일자: 2025-07-31

#### 환경
- OS: Windows 11
- Python: 3.9.0
- CPU: Intel i7 (4 cores)
- RAM: 16GB

#### 테스트 결과
1. 샘플 비디오 (10분)
   - 분석 시간: 1분 30초
   - 감지된 핸드: 15개
   - 정확도: 80%

2. 실제 포커 영상 (30분)
   - 분석 시간: 4분 20초
   - 감지된 핸드: 42개
   - 정확도: 85%

#### 이슈
- 없음

#### 개선사항
- GPU 가속 추가 시 50% 추가 성능 향상 예상
```

---

**문서 버전**: 1.0  
**최종 수정**: 2025년 7월 31일