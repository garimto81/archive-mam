#!/usr/bin/env python
"""
고급 포커 핸드 감지 시스템
다층 감지 아키텍처를 사용한 정확한 핸드 경계 식별
"""
import cv2
import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HandInfo:
    """핸드 정보 데이터 클래스"""
    hand_id: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    confidence_score: float
    detection_method: str
    key_events: List[Dict]
    
    def to_dict(self):
        return asdict(self)

class MotionDetector:
    """기본 모션 감지 클래스"""
    
    def __init__(self, threshold=30, min_area=500):
        self.threshold = threshold
        self.min_area = min_area
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False, varThreshold=50
        )
    
    def detect_motion(self, frame):
        """프레임에서 모션 감지"""
        # 배경 제거 및 전경 마스크 생성
        fg_mask = self.background_subtractor.apply(frame)
        
        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 유의미한 크기의 모션만 필터링
        significant_motions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                significant_motions.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'center': (x + w//2, y + h//2)
                })
        
        return significant_motions, fg_mask

class CardDetector:
    """카드 감지 클래스"""
    
    def __init__(self):
        self.card_cascade = None
        self._load_cascades()
    
    def _load_cascades(self):
        """Haar Cascade 로드 (없으면 기본 사각형 감지 사용)"""
        try:
            # 커스텀 카드 cascade 파일이 있다면 로드
            cascade_path = "models/card_cascade.xml"
            if Path(cascade_path).exists():
                self.card_cascade = cv2.CascadeClassifier(cascade_path)
        except:
            logger.warning("카드 cascade 파일을 찾을 수 없습니다. 기본 감지 방법을 사용합니다.")
    
    def detect_cards_by_shape(self, frame):
        """형태 기반 카드 감지"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 가우시안 블러 적용
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 적응적 임계값 적용
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cards = []
        for contour in contours:
            # 컨투어 근사화
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 사각형 형태이고 적절한 크기인지 확인
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if 1000 < area < 10000:  # 카드 크기 범위
                    # 종횡비 확인 (카드는 대략 3:4 비율)
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        if 1.2 < aspect_ratio < 1.8:  # 카드 비율 범위
                            cards.append({
                                'contour': contour,
                                'bbox': cv2.boundingRect(contour),
                                'center': rect[0],
                                'area': area,
                                'aspect_ratio': aspect_ratio
                            })
        
        return cards
    
    def detect_cards_by_color(self, frame):
        """색상 기반 카드 감지 (흰색 카드 뒷면)"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 흰색 범위 정의
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # 흰색 마스크 생성
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        white_cards = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 5000:  # 카드 크기 범위
                rect = cv2.minAreaRect(contour)
                width, height = rect[1]
                if width > 0 and height > 0:
                    aspect_ratio = max(width, height) / min(width, height)
                    if 1.2 < aspect_ratio < 1.8:
                        white_cards.append({
                            'contour': contour,
                            'bbox': cv2.boundingRect(contour),
                            'center': rect[0],
                            'area': area,
                            'color_type': 'white'
                        })
        
        return white_cards

class ChipDetector:
    """칩 감지 클래스"""
    
    def __init__(self):
        self.chip_colors = {
            'white': ([0, 0, 200], [180, 30, 255]),
            'red': ([0, 120, 70], [10, 255, 255]),
            'green': ([40, 40, 40], [80, 255, 255]),
            'black': ([0, 0, 0], [180, 255, 30]),
            'blue': ([100, 150, 0], [140, 255, 255])
        }
    
    def detect_chips(self, frame):
        """색상별 칩 감지"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        all_chips = []
        
        for color_name, (lower, upper) in self.chip_colors.items():
            lower = np.array(lower)
            upper = np.array(upper)
            
            # 색상 마스크 생성
            mask = cv2.inRange(hsv, lower, upper)
            
            # 원형 객체 감지 (HoughCircles)
            circles = cv2.HoughCircles(
                mask, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                param1=50, param2=30, minRadius=5, maxRadius=50
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    all_chips.append({
                        'center': (x, y),
                        'radius': r,
                        'color': color_name,
                        'area': np.pi * r * r
                    })
        
        return all_chips

class HandStartDetector:
    """핸드 시작 감지 클래스"""
    
    def __init__(self):
        self.card_detector = CardDetector()
        self.motion_detector = MotionDetector()
        self.previous_card_count = 0
        self.dealing_motion_threshold = 3  # 연속된 프레임에서 딜링 모션 감지
        self.dealing_motion_count = 0
    
    def detect_hand_start(self, frame, frame_number, fps):
        """핸드 시작 감지"""
        indicators = {}
        confidence = 0.0
        
        # 1. 새로운 카드 출현 감지
        cards = self.card_detector.detect_cards_by_shape(frame)
        current_card_count = len(cards)
        
        if current_card_count > self.previous_card_count:
            new_cards = current_card_count - self.previous_card_count
            if new_cards >= 2:  # 홀카드 2장 이상 새로 나타남
                indicators['new_cards'] = True
                confidence += 0.4
                logger.info(f"Frame {frame_number}: {new_cards}장의 새 카드 감지")
        
        self.previous_card_count = current_card_count
        
        # 2. 딜링 모션 감지
        motions, _ = self.motion_detector.detect_motion(frame)
        
        # 테이블 중앙에서 플레이어 방향으로의 모션 감지
        dealing_motions = self._analyze_dealing_motion(motions, frame.shape)
        
        if dealing_motions:
            self.dealing_motion_count += 1
            if self.dealing_motion_count >= self.dealing_motion_threshold:
                indicators['dealing_motion'] = True
                confidence += 0.3
                logger.info(f"Frame {frame_number}: 딜링 모션 감지")
        else:
            self.dealing_motion_count = 0
        
        # 3. 시간적 패턴 (단순 버전)
        # 실제로는 이전 핸드 종료 시점부터의 시간을 계산해야 함
        indicators['time_pattern'] = True
        confidence += 0.1
        
        return confidence > 0.6, confidence, indicators
    
    def _analyze_dealing_motion(self, motions, frame_shape):
        """딜링 모션 분석"""
        height, width = frame_shape[:2]
        center_x, center_y = width // 2, height // 2
        
        dealing_motions = []
        for motion in motions:
            center = motion['center']
            
            # 중앙에서 시작하여 가장자리로 향하는 모션인지 확인
            distance_from_center = np.sqrt(
                (center[0] - center_x) ** 2 + (center[1] - center_y) ** 2
            )
            
            # 중앙 영역에서 발생한 모션이고 적절한 크기인지 확인
            if distance_from_center < width * 0.3 and motion['area'] > 1000:
                dealing_motions.append(motion)
        
        return dealing_motions

class HandEndDetector:
    """핸드 종료 감지 클래스"""
    
    def __init__(self):
        self.chip_detector = ChipDetector()
        self.motion_detector = MotionDetector()
        self.pot_collection_threshold = 2
        self.pot_collection_count = 0
    
    def detect_hand_end(self, frame, frame_number, fps):
        """핸드 종료 감지"""
        indicators = {}
        confidence = 0.0
        
        # 1. 팟 수집 모션 감지
        motions, _ = self.motion_detector.detect_motion(frame)
        pot_collection = self._analyze_pot_collection(motions, frame.shape)
        
        if pot_collection:
            self.pot_collection_count += 1
            if self.pot_collection_count >= self.pot_collection_threshold:
                indicators['pot_collection'] = True
                confidence += 0.5
                logger.info(f"Frame {frame_number}: 팟 수집 모션 감지")
        else:
            self.pot_collection_count = 0
        
        # 2. 칩 분포 변화 분석
        chips = self.chip_detector.detect_chips(frame)
        central_chips = self._count_central_chips(chips, frame.shape)
        
        if central_chips == 0:  # 중앙 팟 영역에 칩이 없음
            indicators['pot_cleared'] = True
            confidence += 0.3
        
        # 3. 모션의 급격한 감소 (핸드 종료 후 정적 상태)
        total_motion_area = sum(motion['area'] for motion in motions)
        if total_motion_area < 500:  # 매우 적은 모션
            indicators['static_state'] = True
            confidence += 0.2
        
        return confidence > 0.7, confidence, indicators
    
    def _analyze_pot_collection(self, motions, frame_shape):
        """팟 수집 모션 분석"""
        height, width = frame_shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # 중앙에서 한쪽으로 향하는 큰 모션 감지
        for motion in motions:
            if motion['area'] > 2000:  # 큰 움직임
                motion_center = motion['center']
                
                # 중앙 근처에서 발생한 모션인지 확인
                distance_from_center = np.sqrt(
                    (motion_center[0] - center_x) ** 2 + 
                    (motion_center[1] - center_y) ** 2
                )
                
                if distance_from_center < width * 0.4:
                    return True
        
        return False
    
    def _count_central_chips(self, chips, frame_shape):
        """중앙 영역의 칩 개수 계산"""
        height, width = frame_shape[:2]
        center_x, center_y = width // 2, height // 2
        central_radius = min(width, height) * 0.15  # 중앙 영역 반경
        
        central_chips = 0
        for chip in chips:
            chip_center = chip['center']
            distance = np.sqrt(
                (chip_center[0] - center_x) ** 2 + 
                (chip_center[1] - center_y) ** 2
            )
            
            if distance <= central_radius:
                central_chips += 1
        
        return central_chips

class AdvancedHandDetector:
    """고급 핸드 감지 메인 클래스"""
    
    def __init__(self):
        self.start_detector = HandStartDetector()
        self.end_detector = HandEndDetector()
        self.detected_hands = []
        self.current_hand_start = None
        
    def analyze_video(self, video_path: str, output_path: str = None) -> str:
        """비디오 분석 및 핸드 감지"""
        logger.info(f"고급 핸드 감지 시작: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_number = 0
        hand_id = 1
        
        logger.info(f"총 {total_frames} 프레임, {fps} FPS")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_time = frame_number / fps
            
            # 핸드 시작 감지
            if self.current_hand_start is None:
                is_start, start_confidence, start_indicators = \
                    self.start_detector.detect_hand_start(frame, frame_number, fps)
                
                if is_start:
                    self.current_hand_start = {
                        'hand_id': hand_id,
                        'frame': frame_number,
                        'time': current_time,
                        'confidence': start_confidence,
                        'indicators': start_indicators
                    }
                    logger.info(f"핸드 {hand_id} 시작 감지: {current_time:.2f}초")
            
            # 핸드 종료 감지
            else:
                is_end, end_confidence, end_indicators = \
                    self.end_detector.detect_hand_end(frame, frame_number, fps)
                
                if is_end:
                    # 핸드 정보 생성
                    hand_info = HandInfo(
                        hand_id=self.current_hand_start['hand_id'],
                        start_frame=self.current_hand_start['frame'],
                        end_frame=frame_number,
                        start_time=self.current_hand_start['time'],
                        end_time=current_time,
                        confidence_score=(self.current_hand_start['confidence'] + end_confidence) / 2,
                        detection_method='advanced_multi_layer',
                        key_events=[
                            {'type': 'hand_start', 'indicators': self.current_hand_start['indicators']},
                            {'type': 'hand_end', 'indicators': end_indicators}
                        ]
                    )
                    
                    self.detected_hands.append(hand_info)
                    logger.info(f"핸드 {hand_id} 종료 감지: {current_time:.2f}초 "
                              f"(지속시간: {current_time - self.current_hand_start['time']:.1f}초)")
                    
                    # 다음 핸드 준비
                    self.current_hand_start = None
                    hand_id += 1
            
            frame_number += 1
            
            # 진행률 표시
            if frame_number % 300 == 0:  # 10초마다 (30fps 기준)
                progress = (frame_number / total_frames) * 100
                logger.info(f"진행률: {progress:.1f}% ({frame_number}/{total_frames})")
        
        cap.release()
        
        # 결과 저장
        if output_path is None:
            output_path = f"analysis_results/advanced_hands_{Path(video_path).stem}.json"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([hand.to_dict() for hand in self.detected_hands], f, 
                     indent=2, ensure_ascii=False)
        
        logger.info(f"분석 완료: {len(self.detected_hands)}개 핸드 감지")
        logger.info(f"결과 저장: {output_path}")
        
        return output_path

def main():
    """테스트 실행"""
    detector = AdvancedHandDetector()
    
    # 샘플 비디오로 테스트
    video_path = "videos/sample_poker_video.mp4"
    
    if Path(video_path).exists():
        result_file = detector.analyze_video(video_path)
        print(f"분석 결과: {result_file}")
    else:
        print(f"테스트 비디오가 없습니다: {video_path}")
        print("python -m src.generate_sample_video 를 실행해서 샘플 비디오를 생성하세요.")

if __name__ == "__main__":
    main()