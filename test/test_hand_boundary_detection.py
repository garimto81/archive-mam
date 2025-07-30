#!/usr/bin/env python
"""
핸드 경계 감지 시스템 테스트 및 검증
"""
import sys
import os
import pytest
import numpy as np
import cv2
import json
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.hand_boundary_detector import (
        HandBoundaryDetector, MotionTracker, ObjectDetector,
        HandBoundary, DetectionEvent
    )
    from src.generate_sample_video import create_sample_video
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)

class TestMotionTracker:
    """모션 추적 시스템 테스트"""
    
    @pytest.fixture
    def motion_tracker(self):
        return MotionTracker()
    
    @pytest.fixture
    def sample_frames(self):
        """테스트용 프레임 생성"""
        frames = []
        for i in range(10):
            # 640x480 크기의 컬러 프레임 생성
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # 움직이는 사각형 추가 (딜링 모션 시뮬레이션)
            x = 50 + i * 20
            y = 200 + int(10 * np.sin(i * 0.5))
            cv2.rectangle(frame, (x, y), (x+30, y+50), (255, 255, 255), -1)
            
            frames.append(frame)
        
        return frames
    
    def test_motion_tracker_initialization(self, motion_tracker):
        """모션 추적기 초기화 테스트"""
        assert motion_tracker.bg_subtractor is not None
        assert motion_tracker.lk_params is not None
        assert len(motion_tracker.motion_history) == 0
    
    def test_motion_update(self, motion_tracker, sample_frames):
        """모션 업데이트 테스트"""
        for frame in sample_frames[:5]:
            motion_info = motion_tracker.update(frame)
            
            assert 'timestamp' in motion_info
            assert 'motion_regions' in motion_info
            assert 'total_motion_area' in motion_info
            assert isinstance(motion_info['motion_regions'], list)
            assert isinstance(motion_info['total_motion_area'], (int, float))
    
    def test_dealing_motion_analysis(self, motion_tracker, sample_frames):
        """딜링 모션 분석 테스트"""
        # 몇 개 프레임 처리
        for frame in sample_frames:
            motion_tracker.update(frame)
        
        dealing_score = motion_tracker.analyze_motion_pattern('dealing')
        assert 0.0 <= dealing_score <= 1.0
    
    def test_collection_motion_analysis(self, motion_tracker, sample_frames):
        """팟 수집 모션 분석 테스트"""
        for frame in sample_frames:
            motion_tracker.update(frame)
        
        collection_score = motion_tracker.analyze_motion_pattern('collection')
        assert 0.0 <= collection_score <= 1.0

class TestObjectDetector:
    """객체 감지 시스템 테스트"""
    
    @pytest.fixture
    def object_detector(self):
        return ObjectDetector()
    
    @pytest.fixture
    def test_frame_with_cards(self):
        """카드가 있는 테스트 프레임 생성"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 카드 모양 사각형 추가 (3:4 비율)
        cv2.rectangle(frame, (100, 100), (175, 233), (255, 255, 255), -1)  # 75x133
        cv2.rectangle(frame, (300, 200), (375, 333), (255, 255, 255), -1)  # 75x133
        
        return frame
    
    @pytest.fixture
    def test_frame_with_chips(self):
        """칩이 있는 테스트 프레임 생성"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 다양한 색상의 원형 칩 추가
        cv2.circle(frame, (200, 200), 15, (255, 255, 255), -1)  # 흰색 칩
        cv2.circle(frame, (250, 200), 15, (0, 0, 255), -1)      # 빨간색 칩
        cv2.circle(frame, (300, 200), 15, (0, 255, 0), -1)      # 녹색 칩
        
        return frame
    
    def test_object_detector_initialization(self, object_detector):
        """객체 감지기 초기화 테스트"""
        assert object_detector.card_size_range is not None
        assert object_detector.card_aspect_ratio_range is not None
        assert object_detector.chip_colors is not None
        assert len(object_detector.chip_colors) > 0
    
    def test_card_detection_by_shape(self, object_detector, test_frame_with_cards):
        """형태 기반 카드 감지 테스트"""
        cards = object_detector._detect_cards_by_shape(test_frame_with_cards)
        
        assert isinstance(cards, list)
        # 최소 1개 이상의 카드가 감지되어야 함
        assert len(cards) >= 1
        
        if cards:
            card = cards[0]
            assert 'bbox' in card
            assert 'center' in card
            assert 'area' in card
            assert 'aspect_ratio' in card
    
    def test_card_detection_by_color(self, object_detector, test_frame_with_cards):
        """색상 기반 카드 감지 테스트"""
        cards = object_detector._detect_cards_by_color(test_frame_with_cards)
        
        assert isinstance(cards, list)
        # 흰색 카드가 감지될 수 있음
        if cards:
            card = cards[0]
            assert 'color' in card
            assert card['color'] == 'white'
    
    def test_chip_detection(self, object_detector, test_frame_with_chips):
        """칩 감지 테스트"""
        chips = object_detector.detect_chips(test_frame_with_chips)
        
        assert isinstance(chips, list)
        # 최소 1개 이상의 칩이 감지되어야 함
        assert len(chips) >= 1
        
        if chips:
            chip = chips[0]
            assert 'center' in chip
            assert 'radius' in chip
            assert 'color' in chip
            assert 'area' in chip
    
    def test_regions_setting(self, object_detector):
        """ROI 영역 설정 테스트"""
        frame_shape = (480, 640, 3)
        object_detector.set_regions(frame_shape)
        
        assert object_detector.pot_region is not None
        assert object_detector.player_regions is not None
        assert len(object_detector.player_regions) > 0
        
        # 팟 영역 검증
        pot = object_detector.pot_region
        assert pot['x1'] < pot['x2']
        assert pot['y1'] < pot['y2']

class TestHandBoundaryDetector:
    """핸드 경계 감지 메인 시스템 테스트"""
    
    @pytest.fixture
    def detector(self):
        return HandBoundaryDetector()
    
    @pytest.fixture
    def sample_video_path(self):
        """테스트용 샘플 비디오"""
        video_path = "test_videos/test_sample.mp4"
        os.makedirs("test_videos", exist_ok=True)
        
        if not os.path.exists(video_path):
            create_sample_video(video_path, duration=30, fps=10)
        
        return video_path
    
    def test_detector_initialization(self, detector):
        """감지기 초기화 테스트"""
        assert detector.motion_tracker is not None
        assert detector.object_detector is not None
        assert detector.current_hand_start is None
        assert len(detector.detected_hands) == 0
        assert detector.start_threshold > 0
        assert detector.end_threshold > 0
    
    def test_hand_start_detection_logic(self, detector):
        """핸드 시작 감지 로직 테스트"""
        # 테스트 프레임 생성
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 모션 정보 생성
        motion_info = {
            'motion_regions': [{'area': 1000, 'center': (320, 240)}],
            'total_motion_area': 1000,
            'flow_vectors': None
        }
        
        # 첫 번째 프레임 처리 (ROI 설정용)
        detector.object_detector.set_regions(frame.shape)
        
        is_start, confidence, indicators = detector._detect_hand_start(
            frame, motion_info, 60.0  # 1분 시점
        )
        
        assert isinstance(is_start, bool)
        assert isinstance(confidence, (int, float))
        assert isinstance(indicators, dict)
        assert 'indicators' in indicators
        assert 'confidence_breakdown' in indicators
    
    def test_hand_end_detection_logic(self, detector):
        """핸드 종료 감지 로직 테스트"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        motion_info = {
            'motion_regions': [{'area': 200, 'center': (320, 240)}],
            'total_motion_area': 200,
            'flow_vectors': None
        }
        
        detector.object_detector.set_regions(frame.shape)
        
        is_end, confidence, indicators = detector._detect_hand_end(
            frame, motion_info, 120.0  # 2분 시점
        )
        
        assert isinstance(is_end, bool)
        assert isinstance(confidence, (int, float))
        assert isinstance(indicators, dict)
    
    def test_video_analysis_integration(self, detector, sample_video_path):
        """전체 비디오 분석 통합 테스트"""
        if not os.path.exists(sample_video_path):
            pytest.skip(f"샘플 비디오가 없습니다: {sample_video_path}")
        
        result_file = detector.analyze_video(sample_video_path)
        
        assert os.path.exists(result_file)
        
        # 결과 파일 검증
        with open(result_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        assert isinstance(results, list)
        
        # 결과가 있다면 구조 검증
        if results:
            hand = results[0]
            required_fields = [
                'hand_id', 'start_time', 'end_time', 'duration',
                'start_confidence', 'end_confidence', 'overall_confidence'
            ]
            
            for field in required_fields:
                assert field in hand, f"필수 필드 '{field}'가 없습니다"
        
        # 테스트 후 정리
        os.remove(result_file)
    
    def test_hand_validation(self, detector):
        """핸드 검증 테스트"""
        # 테스트용 핸드 데이터 생성
        test_hands = [
            HandBoundary(
                hand_id=1, start_frame=0, end_frame=900,
                start_time=0.0, end_time=30.0, duration=30.0,
                start_confidence=80.0, end_confidence=85.0, overall_confidence=82.5,
                start_indicators={}, end_indicators={}
            ),
            HandBoundary(
                hand_id=2, start_frame=1000, end_frame=1150,
                start_time=35.0, end_time=40.0, duration=5.0,  # 너무 짧음
                start_confidence=75.0, end_confidence=70.0, overall_confidence=72.5,
                start_indicators={}, end_indicators={}
            ),
            HandBoundary(
                hand_id=3, start_frame=1200, end_frame=3000,
                start_time=45.0, end_time=105.0, duration=60.0,
                start_confidence=90.0, end_confidence=88.0, overall_confidence=89.0,
                start_indicators={}, end_indicators={}
            ),
        ]
        
        validated = detector._validate_hands(test_hands)
        
        # 너무 짧은 핸드(5초)는 제외되어야 함
        assert len(validated) == 2
        assert validated[0].hand_id == 1
        assert validated[1].hand_id == 3

class TestPerformanceMetrics:
    """성능 측정 테스트"""
    
    def test_processing_speed(self):
        """처리 속도 테스트"""
        detector = HandBoundaryDetector()
        
        # 테스트용 작은 비디오 생성
        test_video = "test_videos/speed_test.mp4"
        os.makedirs("test_videos", exist_ok=True)
        
        if not os.path.exists(test_video):
            create_sample_video(test_video, duration=10, fps=15)
        
        start_time = time.time()
        result_file = detector.analyze_video(test_video)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"처리 시간: {processing_time:.2f}초 (10초 비디오)")
        print(f"실시간 배율: {10.0 / processing_time:.2f}x")
        
        # 정리
        if os.path.exists(result_file):
            os.remove(result_file)
        
        # 처리 시간이 비디오 길이의 3배를 넘지 않아야 함 (허용 가능한 범위)
        assert processing_time < 30, f"처리가 너무 느림: {processing_time}초"
    
    def test_memory_usage(self):
        """메모리 사용량 테스트"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        detector = HandBoundaryDetector()
        
        # 여러 프레임 처리 시뮬레이션
        for i in range(100):
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            motion_info = detector.motion_tracker.update(frame)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 정리
        del detector
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"초기 메모리: {initial_memory:.1f}MB")
        print(f"최대 메모리: {peak_memory:.1f}MB")
        print(f"최종 메모리: {final_memory:.1f}MB")
        print(f"메모리 증가: {peak_memory - initial_memory:.1f}MB")
        
        # 메모리 증가가 500MB를 넘지 않아야 함
        assert peak_memory - initial_memory < 500, "메모리 사용량이 너무 높음"

def run_comprehensive_test():
    """종합 테스트 실행"""
    print("🧪 핸드 경계 감지 시스템 종합 테스트")
    print("=" * 60)
    
    # pytest 실행
    test_files = [__file__]
    
    print("단위 테스트 실행 중...")
    exit_code = pytest.main(["-v", "--tb=short"] + test_files)
    
    if exit_code == 0:
        print("\n✅ 모든 테스트 통과!")
        
        # 실제 비디오로 성능 테스트
        print("\n성능 테스트 실행 중...")
        
        detector = HandBoundaryDetector()
        
        # 샘플 비디오가 있다면 실제 테스트
        sample_video = "videos/sample_poker_video.mp4"
        if os.path.exists(sample_video):
            print(f"실제 비디오 테스트: {sample_video}")
            
            start_time = time.time()
            result_file = detector.analyze_video(sample_video)
            end_time = time.time()
            
            with open(result_file, 'r') as f:
                results = json.load(f)
            
            print(f"✅ 분석 완료: {len(results)}개 핸드 감지")
            print(f"⏱️  처리 시간: {end_time - start_time:.1f}초")
            
            if results:
                avg_confidence = sum(h['overall_confidence'] for h in results) / len(results)
                avg_duration = sum(h['duration'] for h in results) / len(results)
                print(f"📊 평균 신뢰도: {avg_confidence:.1f}")
                print(f"📊 평균 핸드 길이: {avg_duration:.1f}초")
        else:
            print("⚠️  실제 비디오가 없어 성능 테스트를 건너뜁니다.")
        
        return True
    else:
        print("\n❌ 일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)