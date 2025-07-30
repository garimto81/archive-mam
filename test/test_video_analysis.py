#!/usr/bin/env python
"""
비디오 분석 모듈 단위 테스트
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
import sys

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.detect_hands import analyze_video, detect_text_in_frame
    from src.detect_pot_size import analyze_pot_size
    from src.integrate_analysis import analyze_video as integrate_analyze_video
    from src.generate_sample_video import create_sample_video
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("프로젝트 루트 디렉토리에서 테스트를 실행해주세요.")
    sys.exit(1)

class TestVideoAnalysis:
    """비디오 분석 기능 테스트"""
    
    @pytest.fixture(scope="class")
    def sample_video(self):
        """테스트용 샘플 비디오 생성"""
        video_path = "videos/test_sample_video.mp4"
        os.makedirs("videos", exist_ok=True)
        
        try:
            create_sample_video(video_path, duration=10, fps=2)
            yield video_path
        finally:
            # 테스트 후 정리
            if os.path.exists(video_path):
                os.remove(video_path)
    
    def test_sample_video_creation(self, sample_video):
        """샘플 비디오 생성 테스트"""
        assert os.path.exists(sample_video), "샘플 비디오 파일이 생성되지 않았습니다"
        
        # 파일 크기 확인 (최소 크기)
        file_size = os.path.getsize(sample_video)
        assert file_size > 1000, f"비디오 파일이 너무 작습니다: {file_size} bytes"
    
    def test_hand_detection_with_valid_video(self, sample_video):
        """유효한 비디오로 핸드 감지 테스트"""
        # 실제 분석 함수 호출 (콘솔 출력 캡처)
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            analyze_video(sample_video)
        
        output = f.getvalue()
        assert "Analysis Complete" in output, "분석이 완료되지 않았습니다"
    
    def test_hand_detection_with_invalid_video(self):
        """존재하지 않는 비디오 파일 테스트"""
        invalid_path = "videos/nonexistent_video.mp4"
        
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            analyze_video(invalid_path)
        
        output = f.getvalue()
        assert "Error" in output, "에러 메시지가 출력되지 않았습니다"
    
    def test_pot_size_analysis(self, sample_video):
        """팟 사이즈 분석 테스트"""
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            analyze_pot_size(sample_video)
        
        output = f.getvalue()
        assert "Analysis Complete" in output, "팟 사이즈 분석이 완료되지 않았습니다"
    
    def test_integrated_analysis(self, sample_video):
        """통합 분석 테스트"""
        result_file = integrate_analyze_video(sample_video)
        
        # 결과 파일이 생성되었는지 확인
        assert result_file is not None, "결과 파일 경로가 반환되지 않았습니다"
        assert os.path.exists(result_file), f"결과 파일이 생성되지 않았습니다: {result_file}"
        
        # JSON 파일 내용 확인
        with open(result_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "결과 데이터가 리스트가 아닙니다"
        
        if data:  # 데이터가 있는 경우
            hand = data[0]
            required_fields = ["start_time_s", "pot_size_history", "participating_players"]
            
            for field in required_fields:
                assert field in hand, f"필수 필드 '{field}'가 없습니다"
        
        # 테스트 후 정리
        if os.path.exists(result_file):
            os.remove(result_file)
    
    def test_detect_text_in_frame(self):
        """프레임 텍스트 감지 테스트"""
        # 더미 프레임 생성 (검은색 이미지)
        import numpy as np
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 텍스트 감지 테스트
        result_start = detect_text_in_frame(dummy_frame, "Hand Start")
        result_end = detect_text_in_frame(dummy_frame, "Hand End")
        result_invalid = detect_text_in_frame(dummy_frame, "Invalid Text")
        
        # 결과는 boolean이어야 함
        assert isinstance(result_start, (bool, np.bool_)), "Hand Start 감지 결과가 boolean이 아닙니다"
        assert isinstance(result_end, (bool, np.bool_)), "Hand End 감지 결과가 boolean이 아닙니다"
        assert isinstance(result_invalid, (bool, np.bool_)), "Invalid Text 감지 결과가 boolean이 아닙니다"
        
        # 잘못된 텍스트는 False를 반환해야 함
        assert result_invalid == False, "잘못된 텍스트에 대해 False를 반환하지 않았습니다"


class TestDataValidation:
    """데이터 검증 테스트"""
    
    def test_analysis_result_structure(self):
        """분석 결과 구조 테스트"""
        # 기존 분석 결과 파일 확인
        analysis_file = "analysis_results/poker_hands_analysis.json"
        
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list), "분석 결과가 리스트가 아닙니다"
            
            if data:
                hand = data[0]
                required_fields = [
                    "hand_id", "start_time_s", "end_time_s", 
                    "pot_size_history", "participating_players"
                ]
                
                for field in required_fields:
                    assert field in hand, f"필수 필드 '{field}'가 없습니다"
                
                # 데이터 타입 확인
                assert isinstance(hand["hand_id"], int), "hand_id가 정수가 아닙니다"
                assert isinstance(hand["start_time_s"], (int, float)), "start_time_s가 숫자가 아닙니다"
                assert isinstance(hand["pot_size_history"], list), "pot_size_history가 리스트가 아닙니다"
                assert isinstance(hand["participating_players"], list), "participating_players가 리스트가 아닙니다"
    
    def test_pot_size_data_consistency(self):
        """팟 사이즈 데이터 일관성 테스트"""
        analysis_file = "analysis_results/poker_hands_analysis.json"
        
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            
            for hand in data[:10]:  # 처음 10개만 테스트
                for pot_entry in hand.get("pot_size_history", []):
                    assert "time_s" in pot_entry, "팟 히스토리에 time_s가 없습니다"
                    assert "pot" in pot_entry, "팟 히스토리에 pot이 없습니다"
                    assert isinstance(pot_entry["pot"], (int, float)), "팟 값이 숫자가 아닙니다"
                    assert pot_entry["pot"] >= 0, "팟 값이 음수입니다"


def run_tests():
    """테스트 실행"""
    print("🧪 비디오 분석 모듈 단위 테스트 시작")
    print("=" * 50)
    
    # OpenCV 가용성 확인
    try:
        import cv2
        print("✅ OpenCV 사용 가능")
    except ImportError:
        print("❌ OpenCV를 찾을 수 없습니다. pip install opencv-python")
        return False
    
    # NumPy 가용성 확인
    try:
        import numpy as np
        print("✅ NumPy 사용 가능")
    except ImportError:
        print("❌ NumPy를 찾을 수 없습니다. pip install numpy")
        return False
    
    # pytest 실행
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)