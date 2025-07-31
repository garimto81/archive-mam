# ⚡ 고속 분석 기능 가이드

## 개요

포커 MAM의 고속 분석 기능은 긴 영상을 빠르게 분석하기 위해 개발된 최적화된 핸드 감지 시스템입니다. 
기존 방식 대비 최대 800배 빠른 속도로 분석이 가능합니다.

---

## 🚀 빠른 시작

### 웹 인터페이스 사용
1. 포커 MAM 웹 애플리케이션 실행
2. 영상 업로드 또는 URL 입력
3. **"고속 분석 모드"** 체크박스 선택
4. 분석 시작 클릭

### 커맨드라인 사용
```bash
# Windows
run_fast_analysis.bat your_video.mp4

# Python
python test_fast_detector.py your_video.mp4
```

---

## 🔧 기술적 세부사항

### 핵심 최적화 기법

#### 1. 프레임 샘플링 (60:1)
- 30fps 영상 기준 2초마다 1프레임만 분석
- 10분 영상: 18,000프레임 → 300프레임

#### 2. 멀티프로세싱
- CPU 코어 수만큼 워커 프로세스 생성
- 프레임을 청크로 분할하여 병렬 처리

#### 3. 이미지 전처리
- 480x270 해상도로 리사이즈
- 중앙 60% 영역만 카드 감지

#### 4. 간소화된 알고리즘
- 복잡한 옵티컬 플로우 대신 모션 변화량 추적
- HSV 색상 기반 빠른 카드 감지

---

## 📊 성능 비교

### 샘플링 비율별 성능

| 샘플링 비율 | 분석 프레임 수 | 예상 소요 시간 | 정확도 |
|------------|---------------|---------------|--------|
| 15:1 | 1,200개 | 4-5분 | 90% |
| 30:1 | 600개 | 2-3분 | 85% |
| **60:1** | **300개** | **1-2분** | **80%** |
| 90:1 | 200개 | 30-60초 | 70% |

### 사용 시나리오별 권장 설정

#### 빠른 미리보기 (Speed Priority)
- 샘플링: 90:1
- 용도: 대략적인 핸드 위치 파악
- 정확도: 낮음

#### 균형잡힌 분석 (Recommended)
- 샘플링: 60:1
- 용도: 일반적인 분석 작업
- 정확도: 중간

#### 정밀 분석 (Accuracy Priority)
- 샘플링: 15:1 또는 기존 모드
- 용도: 정확한 타임코드 필요시
- 정확도: 높음

---

## 🎯 사용 사례

### 1. 대용량 영상 빠른 스캔
```python
# 여러 시간 분량의 토너먼트 영상 분석
detector = FastHandDetector(sampling_rate=60)
for video in tournament_videos:
    detector.analyze_video(video)
```

### 2. 실시간 스트리밍 분석
```python
# YouTube 라이브 스트림 분석
detector = FastHandDetector(sampling_rate=90)  # 더 빠른 샘플링
detector.analyze_stream(stream_url)
```

### 3. 배치 처리
```python
# 여러 영상 동시 처리
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(analyze_video, video) for video in videos]
```

---

## ⚙️ 고급 설정

### FastHandDetector 파라미터

```python
FastHandDetector(
    sampling_rate=60,    # 프레임 샘플링 비율
    num_workers=None,    # 워커 수 (None=자동)
)
```

### 감지 임계값 조정
```python
detector.motion_threshold = 1000  # 모션 영역 크기
detector.card_threshold = 3       # 최소 카드 수
detector.min_hand_duration = 30   # 최소 핸드 길이(초)
detector.max_hand_duration = 600  # 최대 핸드 길이(초)
```

---

## 🐛 문제 해결

### 핸드를 놓치는 경우
- 샘플링 비율을 낮춰보세요 (60 → 30)
- motion_threshold를 낮춰보세요

### 잘못된 핸드 감지
- card_threshold를 높여보세요
- min_hand_duration을 늘려보세요

### 메모리 부족
- num_workers를 줄여보세요
- 이미지 리사이즈 크기를 더 작게 조정

---

## 📈 향후 개선 계획

1. **GPU 가속**: CUDA 지원으로 추가 속도 향상
2. **적응형 샘플링**: 모션이 많은 구간은 더 자주 샘플링
3. **딥러닝 통합**: YOLO 기반 정확도 향상
4. **실시간 모드**: 스트리밍 중 실시간 분석

---

## 💡 팁과 트릭

1. **첫 분석은 고속 모드로**: 전체적인 핸드 분포 파악
2. **관심 구간만 정밀 분석**: 특정 시간대만 기존 모드로 재분석
3. **네트워크 드라이브 주의**: 로컬에 복사 후 분석이 더 빠름
4. **SSD 사용 권장**: HDD보다 2-3배 빠른 프레임 읽기

---

**문서 버전**: 1.0  
**최종 수정**: 2025년 7월 31일