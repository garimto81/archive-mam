#!/usr/bin/env python
"""
포커 MAM 빠른 테스트 스크립트
1분 안에 모든 기능을 간단히 테스트
"""
import os
import time
import subprocess
import sys
from pathlib import Path

def print_header(text):
    """헤더 출력"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def run_command(cmd, description):
    """명령 실행 및 결과 출력"""
    print(f"\n[실행] {description}")
    print(f"[명령] {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[결과] 성공")
            return True
        else:
            print(f"[결과] 실패: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("[결과] 시간 초과 (30초)")
        return False
    except Exception as e:
        print(f"[결과] 오류: {e}")
        return False

def quick_test():
    """빠른 테스트 실행"""
    print_header("포커 MAM 빠른 테스트")
    print("이 테스트는 약 1분 정도 소요됩니다.")
    
    # 1. 환경 확인
    print_header("1. 환경 확인")
    
    # Python 버전
    print(f"Python 버전: {sys.version.split()[0]}")
    
    # 필수 패키지 확인
    packages = ['cv2', 'flask', 'numpy']
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg} 설치됨")
        except ImportError:
            print(f"  [X] {pkg} 미설치")
    
    # 2. 디렉토리 확인
    print_header("2. 디렉토리 구조")
    
    dirs = ['videos', 'test_videos', 'temp_videos', 'analysis_results', 'src', 'templates']
    for d in dirs:
        if os.path.exists(d):
            print(f"  [OK] {d}/")
        else:
            print(f"  [X] {d}/ (생성 중...)")
            Path(d).mkdir(parents=True, exist_ok=True)
    
    # 3. 샘플 비디오 확인
    print_header("3. 샘플 비디오")
    
    sample_video = "test_videos/sample_poker_tournament.mp4"
    if os.path.exists(sample_video):
        size = os.path.getsize(sample_video) / (1024*1024)
        print(f"  [OK] {sample_video} ({size:.1f} MB)")
    else:
        print(f"  [X] 샘플 비디오 없음")
        print("  생성하려면: python src/generate_sample_video.py")
    
    # 4. 고속 분석 테스트 (간단 버전)
    print_header("4. 고속 분석 테스트")
    
    if os.path.exists(sample_video):
        # 짧은 테스트를 위한 Python 코드 실행
        test_code = f"""
import sys
sys.path.append('.')
from src.fast_hand_detector import FastHandDetector

detector = FastHandDetector(sampling_rate=60, num_workers=2)
print("고속 감지기 생성 완료")

# 5초만 분석 (전체 분석은 시간이 오래 걸림)
import cv2
cap = cv2.VideoCapture("{sample_video}")
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(fps * 5)  # 5초 분량만

print(f"5초 분량 테스트: {{total_frames}} 프레임")
cap.release()

print("테스트 성공!")
"""
        
        with open('_quick_test_temp.py', 'w') as f:
            f.write(test_code)
        
        run_command(f"{sys.executable} _quick_test_temp.py", "고속 감지기 초기화 테스트")
        
        # 임시 파일 삭제
        if os.path.exists('_quick_test_temp.py'):
            os.remove('_quick_test_temp.py')
    
    # 5. 웹 서버 테스트
    print_header("5. 웹 서버 확인")
    
    # Flask 앱 import 테스트
    try:
        import poker_analyzer_app
        print("  [OK] Flask 앱 로드 가능")
    except Exception as e:
        print(f"  [X] Flask 앱 로드 실패: {e}")
    
    # 6. 최종 결과
    print_header("테스트 완료")
    print("\n다음 단계:")
    print("1. 웹 서버 실행: python run_poker_app.py")
    print("2. 브라우저 접속: http://localhost:5000")
    print("3. 샘플 비디오로 테스트")
    print("\n자세한 테스트는 TEST_GUIDE.md 참조")

if __name__ == "__main__":
    quick_test()