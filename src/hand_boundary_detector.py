#!/usr/bin/env python
"""
포커 핸드 경계 감지 시스템 - 핵심 구현
정확한 핸드 시작/종료 지점을 감지하는 고급 알고리즘
"""
import cv2
import numpy as np
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import time
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DetectionEvent:
    """감지 이벤트 데이터 클래스"""
    event_type: str  # 'hand_start' or 'hand_end'
    frame_number: int
    timestamp: float
    confidence: float
    indicators: Dict[str, Any]
    details: Dict[str, Any]

@dataclass
class HandBoundary:
    """핸드 경계 정보"""
    hand_id: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    duration: float
    start_confidence: float
    end_confidence: float
    overall_confidence: float
    start_indicators: Dict[str, Any]
    end_indicators: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)

class MotionTracker:
    """고급 모션 추적 시스템"""
    
    def __init__(self):
        # 배경 제거기 초기화
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=50,
            history=500
        )
        
        # 옵티컬 플로우 파라미터
        self.lk_params = {
            'winSize': (15, 15),
            'maxLevel': 2,
            'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        }
        
        # 추적점 저장
        self.tracking_points = None
        self.previous_gray = None
        
        # 모션 히스토리
        self.motion_history = deque(maxlen=30)  # 1초 분량 (30fps 기준)
    
    def update(self, frame):
        """프레임 업데이트 및 모션 분석"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 배경 제거로 전경 마스크 생성
        fg_mask = self.bg_subtractor.apply(frame)
        
        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # 모션 영역 찾기
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 최소 영역 필터
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append({
                    'bbox': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'area': area,
                    'contour': contour
                })
        
        # 옵티컬 플로우 계산
        flow_vectors = None
        if self.previous_gray is not None:
            # 전체 프레임에 대한 dense optical flow
            flow = cv2.calcOpticalFlowPyrLK(
                self.previous_gray, gray, 
                np.array([[x, y] for x in range(0, gray.shape[1], 20) 
                         for y in range(0, gray.shape[0], 20)], dtype=np.float32), 
                None, **self.lk_params
            )
            
            if flow[0] is not None:
                good_points = flow[0][flow[1].ravel() == 1]
                flow_vectors = flow[0] - np.array([[x, y] for x in range(0, gray.shape[1], 20) 
                                                  for y in range(0, gray.shape[0], 20)], dtype=np.float32)
        
        # 모션 정보 업데이트
        motion_info = {
            'timestamp': time.time(),
            'motion_regions': motion_regions,
            'flow_vectors': flow_vectors,
            'total_motion_area': sum(region['area'] for region in motion_regions),
            'fg_mask': fg_mask
        }
        
        self.motion_history.append(motion_info)
        self.previous_gray = gray.copy()
        
        return motion_info
    
    def analyze_motion_pattern(self, pattern_type='dealing'):
        """특정 모션 패턴 분석"""
        if len(self.motion_history) < 10:
            return 0.0
            
        if pattern_type == 'dealing':
            return self._analyze_dealing_motion()
        elif pattern_type == 'collection':
            return self._analyze_collection_motion()
        else:
            return 0.0
    
    def _analyze_dealing_motion(self):
        """딜링 모션 패턴 분석"""
        # 최근 1초간의 모션 데이터 분석
        recent_motions = list(self.motion_history)[-30:]
        
        if len(recent_motions) < 15:
            return 0.0
        
        # 중앙에서 방사형으로 뻗어나가는 패턴 감지
        center_motions = 0
        radial_motions = 0
        
        frame_height, frame_width = 720, 1280  # 기본값, 실제로는 동적으로 설정
        center_x, center_y = frame_width // 2, frame_height // 2
        
        for motion in recent_motions:
            for region in motion['motion_regions']:
                region_center = region['center']
                distance_from_center = np.sqrt(
                    (region_center[0] - center_x) ** 2 + 
                    (region_center[1] - center_y) ** 2
                )
                
                # 중앙 근처에서 시작하는 모션
                if distance_from_center < frame_width * 0.3:
                    center_motions += 1
                # 가장자리로 향하는 모션
                elif distance_from_center > frame_width * 0.3:
                    radial_motions += 1
        
        # 딜링 패턴 점수 계산
        if center_motions == 0:
            return 0.0
            
        dealing_score = min((radial_motions / center_motions) * 0.5, 1.0)
        return dealing_score
    
    def _analyze_collection_motion(self):
        """팟 수집 모션 패턴 분석"""
        recent_motions = list(self.motion_history)[-15:]
        
        if len(recent_motions) < 10:
            return 0.0
        
        # 중앙에서 한 방향으로의 일관된 움직임 감지
        motion_vectors = []
        for motion in recent_motions:
            if motion['flow_vectors'] is not None:
                # 중앙 영역의 플로우 벡터만 추출
                central_vectors = self._extract_central_vectors(motion['flow_vectors'])
                motion_vectors.extend(central_vectors)
        
        if len(motion_vectors) < 5:
            return 0.0
        
        # 벡터들의 일관성 검사
        angles = [np.arctan2(v[1], v[0]) for v in motion_vectors if np.linalg.norm(v) > 2]
        
        if len(angles) < 3:
            return 0.0
        
        # 각도의 표준편차가 작을수록 일관된 방향
        angle_std = np.std(angles)
        consistency_score = max(0, 1 - angle_std / np.pi)
        
        # 속도의 평균이 충분한지 확인
        velocities = [np.linalg.norm(v) for v in motion_vectors]
        avg_velocity = np.mean(velocities)
        velocity_score = min(avg_velocity / 10, 1.0)
        
        collection_score = (consistency_score + velocity_score) / 2
        return collection_score
    
    def _extract_central_vectors(self, flow_vectors):
        """중앙 영역의 플로우 벡터 추출"""
        # 구현 세부사항은 실제 프레임 크기에 따라 조정
        return flow_vectors  # 단순화된 버전

class ObjectDetector:
    """포커 객체 감지 시스템 (카드, 칩)"""
    
    def __init__(self):
        # 카드 감지 파라미터
        self.card_size_range = (800, 8000)  # 픽셀 영역
        self.card_aspect_ratio_range = (1.2, 1.8)
        
        # 칩 감지 파라미터
        self.chip_colors = {
            'white': ([0, 0, 180], [180, 30, 255]),
            'red': ([0, 100, 100], [10, 255, 255]),
            'green': ([40, 50, 50], [80, 255, 255]),
            'blue': ([100, 100, 100], [130, 255, 255]),
            'black': ([0, 0, 0], [180, 50, 50])
        }
        
        # ROI 설정 (실제로는 비디오별로 설정)
        self.player_regions = {}
        self.pot_region = None
        self.dealer_region = None
    
    def detect_cards(self, frame):
        """카드 감지"""
        cards = []
        
        # 형태 기반 감지
        shape_cards = self._detect_cards_by_shape(frame)
        cards.extend(shape_cards)
        
        # 색상 기반 감지
        color_cards = self._detect_cards_by_color(frame)
        cards.extend(color_cards)
        
        # 중복 제거 및 검증
        verified_cards = self._verify_and_merge_cards(cards)
        
        return verified_cards
    
    def _detect_cards_by_shape(self, frame):
        """형태 기반 카드 감지"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cards = []
        for contour in contours:
            # 컨투어 근사화
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 사각형 형태 확인
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if self.card_size_range[0] < area < self.card_size_range[1]:
                    # 종횡비 확인
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        if self.card_aspect_ratio_range[0] < aspect_ratio < self.card_aspect_ratio_range[1]:
                            cards.append({
                                'type': 'shape_detected',
                                'contour': contour,
                                'bbox': cv2.boundingRect(contour),
                                'center': rect[0],
                                'area': area,
                                'aspect_ratio': aspect_ratio,
                                'confidence': 0.7
                            })
        
        return cards
    
    def _detect_cards_by_color(self, frame):
        """색상 기반 카드 감지 (흰색 카드 뒷면)"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 흰색 범위
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cards = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.card_size_range[0] * 0.5 < area < self.card_size_range[1]:
                rect = cv2.minAreaRect(contour)
                width, height = rect[1]
                if width > 0 and height > 0:
                    aspect_ratio = max(width, height) / min(width, height)
                    if self.card_aspect_ratio_range[0] < aspect_ratio < self.card_aspect_ratio_range[1]:
                        cards.append({
                            'type': 'color_detected',
                            'contour': contour,
                            'bbox': cv2.boundingRect(contour),
                            'center': rect[0],
                            'area': area,
                            'color': 'white',
                            'confidence': 0.6
                        })
        
        return cards
    
    def _verify_and_merge_cards(self, cards):
        """카드 검증 및 중복 제거"""
        verified_cards = []
        
        # 중복 제거 (같은 위치의 카드들)
        merged_cards = []
        for card in cards:
            is_duplicate = False
            for existing in merged_cards:
                # 중심점 거리로 중복 판단
                dist = np.sqrt(
                    (card['center'][0] - existing['center'][0])**2 + 
                    (card['center'][1] - existing['center'][1])**2
                )
                if dist < 50:  # 50픽셀 이내면 같은 카드
                    # 더 높은 신뢰도로 업데이트
                    if card['confidence'] > existing['confidence']:
                        existing.update(card)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged_cards.append(card)
        
        return merged_cards
    
    def detect_chips(self, frame):
        """칩 감지"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        all_chips = []
        
        for color_name, (lower, upper) in self.chip_colors.items():
            lower = np.array(lower)
            upper = np.array(upper)
            
            mask = cv2.inRange(hsv, lower, upper)
            
            # HoughCircles로 원형 객체 감지
            circles = cv2.HoughCircles(
                mask, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                param1=50, param2=30, minRadius=8, maxRadius=40
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    all_chips.append({
                        'center': (x, y),
                        'radius': r,
                        'color': color_name,
                        'area': np.pi * r * r,
                        'confidence': 0.8
                    })
        
        return all_chips
    
    def set_regions(self, frame_shape):
        """ROI 영역 설정"""
        height, width = frame_shape[:2]
        
        # 기본 영역 설정 (실제로는 더 정교하게 설정)
        self.pot_region = {
            'x1': int(width * 0.4), 'y1': int(height * 0.4),
            'x2': int(width * 0.6), 'y2': int(height * 0.6)
        }
        
        # 플레이어 영역 (6인 테이블 기준)
        self.player_regions = {
            1: {'x1': int(width * 0.1), 'y1': int(height * 0.7), 
                'x2': int(width * 0.3), 'y2': int(height * 0.9)},
            2: {'x1': int(width * 0.05), 'y1': int(height * 0.4), 
                'x2': int(width * 0.25), 'y2': int(height * 0.6)},
            3: {'x1': int(width * 0.1), 'y1': int(height * 0.1), 
                'x2': int(width * 0.3), 'y2': int(height * 0.3)},
            4: {'x1': int(width * 0.7), 'y1': int(height * 0.1), 
                'x2': int(width * 0.9), 'y2': int(height * 0.3)},
            5: {'x1': int(width * 0.75), 'y1': int(height * 0.4), 
                'x2': int(width * 0.95), 'y2': int(height * 0.6)},
            6: {'x1': int(width * 0.7), 'y1': int(height * 0.7), 
                'x2': int(width * 0.9), 'y2': int(height * 0.9)}
        }

class HandBoundaryDetector:
    """핸드 경계 감지 메인 클래스"""
    
    def __init__(self):
        self.motion_tracker = MotionTracker()
        self.object_detector = ObjectDetector()
        
        # 상태 관리
        self.current_hand_start = None
        self.detected_hands = []
        self.frame_count = 0
        self.fps = 30
        
        # 감지 임계값
        self.start_threshold = 75
        self.end_threshold = 80
        
        # 카드 추적
        self.previous_card_count = 0
        self.card_count_history = deque(maxlen=10)
        
        # 모션 상태 추적
        self.dealing_motion_count = 0
        self.collection_motion_count = 0
        
    def analyze_video(self, video_path: str, output_path: str = None, progress_callback=None) -> str:
        """비디오 분석 메인 함수 (파일 경로 기반)"""
        logger.info(f"핸드 경계 감지 시작: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오를 열 수 없습니다: {video_path}")
        
        return self._analyze_video_capture(cap, output_path, progress_callback, source_info={'type': 'file', 'path': video_path})
    
    def analyze_stream(self, video_capture: cv2.VideoCapture, source_info: dict, output_path: str = None, progress_callback=None) -> str:
        """비디오 스트림 분석 메인 함수 (VideoCapture 객체 기반)"""
        logger.info(f"스트림 분석 시작: {source_info.get('title', 'Unknown')}")
        
        if not video_capture.isOpened():
            raise ValueError("비디오 스트림이 열려있지 않습니다")
        
        return self._analyze_video_capture(video_capture, output_path, progress_callback, source_info)
    
    def _analyze_video_capture(self, cap: cv2.VideoCapture, output_path: str = None, progress_callback=None, source_info: dict = None) -> str:
        """VideoCapture 객체를 이용한 실제 분석 로직"""
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 첫 번째 프레임으로 ROI 설정
        ret, first_frame = cap.read()
        if ret:
            self.object_detector.set_regions(first_frame.shape)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 처음으로 되돌리기
        
        # 스트리밍의 경우 총 프레임 수를 모를 수 있음
        if total_frames <= 0:
            total_frames = None
            logger.info(f"스트리밍 분석 시작, {self.fps} FPS")
        else:
            logger.info(f"총 {total_frames} 프레임, {self.fps} FPS")
        
        hand_id = 1
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_time = self.frame_count / self.fps
            
            # 진행률 콜백 호출
            if progress_callback and self.frame_count % 30 == 0:  # 1초마다
                progress_info = {
                    'current_frame': self.frame_count,
                    'total_frames': total_frames,
                    'current_time': current_time,
                    'detected_hands': len(self.detected_hands),
                    'source_info': source_info
                }
                
                if total_frames:
                    progress_info['progress_percent'] = (self.frame_count / total_frames) * 100
                else:
                    progress_info['progress_percent'] = 0
                
                try:
                    progress_callback(progress_info)
                except Exception as e:
                    logger.warning(f"진행률 콜백 오류: {e}")
            
            # 모션 추적 업데이트
            motion_info = self.motion_tracker.update(frame)
            
            # 핸드 시작 감지
            if self.current_hand_start is None:
                is_start, confidence, indicators = self._detect_hand_start(
                    frame, motion_info, current_time
                )
                
                if is_start:
                    self.current_hand_start = DetectionEvent(
                        event_type='hand_start',
                        frame_number=self.frame_count,
                        timestamp=current_time,
                        confidence=confidence,
                        indicators=indicators,
                        details={'hand_id': hand_id}
                    )
                    logger.info(f"핸드 {hand_id} 시작 감지: {current_time:.2f}초 (신뢰도: {confidence:.1f})")
            
            # 핸드 종료 감지
            else:
                # 최소 30초 후부터 종료 감지
                if current_time - self.current_hand_start.timestamp > 30:
                    is_end, confidence, indicators = self._detect_hand_end(
                        frame, motion_info, current_time
                    )
                    
                    if is_end:
                        # 핸드 완성
                        duration = current_time - self.current_hand_start.timestamp
                        overall_confidence = (self.current_hand_start.confidence + confidence) / 2
                        
                        hand_boundary = HandBoundary(
                            hand_id=hand_id,
                            start_frame=self.current_hand_start.frame_number,
                            end_frame=self.frame_count,
                            start_time=self.current_hand_start.timestamp,
                            end_time=current_time,
                            duration=duration,
                            start_confidence=self.current_hand_start.confidence,
                            end_confidence=confidence,
                            overall_confidence=overall_confidence,
                            start_indicators=self.current_hand_start.indicators,
                            end_indicators=indicators
                        )
                        
                        self.detected_hands.append(hand_boundary)
                        logger.info(f"핸드 {hand_id} 종료 감지: {current_time:.2f}초 "
                                  f"(지속시간: {duration:.1f}초, 신뢰도: {overall_confidence:.1f})")
                        
                        # 다음 핸드 준비
                        self.current_hand_start = None
                        hand_id += 1
            
            self.frame_count += 1
            
            # 진행률 표시
            if self.frame_count % 900 == 0:  # 30초마다
                progress = (self.frame_count / total_frames) * 100
                logger.info(f"진행률: {progress:.1f}% ({self.frame_count}/{total_frames})")
        
        cap.release()
        
        # 결과 후처리 및 저장
        validated_hands = self._validate_hands(self.detected_hands)
        
        if output_path is None:
            # 소스 정보에 따라 파일명 결정
            if source_info and source_info.get('type') == 'stream':
                filename = f"stream_analysis_{int(time.time())}.json"
            else:
                source_name = source_info.get('title', 'unknown') if source_info else 'unknown'
                # 파일명에 사용할 수 없는 문자 제거
                safe_name = "".join(c for c in source_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"hand_boundaries_{safe_name}.json"
            
            output_path = f"analysis_results/{filename}"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([hand.to_dict() for hand in validated_hands], f, 
                     indent=2, ensure_ascii=False)
        
        logger.info(f"분석 완료: {len(validated_hands)}개 핸드 감지")
        logger.info(f"결과 저장: {output_path}")
        
        return output_path
    
    def _detect_hand_start(self, frame, motion_info, current_time):
        """핸드 시작 감지"""
        indicators = {}
        confidence_scores = {}
        
        # 1. 새로운 카드 출현 감지 (35점)
        cards = self.object_detector.detect_cards(frame)
        current_card_count = len(cards)
        self.card_count_history.append(current_card_count)
        
        if len(self.card_count_history) >= 5:
            avg_previous = np.mean(list(self.card_count_history)[:-1])
            if current_card_count > avg_previous + 2:  # 2장 이상 증가
                indicators['new_cards'] = True
                confidence_scores['new_cards'] = 35
                logger.debug(f"새 카드 감지: {current_card_count}장 (이전 평균: {avg_previous:.1f})")
            else:
                confidence_scores['new_cards'] = 0
        else:
            confidence_scores['new_cards'] = 0
        
        # 2. 딜링 모션 패턴 감지 (40점)
        dealing_score = self.motion_tracker.analyze_motion_pattern('dealing')
        if dealing_score > 0.6:
            self.dealing_motion_count += 1
        else:
            self.dealing_motion_count = max(0, self.dealing_motion_count - 1)
        
        if self.dealing_motion_count >= 3:  # 연속 3프레임 이상
            indicators['dealing_motion'] = True
            confidence_scores['dealing_motion'] = min(dealing_score * 40, 40)
        else:
            confidence_scores['dealing_motion'] = 0
        
        # 3. 시간적 패턴 (15점)
        time_since_last = self._get_time_since_last_hand(current_time)
        if 30 <= time_since_last <= 120:  # 30초-2분
            indicators['time_pattern'] = True
            confidence_scores['time_pattern'] = 15
        elif time_since_last >= 20:
            confidence_scores['time_pattern'] = 8
        else:
            confidence_scores['time_pattern'] = 0
        
        # 4. 모션 활동 증가 (10점)
        if motion_info['total_motion_area'] > 2000:
            indicators['increased_activity'] = True
            confidence_scores['increased_activity'] = 10
        else:
            confidence_scores['increased_activity'] = 0
        
        total_confidence = sum(confidence_scores.values())
        is_hand_start = total_confidence >= self.start_threshold
        
        return is_hand_start, total_confidence, {
            'indicators': indicators,
            'confidence_breakdown': confidence_scores,
            'card_count': current_card_count,
            'dealing_score': dealing_score,
            'motion_area': motion_info['total_motion_area']
        }
    
    def _detect_hand_end(self, frame, motion_info, current_time):
        """핸드 종료 감지"""
        indicators = {}
        confidence_scores = {}
        
        # 1. 팟 수집 모션 감지 (50점)
        collection_score = self.motion_tracker.analyze_motion_pattern('collection')
        if collection_score > 0.7:
            self.collection_motion_count += 1
        else:
            self.collection_motion_count = max(0, self.collection_motion_count - 1)
        
        if self.collection_motion_count >= 2:  # 연속 2프레임 이상
            indicators['pot_collection'] = True
            confidence_scores['pot_collection'] = min(collection_score * 50, 50)
        else:
            confidence_scores['pot_collection'] = 0
        
        # 2. 칩 분포 변화 (30점)
        chips = self.object_detector.detect_chips(frame)
        central_chips = self._count_central_chips(chips)
        
        if central_chips == 0:  # 중앙 팟에 칩이 없음
            indicators['pot_cleared'] = True
            confidence_scores['pot_cleared'] = 30
        else:
            confidence_scores['pot_cleared'] = 0
        
        # 3. 모션 활동 급감 (20점)
        if motion_info['total_motion_area'] < 500:  # 매우 적은 모션
            indicators['reduced_activity'] = True
            confidence_scores['reduced_activity'] = 20
        else:
            confidence_scores['reduced_activity'] = 0
        
        total_confidence = sum(confidence_scores.values())
        is_hand_end = total_confidence >= self.end_threshold
        
        return is_hand_end, total_confidence, {
            'indicators': indicators,
            'confidence_breakdown': confidence_scores,
            'collection_score': collection_score,
            'central_chips': central_chips,
            'motion_area': motion_info['total_motion_area']
        }
    
    def _get_time_since_last_hand(self, current_time):
        """마지막 핸드 종료 후 경과 시간"""
        if not self.detected_hands:
            return 60  # 첫 핸드는 적절한 시간으로 가정
        
        last_hand_end = self.detected_hands[-1].end_time
        return current_time - last_hand_end
    
    def _count_central_chips(self, chips):
        """중앙 영역의 칩 개수"""
        if self.object_detector.pot_region is None:
            return 0
        
        pot_region = self.object_detector.pot_region
        central_chips = 0
        
        for chip in chips:
            x, y = chip['center']
            if (pot_region['x1'] <= x <= pot_region['x2'] and 
                pot_region['y1'] <= y <= pot_region['y2']):
                central_chips += 1
        
        return central_chips
    
    def _validate_hands(self, hands):
        """핸드 검증 및 필터링"""
        validated_hands = []
        
        for hand in hands:
            # 기본 검증
            if hand.duration < 30 or hand.duration > 600:
                logger.debug(f"핸드 {hand.hand_id} 제외: 부적절한 길이 ({hand.duration:.1f}초)")
                continue
            
            if hand.overall_confidence < 50:
                logger.debug(f"핸드 {hand.hand_id} 제외: 낮은 신뢰도 ({hand.overall_confidence:.1f})")
                continue
            
            # 이전 핸드와의 겹침 확인
            if validated_hands:
                prev_hand = validated_hands[-1]
                if hand.start_time < prev_hand.end_time:
                    # 더 신뢰도가 높은 것을 선택
                    if hand.overall_confidence > prev_hand.overall_confidence:
                        validated_hands[-1] = hand
                    continue
            
            validated_hands.append(hand)
        
        return validated_hands

def main():
    """테스트 실행"""
    detector = HandBoundaryDetector()
    
    video_path = "videos/sample_poker_video.mp4"
    
    if Path(video_path).exists():
        result_file = detector.analyze_video(video_path)
        print(f"분석 결과: {result_file}")
        
        # 결과 요약 출력
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"\n=== 분석 결과 요약 ===")
        print(f"감지된 핸드 수: {len(results)}")
        if results:
            total_duration = sum(hand['duration'] for hand in results)
            avg_duration = total_duration / len(results)
            avg_confidence = sum(hand['overall_confidence'] for hand in results) / len(results)
            
            print(f"평균 핸드 길이: {avg_duration:.1f}초")
            print(f"평균 신뢰도: {avg_confidence:.1f}")
            print(f"전체 게임 시간: {total_duration:.1f}초")
    else:
        print(f"테스트 비디오가 없습니다: {video_path}")
        print("먼저 샘플 비디오를 생성하세요: python -m src.generate_sample_video")

if __name__ == "__main__":
    main()