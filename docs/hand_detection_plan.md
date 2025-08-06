# 포커 핸드 감지 시스템 상세 계획

## 1. 다층 감지 아키텍처

### Layer 1: 기본 모션 감지
```python
def detect_motion_changes(frames):
    """프레임 간 차이를 통한 기본 모션 감지"""
    # 연속 프레임 간 픽셀 차이 계산
    # 임계값을 넘는 변화가 있는 영역 식별
    # 카드 딜링, 칩 이동 등 큰 변화 감지
```

### Layer 2: 객체 기반 감지
```python
def detect_poker_objects(frame):
    """포커 관련 객체 감지"""
    # 카드 형태 감지 (사각형 패턴)
    # 칩 형태 감지 (원형 패턴)
    # 딜러 손 추적
    # 테이블 영역 정의
```

### Layer 3: 템플릿 매칭
```python
def template_matching(frame, templates):
    """특정 패턴 매칭"""
    # 카드 뒷면 템플릿 매칭
    # 딜러 버튼 위치 추적
    # 특정 방송사 UI 요소 매칭
```

### Layer 4: 색상 분석
```python
def color_analysis(frame):
    """색상 기반 분석"""
    # 카드 색상 (흰색/검은색 패턴)
    # 칩 색상별 분류
    # 테이블 펠트 색상 (녹색 영역)
    # UI 색상 변화 감지
```

## 2. 핸드 경계 감지 알고리즘

### 핸드 시작 감지
```python
class HandStartDetector:
    def __init__(self):
        self.dealing_template = None  # 딜링 모션 템플릿
        self.card_positions = []      # 플레이어 카드 위치
        
    def detect_hand_start(self, frames):
        indicators = []
        
        # 1. 딜링 모션 감지
        dealing_motion = self.detect_dealing_motion(frames)
        indicators.append(('dealing_motion', dealing_motion))
        
        # 2. 새로운 카드 출현
        new_cards = self.detect_new_cards(frames)
        indicators.append(('new_cards', new_cards))
        
        # 3. UI 변화 (새 핸드 표시)
        ui_reset = self.detect_ui_reset(frames)
        indicators.append(('ui_reset', ui_reset))
        
        # 4. 시간적 패턴 (이전 핸드 종료 후 일정 시간)
        time_pattern = self.check_time_pattern()
        indicators.append(('time_pattern', time_pattern))
        
        return self.combine_indicators(indicators)
```

### 핸드 종료 감지
```python
class HandEndDetector:
    def __init__(self):
        self.pot_template = None      # 팟 영역 템플릿
        self.fold_indicators = []     # 폴드 표시 패턴
        
    def detect_hand_end(self, frames):
        indicators = []
        
        # 1. 팟 수집 모션
        pot_collection = self.detect_pot_collection(frames)
        indicators.append(('pot_collection', pot_collection))
        
        # 2. 모든 플레이어 폴드
        all_folded = self.detect_all_fold(frames)
        indicators.append(('all_folded', all_folded))
        
        # 3. 승부 결정 (카드 공개)
        showdown = self.detect_showdown(frames)
        indicators.append(('showdown', showdown))
        
        # 4. UI 정리 (베팅 정보 초기화)
        ui_cleanup = self.detect_ui_cleanup(frames)
        indicators.append(('ui_cleanup', ui_cleanup))
        
        return self.combine_indicators(indicators)
```

## 3. 구현 우선순위

### Phase 1: 기본 모션 감지 (1주)
- 프레임 차분을 통한 기본 변화 감지
- 카드 딜링 타이밍 대략적 감지
- 간단한 임계값 기반 핸드 분할

### Phase 2: 객체 감지 강화 (2주)
- OpenCV Haar Cascade로 카드/칩 감지
- 색상 기반 객체 분류
- ROI(Region of Interest) 설정으로 성능 최적화

### Phase 3: 템플릿 매칭 추가 (1주)
- 방송사별 UI 템플릿 생성
- 딜러 버튼, 카드 뒷면 등 고정 요소 추적
- 정확도 향상을 위한 다중 템플릿 매칭

### Phase 4: 시간적 패턴 분석 (1주)
- 핸드 간 평균 시간 간격 학습
- 비정상적으로 짧거나 긴 핸드 필터링
- 시계열 데이터를 통한 패턴 인식

## 4. 데이터 구조 설계

### 핸드 정보 클래스
```python
@dataclass
class HandInfo:
    hand_id: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    confidence_score: float
    detection_method: str
    key_events: List[Dict]
    
    def to_dict(self):
        return {
            "hand_id": self.hand_id,
            "start_time_s": self.start_time,
            "end_time_s": self.end_time,
            "confidence": self.confidence_score,
            "method": self.detection_method,
            "events": self.key_events
        }
```

### 감지 결과 검증
```python
class HandDetectionValidator:
    def __init__(self):
        self.min_hand_duration = 30  # 최소 30초
        self.max_hand_duration = 600  # 최대 10분
        
    def validate_hands(self, hands: List[HandInfo]) -> List[HandInfo]:
        valid_hands = []
        
        for hand in hands:
            # 시간 길이 검증
            if not self.is_valid_duration(hand):
                continue
                
            # 연속성 검증 (겹치지 않는지)
            if not self.is_continuous(hand, valid_hands):
                continue
                
            # 신뢰도 검증
            if hand.confidence_score < 0.7:
                continue
                
            valid_hands.append(hand)
            
        return valid_hands
```

## 5. 테스트 및 검증 전략

### 테스트 데이터셋
- 다양한 포커 방송사 영상 (10시간 분량)
- 수동 라벨링된 정답 데이터
- 다양한 카메라 각도 및 화질

### 성능 메트릭
- **정확도**: 올바르게 감지된 핸드 / 전체 핸드
- **재현율**: 감지된 핸드 / 실제 핸드 수
- **정밀도**: 올바른 감지 / 전체 감지 수
- **시간 오차**: 실제 시작/종료 시점과의 차이

### 최적화 목표
- 정확도 90% 이상
- 시간 오차 ±5초 이내
- 실시간 처리 가능 (1x 속도)

## 6. 확장성 및 적응성

### 방송사별 적응
```python
class BroadcastAdapter:
    def __init__(self, broadcast_type):
        self.templates = self.load_templates(broadcast_type)
        self.roi_settings = self.load_roi_settings(broadcast_type)
        
    def adapt_detector(self, detector):
        """방송사별 설정으로 감지기 조정"""
        detector.set_templates(self.templates)
        detector.set_roi(self.roi_settings)
        return detector
```

### 학습 기반 개선
```python
class AdaptiveLearning:
    def __init__(self):
        self.feedback_data = []
        
    def learn_from_feedback(self, detected_hands, ground_truth):
        """사용자 피드백을 통한 지속적 개선"""
        # 오탐/미탐 패턴 분석
        # 임계값 자동 조정
        # 새로운 패턴 학습
```

이 계획을 통해 단계별로 정확하고 안정적인 핸드 감지 시스템을 구축할 수 있습니다.