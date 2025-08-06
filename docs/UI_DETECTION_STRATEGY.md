# 🎯 그래픽 UI 기반 핸드 감지 전략

## 📐 UI 감지 알고리즘 설계

### 1. UI 감지 핵심 메트릭

```python
class UIDetectionMetrics:
    def __init__(self):
        self.metrics = {
            'motion_score': 0,      # 움직임 양 (0-100, 낮을수록 UI)
            'text_density': 0,      # 텍스트 밀도 (0-100, 높을수록 UI)
            'color_uniformity': 0,  # 색상 균일도 (0-100, 높을수록 UI)
            'edge_density': 0,      # 엣지 밀도 (0-100, 높을수록 UI)
            'layout_score': 0       # 레이아웃 패턴 (0-100, 높을수록 UI)
        }
```

### 2. 단계별 감지 프로세스

#### Step 1: 모션 분석
```python
# 프레임 간 차이 계산
motion_pixels = cv2.absdiff(prev_frame, curr_frame)
motion_score = 100 - (np.count_nonzero(motion_pixels) / total_pixels * 100)

# UI는 정적이므로 motion_score가 높음 (80 이상)
```

#### Step 2: 텍스트 영역 감지
```python
# EAST 텍스트 감지기 또는 MSER 사용
text_regions = detect_text_regions(frame)
text_density = (text_area / frame_area) * 100

# UI는 텍스트가 많으므로 text_density가 높음 (30 이상)
```

#### Step 3: 색상 분포 분석
```python
# 색상 히스토그램 분석
color_hist = cv2.calcHist([frame], [0,1,2], None, [8,8,8], [0,256,0,256,0,256])
color_uniformity = calculate_uniformity(color_hist)

# UI는 제한된 색상 팔레트 사용 (uniformity 70 이상)
```

#### Step 4: 엣지 패턴 분석
```python
# Canny 엣지 감지
edges = cv2.Canny(frame, 50, 150)
edge_density = np.count_nonzero(edges) / total_pixels * 100

# UI는 직선적인 엣지가 많음 (density 20 이상)
```

#### Step 5: 레이아웃 구조 분석
```python
# 수평/수직 라인 감지
lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100)
layout_score = analyze_grid_structure(lines)

# UI는 격자 구조가 명확 (score 60 이상)
```

### 3. 종합 UI 판정

```python
def calculate_ui_probability(metrics):
    weights = {
        'motion_score': 0.25,
        'text_density': 0.20,
        'color_uniformity': 0.20,
        'edge_density': 0.15,
        'layout_score': 0.20
    }
    
    ui_probability = sum(metrics[key] * weights[key] for key in metrics)
    return ui_probability

# UI 판정 임계값: 65% 이상
```

## 🎬 UI 지속 시간 추적

```python
class UITracker:
    def __init__(self):
        self.ui_start_time = None
        self.ui_duration = 0
        self.ui_history = deque(maxlen=450)  # 15초 @ 30fps
        
    def update(self, is_ui_frame, timestamp):
        self.ui_history.append(is_ui_frame)
        
        # 연속 UI 프레임 카운트
        consecutive_ui = sum(1 for x in self.ui_history if x)
        
        if consecutive_ui >= 450:  # 15초 이상
            if self.ui_start_time is None:
                self.ui_start_time = timestamp - 15
            self.ui_duration = timestamp - self.ui_start_time
            return 'UI_PERSISTENT'
        
        elif consecutive_ui < 30 and self.ui_start_time:  # UI 종료
            hand_end_time = self.ui_start_time - 15
            self.reset()
            return 'HAND_END', hand_end_time
            
        return 'MONITORING'
```

## 🔄 핸드 경계 결정 로직

### UI 기반 핸드 종료 감지
```python
def detect_hand_end_by_ui(ui_tracker, current_time):
    status = ui_tracker.update(is_ui_detected, current_time)
    
    if status[0] == 'HAND_END':
        return {
            'hand_end': status[1],
            'confidence': 0.95,  # UI 기반은 높은 신뢰도
            'reason': 'UI_APPEARANCE'
        }
```

### UI 기반 핸드 시작 감지
```python
def detect_hand_start_by_ui(ui_tracker, game_resumed_time):
    # UI 종료 후 15초 버퍼
    potential_hand_start = game_resumed_time + 15
    
    # 추가 검증: 실제 게임 활동 확인
    if verify_game_activity(potential_hand_start):
        return {
            'hand_start': potential_hand_start,
            'confidence': 0.90,
            'reason': 'POST_UI_RESUMPTION'
        }
```

## 📊 UI 패턴 학습

### 방송사별 UI 템플릿 매칭
```python
class BroadcasterUITemplates:
    def __init__(self):
        self.templates = {
            'pokerstars': [
                {'type': 'player_stats', 'features': {...}},
                {'type': 'tournament_info', 'features': {...}}
            ],
            'wsop': [
                {'type': 'break_screen', 'features': {...}},
                {'type': 'chip_count', 'features': {...}}
            ]
        }
    
    def match_template(self, frame):
        best_match = None
        best_score = 0
        
        for broadcaster, templates in self.templates.items():
            for template in templates:
                score = calculate_similarity(frame, template)
                if score > best_score:
                    best_score = score
                    best_match = (broadcaster, template['type'])
        
        return best_match if best_score > 0.8 else None
```

## 🚀 통합 구현 예시

```python
class EnhancedHandDetector:
    def __init__(self):
        self.ui_tracker = UITracker()
        self.ui_detector = UIDetector()
        self.traditional_detector = TraditionalHandDetector()
        self.hands = []
        
    def process_frame(self, frame, timestamp):
        # 1. UI 감지
        ui_metrics = self.ui_detector.analyze(frame)
        is_ui = ui_metrics['probability'] > 0.65
        
        # 2. UI 추적
        ui_status = self.ui_tracker.update(is_ui, timestamp)
        
        # 3. 핸드 경계 결정
        if ui_status[0] == 'HAND_END':
            self.finalize_hand(ui_status[1])
        
        # 4. 기존 방식과 병행
        if not is_ui:
            traditional_result = self.traditional_detector.process(frame)
            self.merge_results(ui_status, traditional_result)
    
    def merge_results(self, ui_result, traditional_result):
        # UI 기반 결과를 우선시
        if ui_result['confidence'] > 0.9:
            return ui_result
        
        # 두 방식의 결과를 가중 평균
        combined_confidence = (
            ui_result['confidence'] * 0.6 + 
            traditional_result['confidence'] * 0.4
        )
        
        return {
            'hand_boundary': ui_result['boundary'],
            'confidence': combined_confidence,
            'method': 'HYBRID'
        }
```

## 📈 성능 향상 예상

### 기존 방식 vs UI 기반 방식
```
정확도 비교:
- 기존: 75% (카드/칩 기반)
- UI 기반: 90% (명확한 시각적 단서)
- 하이브리드: 95% (상호 보완)

처리 속도:
- 기존: 복잡한 객체 감지 필요
- UI 기반: 단순 패턴 매칭
- 결과: 2-3배 속도 향상

오탐지율:
- 기존: 15% (조명, 카메라 각도 영향)
- UI 기반: 5% (환경 변화에 강건)
```

## 🎯 구현 우선순위

1. **Phase 1**: 기본 UI 감지 (모션 + 텍스트)
2. **Phase 2**: 15초 규칙 적용
3. **Phase 3**: 방송사별 템플릿 학습
4. **Phase 4**: 하이브리드 시스템 구축