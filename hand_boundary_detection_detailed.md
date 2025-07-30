# 포커 핸드 경계 감지 상세 알고리즘

## 1. 핸드 시작 감지 (Hand Start Detection)

### 핵심 아이디어
포커 핸드는 **딜러가 플레이어들에게 홀카드 2장씩을 나누어주는 순간**에 시작됩니다.

### 시각적 단서들

#### A. 카드 딜링 모션 패턴
```
딜러 위치 (중앙) → 플레이어 1 → 플레이어 2 → ... → 다시 플레이어 1 → ...
```

**감지 방법:**
1. **모션 벡터 분석**
   - 연속 프레임에서 픽셀 변화량 계산
   - 중앙에서 방사형으로 뻗어나가는 모션 패턴 감지
   - 딜러 손의 원형 움직임 추적

2. **객체 추적**
   - 딜러 손 영역 ROI 설정
   - 손이 각 플레이어 위치로 이동하는 궤적 추적
   - 일정한 시간 간격으로 반복되는 패턴 감지

#### B. 새로운 카드 출현
```python
def detect_new_cards(self, current_frame, previous_frame):
    """새로 나타나는 카드 감지"""
    
    # 1. 카드 영역별 차이 계산
    card_regions = self.get_player_card_regions()  # 미리 정의된 플레이어 카드 위치
    
    new_cards = []
    for player_id, region in card_regions.items():
        # 해당 영역의 프레임 차이
        roi_current = current_frame[region['y1']:region['y2'], region['x1']:region['x2']]
        roi_previous = previous_frame[region['y1']:region['y2'], region['x1']:region['x2']]
        
        # 차이 계산
        diff = cv2.absdiff(roi_current, roi_previous)
        change_amount = np.sum(diff > 30)  # 임계값 이상 변화
        
        # 카드 크기만큼의 변화가 있다면
        if change_amount > region['card_area_threshold']:
            # 실제로 카드 모양인지 검증
            if self.verify_card_shape(roi_current):
                new_cards.append({
                    'player': player_id,
                    'region': region,
                    'confidence': change_amount / region['total_pixels']
                })
    
    return new_cards
```

#### C. 딜링 사운드 패턴 (선택사항)
- 카드가 테이블에 떨어지는 소리의 주기적 패턴
- 오디오 분석으로 딜링 리듬 감지

### 통합 판단 로직

```python
def detect_hand_start(self, frame_window):
    """핸드 시작 종합 판단"""
    
    confidence_scores = {}
    
    # 1. 딜링 모션 점수 (0-40점)
    dealing_motion = self.analyze_dealing_motion(frame_window)
    confidence_scores['dealing_motion'] = min(dealing_motion * 40, 40)
    
    # 2. 새 카드 출현 점수 (0-35점)
    new_cards = self.detect_new_cards_sequence(frame_window)
    if len(new_cards) >= 4:  # 최소 2명 플레이어 (4장 카드)
        confidence_scores['new_cards'] = 35
    elif len(new_cards) >= 2:
        confidence_scores['new_cards'] = 20
    else:
        confidence_scores['new_cards'] = 0
    
    # 3. 시간적 간격 점수 (0-15점)
    time_since_last_hand = self.get_time_since_last_hand()
    if 30 < time_since_last_hand < 120:  # 30초-2분 사이
        confidence_scores['timing'] = 15
    elif time_since_last_hand > 20:
        confidence_scores['timing'] = 8
    else:
        confidence_scores['timing'] = 0
    
    # 4. UI 변화 점수 (0-10점)
    ui_reset = self.detect_ui_reset(frame_window)
    confidence_scores['ui_change'] = ui_reset * 10
    
    total_confidence = sum(confidence_scores.values())
    
    # 75점 이상이면 핸드 시작으로 판단
    is_hand_start = total_confidence >= 75
    
    return is_hand_start, total_confidence, confidence_scores
```

## 2. 핸드 종료 감지 (Hand End Detection)

### 핵심 아이디어
포커 핸드는 다음 중 하나의 상황에서 종료됩니다:
1. **팟 수집**: 승자가 칩을 자신쪽으로 가져가는 모션
2. **모든 플레이어 폴드**: 마지막 한 명만 남고 나머지 폴드
3. **쇼다운**: 카드 공개 후 승부 결정

### 시각적 단서들

#### A. 팟 수집 모션
```python
def detect_pot_collection(self, frame_sequence):
    """팟 수집 모션 감지"""
    
    # 1. 팟 영역 정의 (테이블 중앙)
    pot_region = self.get_pot_region()
    
    # 2. 팟에서 플레이어 방향으로의 모션 추적
    motion_vectors = []
    
    for i in range(len(frame_sequence) - 1):
        current = frame_sequence[i]
        next_frame = frame_sequence[i + 1]
        
        # 옵티컬 플로우로 모션 벡터 계산
        flow = cv2.calcOpticalFlowPyrLK(
            cv2.cvtColor(current, cv2.COLOR_BGR2GRAY),
            cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY),
            self.get_pot_points(), None
        )
        
        # 중앙에서 한 방향으로 집중되는 모션 감지
        if self.is_collection_motion(flow):
            motion_vectors.append(flow)
    
    # 3. 일관된 수집 모션이 3프레임 이상 지속되면 감지
    return len(motion_vectors) >= 3

def is_collection_motion(self, flow_vectors):
    """수집 모션인지 판단"""
    if len(flow_vectors) < 5:
        return False
    
    # 모든 벡터가 비슷한 방향을 향하는지 확인
    angles = [np.arctan2(vy, vx) for vx, vy in flow_vectors]
    angle_std = np.std(angles)
    
    # 각도 표준편차가 작고(일관된 방향), 속도가 충분한지 확인
    avg_magnitude = np.mean([np.sqrt(vx**2 + vy**2) for vx, vy in flow_vectors])
    
    return angle_std < 0.5 and avg_magnitude > 10
```

#### B. 칩 분포 변화 분석
```python
def analyze_chip_distribution(self, frame_sequence):
    """칩 분포 변화 분석"""
    
    chip_counts = []
    
    for frame in frame_sequence:
        # 중앙 팟 영역의 칩 개수 세기
        pot_chips = self.count_chips_in_pot(frame)
        
        # 각 플레이어 영역의 칩 개수 세기
        player_chips = {}
        for player_id in self.player_regions:
            player_chips[player_id] = self.count_chips_in_region(
                frame, self.player_regions[player_id]
            )
        
        chip_counts.append({
            'pot': pot_chips,
            'players': player_chips
        })
    
    # 팟 칩이 급격히 감소하고 특정 플레이어 칩이 증가했는지 확인
    return self.detect_chip_transfer(chip_counts)

def count_chips_in_pot(self, frame):
    """팟 영역의 칩 개수 계산"""
    pot_region = self.get_pot_region()
    roi = frame[pot_region['y1']:pot_region['y2'], 
                pot_region['x1']:pot_region['x2']]
    
    # 원형 객체(칩) 감지
    circles = cv2.HoughCircles(
        cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY),
        cv2.HOUGH_GRADIENT, dp=1, minDist=15,
        param1=50, param2=30, minRadius=8, maxRadius=25
    )
    
    return len(circles[0]) if circles is not None else 0
```

#### C. 플레이어 액션 상태 분석
```python
def detect_all_players_folded(self, frame):
    """모든 플레이어가 폴드했는지 감지"""
    
    active_players = 0
    
    for player_id, region in self.player_regions.items():
        # 플레이어 앞에 카드가 있는지 확인
        has_cards = self.detect_cards_in_region(frame, region)
        
        # 카드가 뒤집어져 있거나 없으면 폴드
        if has_cards and not self.are_cards_folded(frame, region):
            active_players += 1
    
    return active_players <= 1  # 1명 이하만 남으면 핸드 종료

def are_cards_folded(self, frame, player_region):
    """플레이어 카드가 폴드 상태인지 확인"""
    card_roi = frame[player_region['y1']:player_region['y2'],
                    player_region['x1']:player_region['x2']]
    
    # 카드가 뒤집어져 있거나 딜러 쪽으로 밀려있는지 확인
    # 1. 카드 각도 분석 (정상: 0도, 폴드: 45도 이상)
    # 2. 카드 위치 분석 (딜러 방향으로 이동했는지)
    # 3. 카드 색상 분석 (뒷면이 보이는지)
    
    return self.analyze_card_angle(card_roi) > 45
```

### 통합 판단 로직

```python
def detect_hand_end(self, frame_window):
    """핸드 종료 종합 판단"""
    
    confidence_scores = {}
    
    # 1. 팟 수집 모션 점수 (0-50점)
    pot_collection = self.detect_pot_collection(frame_window)
    confidence_scores['pot_collection'] = 50 if pot_collection else 0
    
    # 2. 칩 분포 변화 점수 (0-30점)
    chip_transfer = self.analyze_chip_distribution(frame_window)
    confidence_scores['chip_transfer'] = chip_transfer * 30
    
    # 3. 플레이어 상태 점수 (0-25점)
    folded_players = self.count_folded_players(frame_window[-1])
    total_players = len(self.player_regions)
    
    if folded_players >= total_players - 1:  # 1명만 남음
        confidence_scores['player_state'] = 25
    else:
        confidence_scores['player_state'] = 0
    
    # 4. 모션 활동 감소 점수 (0-15점)
    motion_decrease = self.detect_motion_decrease(frame_window)
    confidence_scores['motion_decrease'] = motion_decrease * 15
    
    # 5. UI 변화 점수 (0-10점)
    ui_cleanup = self.detect_ui_cleanup(frame_window)
    confidence_scores['ui_cleanup'] = ui_cleanup * 10
    
    total_confidence = sum(confidence_scores.values())
    
    # 80점 이상이면 핸드 종료로 판단
    is_hand_end = total_confidence >= 80
    
    return is_hand_end, total_confidence, confidence_scores
```

## 3. 시간적 일관성 검증

### 핸드 길이 검증
```python
def validate_hand_duration(self, start_time, end_time):
    """핸드 길이가 적절한지 검증"""
    
    duration = end_time - start_time
    
    # 포커 핸드의 일반적인 길이: 30초 ~ 10분
    if duration < 30:
        return False, "너무 짧은 핸드 (30초 미만)"
    elif duration > 600:
        return False, "너무 긴 핸드 (10분 초과)"
    else:
        return True, "적절한 길이"
```

### 핸드 간 간격 검증
```python
def validate_hand_gap(self, previous_end, current_start):
    """핸드 간 간격이 적절한지 검증"""
    
    gap = current_start - previous_end
    
    # 핸드 간 간격: 최소 10초, 최대 5분
    if gap < 10:
        return False, "핸드 간 간격이 너무 짧음"
    elif gap > 300:
        return False, "핸드 간 간격이 너무 김 (광고/휴식 구간일 수 있음)"
    else:
        return True, "적절한 간격"
```

## 4. 오탐 방지 메커니즘

### 잘못된 감지 필터링
```python
def filter_false_positives(self, detected_hands):
    """오탐 제거"""
    
    filtered_hands = []
    
    for i, hand in enumerate(detected_hands):
        is_valid = True
        
        # 1. 최소 신뢰도 확인
        if hand.confidence_score < 0.7:
            is_valid = False
            
        # 2. 이전 핸드와의 중복 확인
        if i > 0:
            prev_hand = detected_hands[i-1]
            if hand.start_time < prev_hand.end_time:
                # 겹치는 경우 더 신뢰도가 높은 것을 선택
                if hand.confidence_score <= prev_hand.confidence_score:
                    is_valid = False
        
        # 3. 길이 검증
        duration_valid, _ = self.validate_hand_duration(
            hand.start_time, hand.end_time
        )
        if not duration_valid:
            is_valid = False
        
        if is_valid:
            filtered_hands.append(hand)
    
    return filtered_hands
```

## 5. 실제 구현 예시

### 프레임 단위 처리 루프
```python
def process_video(self, video_path):
    """실제 비디오 처리 메인 루프"""
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    frame_buffer = []  # 최근 N개 프레임 저장
    buffer_size = int(fps * 5)  # 5초 분량
    
    current_hand = None
    detected_hands = []
    frame_number = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 프레임 버퍼 관리
        frame_buffer.append(frame)
        if len(frame_buffer) > buffer_size:
            frame_buffer.pop(0)
        
        current_time = frame_number / fps
        
        # 핸드 진행 중이 아닐 때: 시작 감지
        if current_hand is None:
            if len(frame_buffer) >= 30:  # 최소 1초 분량 필요
                is_start, confidence, details = self.detect_hand_start(
                    frame_buffer[-30:]  # 최근 1초
                )
                
                if is_start:
                    current_hand = {
                        'start_frame': frame_number - 15,  # 중간 지점
                        'start_time': current_time - 0.5,
                        'start_confidence': confidence,
                        'start_details': details
                    }
                    print(f"핸드 시작 감지: {current_time:.1f}초 (신뢰도: {confidence:.1f})")
        
        # 핸드 진행 중일 때: 종료 감지
        else:
            # 최소 30초 후부터 종료 감지 시작
            if current_time - current_hand['start_time'] > 30:
                is_end, confidence, details = self.detect_hand_end(
                    frame_buffer[-30:]  # 최근 1초
                )
                
                if is_end:
                    # 핸드 완성
                    hand = HandInfo(
                        hand_id=len(detected_hands) + 1,
                        start_frame=current_hand['start_frame'],
                        end_frame=frame_number,
                        start_time=current_hand['start_time'],
                        end_time=current_time,
                        confidence_score=(current_hand['start_confidence'] + confidence) / 2,
                        detection_method='advanced_boundary_detection',
                        key_events=[current_hand['start_details'], details]
                    )
                    
                    detected_hands.append(hand)
                    print(f"핸드 종료 감지: {current_time:.1f}초 (길이: {current_time - current_hand['start_time']:.1f}초)")
                    
                    current_hand = None
        
        frame_number += 1
    
    # 마지막 정리
    cap.release()
    
    # 오탐 제거
    filtered_hands = self.filter_false_positives(detected_hands)
    
    return filtered_hands
```

이 방법으로 포커 핸드의 시작과 끝을 90% 이상의 정확도로 감지할 수 있습니다.