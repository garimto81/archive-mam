import cv2
import numpy as np
from collections import deque
import pytesseract
from typing import Dict, Tuple, Optional

class UIDetector:
    """그래픽 UI 감지를 위한 통합 감지기"""
    
    def __init__(self):
        self.motion_threshold = 0.05  # 5% 이하 움직임
        self.text_threshold = 0.3     # 30% 이상 텍스트 영역
        self.ui_threshold = 0.65      # 65% 이상 UI 확률
        
    def analyze_frame(self, frame: np.ndarray, prev_frame: Optional[np.ndarray] = None) -> Dict:
        """프레임에서 UI 관련 메트릭 분석"""
        metrics = {
            'motion_score': 0,
            'text_density': 0,
            'color_uniformity': 0,
            'edge_density': 0,
            'layout_score': 0
        }
        
        # 1. 모션 분석 (이전 프레임 필요)
        if prev_frame is not None:
            metrics['motion_score'] = self._calculate_motion_score(frame, prev_frame)
        
        # 2. 텍스트 밀도 분석
        metrics['text_density'] = self._calculate_text_density(frame)
        
        # 3. 색상 균일도 분석
        metrics['color_uniformity'] = self._calculate_color_uniformity(frame)
        
        # 4. 엣지 밀도 분석
        metrics['edge_density'] = self._calculate_edge_density(frame)
        
        # 5. 레이아웃 구조 분석
        metrics['layout_score'] = self._calculate_layout_score(frame)
        
        # UI 확률 계산
        ui_probability = self._calculate_ui_probability(metrics)
        
        return {
            'metrics': metrics,
            'ui_probability': ui_probability,
            'is_ui': ui_probability > self.ui_threshold
        }
    
    def _calculate_motion_score(self, frame: np.ndarray, prev_frame: np.ndarray) -> float:
        """프레임 간 움직임 점수 계산 (낮을수록 UI)"""
        # 그레이스케일 변환
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 프레임 차이 계산
        diff = cv2.absdiff(gray1, gray2)
        
        # 임계값 적용
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # 움직임 픽셀 비율
        motion_pixels = np.count_nonzero(thresh)
        total_pixels = frame.shape[0] * frame.shape[1]
        motion_ratio = motion_pixels / total_pixels
        
        # UI는 정적이므로 움직임이 적음 (역수 점수)
        return 100 * (1 - min(motion_ratio / self.motion_threshold, 1))
    
    def _calculate_text_density(self, frame: np.ndarray) -> float:
        """텍스트 영역 밀도 계산"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # MSER을 사용한 텍스트 영역 감지
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        # 텍스트 영역 필터링
        text_area = 0
        for region in regions:
            x, y, w, h = cv2.boundingRect(region)
            aspect_ratio = w / h if h > 0 else 0
            
            # 텍스트 특성: 가로로 긴 형태
            if 0.1 < aspect_ratio < 10 and 10 < w < frame.shape[1] * 0.8:
                text_area += w * h
        
        # 전체 대비 텍스트 영역 비율
        total_area = frame.shape[0] * frame.shape[1]
        text_ratio = text_area / total_area
        
        return min(text_ratio / self.text_threshold, 1) * 100
    
    def _calculate_color_uniformity(self, frame: np.ndarray) -> float:
        """색상 균일도 계산"""
        # HSV 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 색상 히스토그램 계산
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        hist = hist.flatten()
        
        # 정규화
        hist = hist / hist.sum()
        
        # 엔트로피 계산 (낮을수록 균일함)
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        max_entropy = np.log2(len(hist))
        
        # 균일도 점수 (높을수록 균일함)
        uniformity = 1 - (entropy / max_entropy)
        
        return uniformity * 100
    
    def _calculate_edge_density(self, frame: np.ndarray) -> float:
        """엣지 밀도 계산"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Canny 엣지 감지
        edges = cv2.Canny(gray, 50, 150)
        
        # 엣지 픽셀 비율
        edge_pixels = np.count_nonzero(edges)
        total_pixels = frame.shape[0] * frame.shape[1]
        edge_ratio = edge_pixels / total_pixels
        
        # UI는 직선적인 엣지가 많음
        return min(edge_ratio / 0.2, 1) * 100
    
    def _calculate_layout_score(self, frame: np.ndarray) -> float:
        """레이아웃 구조 점수 계산"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 엣지 감지
        edges = cv2.Canny(gray, 50, 150)
        
        # Hough 변환으로 직선 감지
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                               minLineLength=100, maxLineGap=10)
        
        if lines is None:
            return 0
        
        # 수평/수직 라인 카운트
        h_lines = 0
        v_lines = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            if angle < 10 or angle > 170:  # 수평
                h_lines += 1
            elif 80 < angle < 100:  # 수직
                v_lines += 1
        
        # 격자 구조 점수
        grid_score = min(h_lines + v_lines, 20) / 20
        
        return grid_score * 100
    
    def _calculate_ui_probability(self, metrics: Dict[str, float]) -> float:
        """종합 UI 확률 계산"""
        weights = {
            'motion_score': 0.25,
            'text_density': 0.20,
            'color_uniformity': 0.20,
            'edge_density': 0.15,
            'layout_score': 0.20
        }
        
        weighted_sum = sum(metrics[key] * weights[key] for key in metrics)
        return weighted_sum / 100


class UITracker:
    """UI 지속 시간 추적 및 핸드 경계 결정"""
    
    def __init__(self, fps: int = 30):
        self.fps = fps
        self.ui_threshold_frames = 15 * fps  # 15초
        self.ui_history = deque(maxlen=self.ui_threshold_frames)
        self.ui_start_time = None
        self.ui_end_time = None
        self.hands = []
        
    def update(self, is_ui: bool, timestamp: float) -> Tuple[str, Optional[float]]:
        """UI 상태 업데이트 및 핸드 경계 감지"""
        self.ui_history.append(is_ui)
        
        # 연속 UI 프레임 카운트
        ui_count = sum(self.ui_history)
        
        # UI가 15초 이상 지속
        if ui_count >= self.ui_threshold_frames:
            if self.ui_start_time is None:
                self.ui_start_time = timestamp - 15
                # 핸드 종료 시점은 UI 시작 15초 전
                hand_end = self.ui_start_time - 15
                return 'HAND_END', hand_end
            return 'UI_PERSISTENT', None
        
        # UI 종료 감지
        elif ui_count < self.fps and self.ui_start_time is not None:
            self.ui_end_time = timestamp
            self.ui_start_time = None
            # 핸드 시작 가능 시점은 UI 종료 15초 후
            potential_hand_start = self.ui_end_time + 15
            return 'HAND_START_POSSIBLE', potential_hand_start
        
        return 'MONITORING', None
    
    def get_hand_boundaries(self) -> list:
        """감지된 핸드 경계 반환"""
        return self.hands


class EnhancedHandDetector:
    """UI 기반 + 전통적 방식 통합 핸드 감지기"""
    
    def __init__(self, sampling_rate: int = 60):
        self.ui_detector = UIDetector()
        self.ui_tracker = UITracker()
        self.sampling_rate = sampling_rate
        self.prev_frame = None
        self.frame_count = 0
        self.hands = []
        self.current_hand = None
        
    def process_frame(self, frame: np.ndarray, timestamp: float) -> Dict:
        """프레임 처리 및 핸드 감지"""
        result = {
            'ui_detected': False,
            'ui_probability': 0,
            'hand_event': None,
            'timestamp': timestamp
        }
        
        # 샘플링 레이트에 따라 처리
        if self.frame_count % self.sampling_rate != 0:
            self.frame_count += 1
            return result
        
        # UI 분석
        ui_analysis = self.ui_detector.analyze_frame(frame, self.prev_frame)
        result['ui_detected'] = ui_analysis['is_ui']
        result['ui_probability'] = ui_analysis['ui_probability']
        
        # UI 추적 및 핸드 경계 결정
        event, event_time = self.ui_tracker.update(
            ui_analysis['is_ui'], timestamp
        )
        
        if event == 'HAND_END' and self.current_hand:
            # 현재 핸드 종료
            self.current_hand['end_time'] = event_time
            self.current_hand['end_confidence'] = 0.95
            self.current_hand['end_reason'] = 'UI_APPEARANCE'
            self.hands.append(self.current_hand)
            self.current_hand = None
            result['hand_event'] = 'HAND_ENDED'
            
        elif event == 'HAND_START_POSSIBLE':
            # 새 핸드 시작 가능
            result['hand_event'] = 'READY_FOR_NEW_HAND'
            result['suggested_start_time'] = event_time
        
        self.prev_frame = frame.copy()
        self.frame_count += 1
        
        return result
    
    def get_results(self) -> Dict:
        """최종 분석 결과 반환"""
        return {
            'total_hands': len(self.hands),
            'hands': self.hands,
            'detection_method': 'UI_BASED',
            'confidence': 'HIGH'
        }