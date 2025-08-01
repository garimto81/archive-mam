"""
핸드 분리 알고리즘 상세 구현
UI 감지 결과를 바탕으로 포커 핸드를 정확히 분리
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class UISegment:
    start: float
    end: float
    confidence: float
    ui_type: str  # 'stats', 'break', 'ad', etc.

@dataclass
class PokerHand:
    hand_id: int
    start_time: float
    end_time: float
    duration: float
    confidence: float
    validation_status: str
    
class HandSeparationAlgorithm:
    """정교한 핸드 분리 알고리즘"""
    
    def __init__(self):
        self.ui_buffer_before = 15.0  # UI 시작 전 버퍼
        self.ui_buffer_after = 15.0   # UI 종료 후 버퍼
        self.min_hand_duration = 30.0  # 최소 핸드 길이
        self.max_hand_duration = 600.0 # 최대 핸드 길이 (10분)
        
    def separate_hands(self, ui_segments: List[UISegment], 
                      video_duration: float) -> List[PokerHand]:
        """
        메인 핸드 분리 알고리즘
        
        핵심 규칙:
        1. UI가 15초 이상 지속되면 유효한 UI 세그먼트
        2. UI 시작 15초 전 = 이전 핸드 종료
        3. UI 종료 15초 후 = 다음 핸드 시작
        """
        
        # 1단계: UI 세그먼트 전처리
        valid_ui_segments = self._preprocess_ui_segments(ui_segments)
        
        # 2단계: 핸드 경계 생성
        hand_boundaries = self._generate_hand_boundaries(
            valid_ui_segments, video_duration
        )
        
        # 3단계: 핸드 검증
        validated_hands = self._validate_hands(hand_boundaries)
        
        # 4단계: 후처리
        final_hands = self._post_process_hands(validated_hands)
        
        return final_hands
    
    def _preprocess_ui_segments(self, segments: List[UISegment]) -> List[UISegment]:
        """UI 세그먼트 전처리 - 병합 및 필터링"""
        if not segments:
            return []
        
        # 시간순 정렬
        segments.sort(key=lambda x: x.start)
        
        # 인접한 UI 병합 (5초 이내)
        merged = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            if next_seg.start - current.end < 5.0:
                # 병합
                current = UISegment(
                    start=current.start,
                    end=next_seg.end,
                    confidence=max(current.confidence, next_seg.confidence),
                    ui_type=current.ui_type
                )
            else:
                merged.append(current)
                current = next_seg
        
        merged.append(current)
        
        # 15초 미만 UI 제거
        return [seg for seg in merged if seg.end - seg.start >= 15.0]
    
    def _generate_hand_boundaries(self, ui_segments: List[UISegment], 
                                 video_duration: float) -> List[Dict]:
        """UI 세그먼트로부터 핸드 경계 생성"""
        hands = []
        
        # 케이스 1: UI가 없는 경우 - 전체가 하나의 핸드
        if not ui_segments:
            return [{
                'start': 0,
                'end': video_duration,
                'confidence': 0.5,
                'source': 'no_ui'
            }]
        
        # 케이스 2: 첫 번째 핸드 (영상 시작 ~ 첫 UI)
        first_ui = ui_segments[0]
        first_hand_end = first_ui.start - self.ui_buffer_before
        
        if first_hand_end > self.min_hand_duration:
            hands.append({
                'start': 0,
                'end': first_hand_end,
                'confidence': 0.8,
                'source': 'before_first_ui'
            })
        
        # 케이스 3: 중간 핸드들 (UI 사이)
        for i in range(len(ui_segments) - 1):
            current_ui = ui_segments[i]
            next_ui = ui_segments[i + 1]
            
            # 핸드 시작 = 현재 UI 종료 + 15초
            hand_start = current_ui.end + self.ui_buffer_after
            # 핸드 종료 = 다음 UI 시작 - 15초
            hand_end = next_ui.start - self.ui_buffer_before
            
            # 유효성 검사
            if self._is_valid_hand_duration(hand_start, hand_end):
                confidence = self._calculate_hand_confidence(
                    current_ui, next_ui, hand_end - hand_start
                )
                
                hands.append({
                    'start': hand_start,
                    'end': hand_end,
                    'confidence': confidence,
                    'source': 'between_ui'
                })
        
        # 케이스 4: 마지막 핸드 (마지막 UI ~ 영상 끝)
        last_ui = ui_segments[-1]
        last_hand_start = last_ui.end + self.ui_buffer_after
        
        if video_duration - last_hand_start > self.min_hand_duration:
            hands.append({
                'start': last_hand_start,
                'end': video_duration,
                'confidence': 0.7,
                'source': 'after_last_ui'
            })
        
        return hands
    
    def _is_valid_hand_duration(self, start: float, end: float) -> bool:
        """핸드 길이 유효성 검사"""
        duration = end - start
        return self.min_hand_duration <= duration <= self.max_hand_duration
    
    def _calculate_hand_confidence(self, prev_ui: UISegment, 
                                 next_ui: UISegment, duration: float) -> float:
        """핸드 신뢰도 계산"""
        confidence = 0.5
        
        # UI 신뢰도 반영
        confidence += (prev_ui.confidence + next_ui.confidence) * 0.2
        
        # 핸드 길이에 따른 신뢰도
        if 60 <= duration <= 300:  # 1-5분 이상적
            confidence += 0.2
        elif 30 <= duration <= 60 or 300 <= duration <= 420:
            confidence += 0.1
        
        # UI 타입에 따른 가중치
        if prev_ui.ui_type == 'stats' and next_ui.ui_type == 'stats':
            confidence += 0.1  # 통계 화면 사이는 신뢰도 높음
        
        return min(confidence, 1.0)
    
    def _validate_hands(self, hand_boundaries: List[Dict]) -> List[PokerHand]:
        """핸드 검증 - 겹침, 갭 체크"""
        validated = []
        
        for i, boundary in enumerate(hand_boundaries):
            hand = PokerHand(
                hand_id=i + 1,
                start_time=boundary['start'],
                end_time=boundary['end'],
                duration=boundary['end'] - boundary['start'],
                confidence=boundary['confidence'],
                validation_status='pending'
            )
            
            # 검증 규칙들
            if hand.duration < self.min_hand_duration:
                hand.validation_status = 'too_short'
            elif hand.duration > self.max_hand_duration:
                hand.validation_status = 'too_long'
            else:
                hand.validation_status = 'valid'
            
            validated.append(hand)
        
        return validated
    
    def _post_process_hands(self, hands: List[PokerHand]) -> List[PokerHand]:
        """후처리 - 짧은 핸드 병합, 긴 핸드 분할"""
        processed = []
        
        i = 0
        while i < len(hands):
            current = hands[i]
            
            if current.validation_status == 'too_short' and i < len(hands) - 1:
                # 다음 핸드와 병합 시도
                next_hand = hands[i + 1]
                if self._can_merge_hands(current, next_hand):
                    merged = self._merge_hands(current, next_hand)
                    processed.append(merged)
                    i += 2
                    continue
            
            elif current.validation_status == 'too_long':
                # 긴 핸드 분할
                split_hands = self._split_long_hand(current)
                processed.extend(split_hands)
            
            elif current.validation_status == 'valid':
                processed.append(current)
            
            i += 1
        
        # ID 재할당
        for i, hand in enumerate(processed):
            hand.hand_id = i + 1
        
        return processed
    
    def _can_merge_hands(self, hand1: PokerHand, hand2: PokerHand) -> bool:
        """두 핸드 병합 가능 여부"""
        gap = hand2.start_time - hand1.end_time
        return gap < 30.0  # 30초 이내 갭
    
    def _merge_hands(self, hand1: PokerHand, hand2: PokerHand) -> PokerHand:
        """두 핸드 병합"""
        return PokerHand(
            hand_id=hand1.hand_id,
            start_time=hand1.start_time,
            end_time=hand2.end_time,
            duration=hand2.end_time - hand1.start_time,
            confidence=(hand1.confidence + hand2.confidence) / 2,
            validation_status='merged'
        )
    
    def _split_long_hand(self, hand: PokerHand) -> List[PokerHand]:
        """긴 핸드를 여러 개로 분할"""
        splits = []
        optimal_duration = 180.0  # 3분
        
        num_splits = int(hand.duration / optimal_duration) + 1
        split_duration = hand.duration / num_splits
        
        for i in range(num_splits):
            split = PokerHand(
                hand_id=hand.hand_id,
                start_time=hand.start_time + i * split_duration,
                end_time=hand.start_time + (i + 1) * split_duration,
                duration=split_duration,
                confidence=hand.confidence * 0.8,  # 분할로 인한 신뢰도 감소
                validation_status='split'
            )
            splits.append(split)
        
        return splits
    
    def generate_hand_report(self, hands: List[PokerHand]) -> Dict:
        """핸드 분리 결과 리포트"""
        return {
            'total_hands': len(hands),
            'valid_hands': len([h for h in hands if h.validation_status == 'valid']),
            'merged_hands': len([h for h in hands if h.validation_status == 'merged']),
            'split_hands': len([h for h in hands if h.validation_status == 'split']),
            'average_duration': np.mean([h.duration for h in hands]),
            'total_duration': sum(h.duration for h in hands),
            'average_confidence': np.mean([h.confidence for h in hands])
        }