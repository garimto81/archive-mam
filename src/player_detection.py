"""
참여 플레이어 감지 모듈
포커 영상에서 각 핸드에 참여한 플레이어를 자동으로 식별하는 모듈
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import defaultdict

@dataclass
class PlayerSeat:
    """플레이어 좌석 정보"""
    seat_id: int
    x: int
    y: int
    width: int
    height: int
    name: str
    description: str

@dataclass
class CardDetection:
    """카드 감지 결과"""
    seat_id: int
    timestamp: float
    has_cards: bool
    confidence: float
    card_count: int
    bbox: Tuple[int, int, int, int]

@dataclass
class HandParticipation:
    """핸드 참여 정보"""
    hand_id: int
    start_time: float
    end_time: float
    participating_seats: List[int]
    total_players: int
    detection_confidence: float
    frame_samples: int

class PlayerDetector:
    """플레이어 감지기"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # 기본 좌석 배치 (9인 테이블 기준)
        self.seat_positions = [
            PlayerSeat(1, 320, 50, 80, 60, "Seat 1", "상단 중앙"),
            PlayerSeat(2, 520, 100, 80, 60, "Seat 2", "상단 우측"),
            PlayerSeat(3, 600, 180, 80, 60, "Seat 3", "우측 상단"),
            PlayerSeat(4, 600, 260, 80, 60, "Seat 4", "우측 하단"),
            PlayerSeat(5, 520, 340, 80, 60, "Seat 5", "하단 우측"),
            PlayerSeat(6, 320, 390, 80, 60, "Seat 6", "하단 중앙"),
            PlayerSeat(7, 120, 340, 80, 60, "Seat 7", "하단 좌측"),
            PlayerSeat(8, 40, 260, 80, 60, "Seat 8", "좌측 하단"),
            PlayerSeat(9, 40, 180, 80, 60, "Seat 9", "좌측 상단"),
        ]
        
        # 카드 감지 설정
        self.card_template_size = (15, 20)  # 카드 템플릿 크기
        self.detection_threshold = 0.6      # 감지 임계값
        self.min_card_area = 200           # 최소 카드 영역
        self.max_card_area = 2000          # 최대 카드 영역
        
        # 홀카드 색상 범위 (일반적으로 흰색/회색)
        self.card_color_ranges = [
            # HSV 색상 범위
            {'lower': np.array([0, 0, 180]), 'upper': np.array([180, 30, 255])},  # 밝은 회색-흰색
            {'lower': np.array([0, 0, 120]), 'upper': np.array([180, 50, 200])},  # 중간 회색
        ]
        
        if config_path and Path(config_path).exists():
            self.load_config(config_path)
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self, config_path: str):
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 좌석 위치 업데이트
            if 'seat_positions' in config:
                self.seat_positions = [
                    PlayerSeat(**seat) for seat in config['seat_positions']
                ]
            
            # 감지 설정 업데이트
            if 'detection_settings' in config:
                settings = config['detection_settings']
                self.detection_threshold = settings.get('threshold', self.detection_threshold)
                self.min_card_area = settings.get('min_area', self.min_card_area)
                self.max_card_area = settings.get('max_area', self.max_card_area)
                
            self.logger.info(f"설정 파일 로드 완료: {config_path}")
            
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
    
    def preprocess_frame(self, frame: np.ndarray) -> Dict[str, np.ndarray]:
        """프레임 전처리"""
        # 다양한 색상 공간으로 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 엣지 검출
        edges = cv2.Canny(denoised, 50, 150)
        
        # 모폴로지 연산으로 카드 모양 강화
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 5))
        morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return {
            'gray': gray,
            'hsv': hsv,
            'edges': edges,
            'morphed': morphed,
            'denoised': denoised
        }
    
    def extract_seat_roi(self, frame: np.ndarray, seat: PlayerSeat) -> np.ndarray:
        """좌석 ROI 영역 추출"""
        h, w = frame.shape[:2]
        
        # 좌표 범위 체크
        x1 = max(0, seat.x)
        y1 = max(0, seat.y)
        x2 = min(w, seat.x + seat.width)
        y2 = min(h, seat.y + seat.height)
        
        return frame[y1:y2, x1:x2]
    
    def detect_cards_in_roi(self, roi_dict: Dict[str, np.ndarray], seat: PlayerSeat) -> CardDetection:
        """ROI 영역에서 카드 감지"""
        gray_roi = roi_dict['gray']
        hsv_roi = roi_dict['hsv']
        edges_roi = roi_dict['edges']
        
        if gray_roi.size == 0:
            return CardDetection(seat.seat_id, 0, False, 0, 0, (0, 0, 0, 0))
        
        # 방법 1: 색상 기반 감지
        card_mask = np.zeros(gray_roi.shape, dtype=np.uint8)
        for color_range in self.card_color_ranges:
            mask = cv2.inRange(hsv_roi, color_range['lower'], color_range['upper'])
            card_mask = cv2.bitwise_or(card_mask, mask)
        
        # 방법 2: 윤곽선 기반 감지
        contours, _ = cv2.findContours(edges_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 카드 후보 찾기
        card_candidates = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_card_area <= area <= self.max_card_area:
                # 종횡비 체크 (카드는 보통 2:3 비율)
                rect = cv2.minAreaRect(contour)
                width, height = rect[1]
                if width > 0 and height > 0:
                    aspect_ratio = max(width, height) / min(width, height)
                    if 1.2 <= aspect_ratio <= 2.0:  # 카드 비율 범위
                        card_candidates.append({
                            'contour': contour,
                            'area': area,
                            'aspect_ratio': aspect_ratio,
                            'rect': rect
                        })
        
        # 색상 마스크와 윤곽선 결합 점수 계산
        total_score = 0
        card_count = 0
        
        for candidate in card_candidates:
            # 윤곽선 내부의 색상 마스크 비율 계산
            mask = np.zeros(gray_roi.shape, dtype=np.uint8)
            cv2.fillContour(mask, [candidate['contour']], 0, 255, -1)
            
            color_overlap = cv2.bitwise_and(card_mask, mask)
            overlap_ratio = np.sum(color_overlap > 0) / candidate['area']
            
            # 점수 계산 (면적, 종횡비, 색상 일치도)
            area_score = min(candidate['area'] / 800, 1.0)  # 정규화
            ratio_score = 1.0 - abs(candidate['aspect_ratio'] - 1.5) / 1.5
            color_score = overlap_ratio
            
            combined_score = (area_score + ratio_score + color_score) / 3
            
            if combined_score >= self.detection_threshold:
                total_score += combined_score
                card_count += 1
        
        # 홀카드는 보통 2장
        has_cards = card_count >= 1
        confidence = min(total_score * 100, 100)
        
        return CardDetection(
            seat_id=seat.seat_id,
            timestamp=0,  # 호출하는 곳에서 설정
            has_cards=has_cards,
            confidence=confidence,
            card_count=card_count,
            bbox=(seat.x, seat.y, seat.width, seat.height)
        )
    
    def analyze_frame(self, frame: np.ndarray, timestamp: float) -> List[CardDetection]:
        """단일 프레임에서 모든 좌석의 카드 감지"""
        detections = []
        processed = self.preprocess_frame(frame)
        
        for seat in self.seat_positions:
            try:
                # 각 좌석별 ROI 추출
                roi_dict = {}
                for key, img in processed.items():
                    roi_dict[key] = self.extract_seat_roi(img, seat)
                
                # 카드 감지
                detection = self.detect_cards_in_roi(roi_dict, seat)
                detection.timestamp = timestamp
                
                detections.append(detection)
                
                if detection.has_cards and detection.confidence > 50:
                    self.logger.debug(f"Seat {seat.seat_id}: 카드 감지 (신뢰도: {detection.confidence:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"Seat {seat.seat_id} 분석 실패: {e}")
                continue
        
        return detections
    
    def analyze_hand_segment(self, video_path: str, start_time: float, 
                           end_time: float, hand_id: int = 1) -> HandParticipation:
        """핸드 구간에서 참여 플레이어 분석"""
        self.logger.info(f"핸드 {hand_id} 분석 시작: {start_time:.1f}s - {end_time:.1f}s")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 시작 시간으로 이동
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        
        all_detections = []
        frame_count = 0
        sample_interval = max(1.0, (end_time - start_time) / 10)  # 최대 10개 샘플
        
        try:
            current_time = start_time
            while current_time < end_time:
                # 특정 시간으로 이동
                cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # 카드 감지
                detections = self.analyze_frame(frame, current_time)
                all_detections.extend(detections)
                frame_count += 1
                
                current_time += sample_interval
                
                if frame_count % 5 == 0:
                    self.logger.debug(f"핸드 {hand_id} 진행률: {((current_time - start_time) / (end_time - start_time)) * 100:.1f}%")
        
        finally:
            cap.release()
        
        # 참여 플레이어 결정
        participation = self._determine_participation(all_detections, hand_id, start_time, end_time, frame_count)
        
        self.logger.info(f"핸드 {hand_id} 완료: {participation.total_players}명 참여")
        
        return participation
    
    def _determine_participation(self, all_detections: List[CardDetection], 
                               hand_id: int, start_time: float, end_time: float,
                               frame_samples: int) -> HandParticipation:
        """모든 감지 결과를 바탕으로 참여 플레이어 결정"""
        seat_votes = defaultdict(list)  # seat_id -> [confidence 값들]
        
        # 좌석별 신뢰도 수집
        for detection in all_detections:
            if detection.has_cards:
                seat_votes[detection.seat_id].append(detection.confidence)
        
        # 좌석별 참여 여부 결정
        participating_seats = []
        total_confidence = 0
        
        for seat_id, confidences in seat_votes.items():
            if not confidences:
                continue
                
            # 평균 신뢰도와 일관성 점수 계산
            avg_confidence = np.mean(confidences)
            consistency = len(confidences) / frame_samples  # 프레임에서 감지된 비율
            
            # 참여 결정 기준: 평균 신뢰도 > 60% AND 일관성 > 30%
            if avg_confidence >= 60 and consistency >= 0.3:
                participating_seats.append(seat_id)
                total_confidence += avg_confidence
        
        # 전체 신뢰도 계산
        detection_confidence = total_confidence / len(participating_seats) if participating_seats else 0
        
        return HandParticipation(
            hand_id=hand_id,
            start_time=start_time,
            end_time=end_time,
            participating_seats=sorted(participating_seats),
            total_players=len(participating_seats),
            detection_confidence=detection_confidence,
            frame_samples=frame_samples
        )
    
    def analyze_multiple_hands(self, video_path: str, 
                             hand_segments: List[Dict]) -> List[HandParticipation]:
        """여러 핸드 구간 분석"""
        results = []
        
        for i, segment in enumerate(hand_segments):
            try:
                hand_id = segment.get('hand_id', i + 1)
                start_time = segment['start_time']
                end_time = segment['end_time']
                
                participation = self.analyze_hand_segment(video_path, start_time, end_time, hand_id)
                results.append(participation)
                
            except Exception as e:
                self.logger.error(f"핸드 {i+1} 분석 실패: {e}")
                continue
        
        return results
    
    def save_results(self, results: List[HandParticipation], output_path: str):
        """결과를 JSON 파일로 저장"""
        export_data = {
            'analysis_type': 'player_detection',
            'timestamp': cv2.getTickCount(),
            'total_hands': len(results),
            'seat_positions': [asdict(seat) for seat in self.seat_positions],
            'hands': [asdict(result) for result in results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"결과 저장 완료: {output_path}")
    
    def get_participation_summary(self, results: List[HandParticipation]) -> Dict:
        """참여 통계 요약"""
        if not results:
            return {}
        
        # 좌석별 참여 횟수
        seat_participation = defaultdict(int)
        for result in results:
            for seat_id in result.participating_seats:
                seat_participation[seat_id] += 1
        
        # 플레이어 수 분포
        player_count_dist = defaultdict(int)
        for result in results:
            player_count_dist[result.total_players] += 1
        
        # 평균 신뢰도
        avg_confidence = np.mean([r.detection_confidence for r in results])
        
        return {
            'total_hands': len(results),
            'seat_participation': dict(seat_participation),
            'player_count_distribution': dict(player_count_dist),
            'average_confidence': avg_confidence,
            'most_active_seat': max(seat_participation.items(), key=lambda x: x[1])[0] if seat_participation else None,
            'average_players_per_hand': np.mean([r.total_players for r in results])
        }
    
    def visualize_detections(self, frame: np.ndarray, detections: List[CardDetection]) -> np.ndarray:
        """감지 결과를 프레임에 시각화"""
        result_frame = frame.copy()
        
        for detection in detections:
            seat = next(s for s in self.seat_positions if s.seat_id == detection.seat_id)
            
            # 좌석 영역 표시
            color = (0, 255, 0) if detection.has_cards else (100, 100, 100)
            thickness = 3 if detection.has_cards else 1
            
            cv2.rectangle(result_frame, 
                         (seat.x, seat.y), 
                         (seat.x + seat.width, seat.y + seat.height),
                         color, thickness)
            
            # 좌석 번호와 신뢰도 표시
            label = f"S{detection.seat_id}"
            if detection.has_cards:
                label += f" ({detection.confidence:.0f}%)"
            
            cv2.putText(result_frame, label, 
                       (seat.x, seat.y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return result_frame


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='플레이어 감지 모듈')
    parser.add_argument('video_path', help='분석할 비디오 파일 경로')
    parser.add_argument('--hands', '-h', help='핸드 구간 JSON 파일 (GFX 분석 결과)')
    parser.add_argument('--output', '-o', help='결과 저장 경로 (JSON)')
    parser.add_argument('--start', '-s', type=float, help='단일 핸드 시작 시간')
    parser.add_argument('--end', '-e', type=float, help='단일 핸드 종료 시간')
    parser.add_argument('--config', '-c', help='설정 파일 경로')
    parser.add_argument('--visualize', '-v', action='store_true', help='결과 시각화')
    parser.add_argument('--debug', '-d', action='store_true', help='디버그 모드')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 플레이어 감지기 생성
        detector = PlayerDetector(config_path=args.config)
        
        if args.start is not None and args.end is not None:
            # 단일 핸드 분석
            result = detector.analyze_hand_segment(args.video_path, args.start, args.end)
            results = [result]
        elif args.hands:
            # 여러 핸드 분석
            with open(args.hands, 'r', encoding='utf-8') as f:
                hand_data = json.load(f)
            
            hand_segments = hand_data.get('segments', [])
            results = detector.analyze_multiple_hands(args.video_path, hand_segments)
        else:
            print("핸드 구간 정보가 필요합니다. --hands 또는 --start/--end 옵션을 사용하세요.")
            return 1
        
        # 결과 저장
        if args.output:
            detector.save_results(results, args.output)
        
        # 결과 요약 출력
        summary = detector.get_participation_summary(results)
        
        print(f"\n👥 플레이어 감지 결과:")
        print(f"• 총 핸드 수: {summary.get('total_hands', 0)}")
        print(f"• 핸드당 평균 플레이어: {summary.get('average_players_per_hand', 0):.1f}명")
        print(f"• 평균 감지 신뢰도: {summary.get('average_confidence', 0):.1f}%")
        
        if summary.get('seat_participation'):
            print(f"• 가장 활발한 좌석: Seat {summary['most_active_seat']}")
            print(f"• 좌석별 참여 횟수:")
            for seat_id, count in summary['seat_participation'].items():
                print(f"  - Seat {seat_id}: {count}회")
        
        # 각 핸드별 상세 정보
        print(f"\n🎮 핸드별 상세:")
        for result in results:
            seat_list = ', '.join([f"Seat {s}" for s in result.participating_seats])
            print(f"Hand {result.hand_id}: {result.total_players}명 [{seat_list}] (신뢰도: {result.detection_confidence:.1f}%)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())