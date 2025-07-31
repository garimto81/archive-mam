#!/usr/bin/env python
"""
포커 MAM 테스트 환경 설정 스크립트
필요한 디렉토리 생성 및 샘플 비디오 생성
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_directories():
    """필요한 디렉토리 생성"""
    directories = [
        'videos',
        'test_videos',
        'temp_videos',
        'analysis_results',
        'static/results',
        'logs'
    ]
    
    print("[INFO] 디렉토리 생성 중...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  - {directory} 생성 완료")
    
    return True

def check_dependencies():
    """필수 패키지 확인"""
    print("\n[INFO] 필수 패키지 확인 중...")
    
    required_packages = [
        'flask',
        'opencv-python',
        'numpy',
        'yt-dlp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  [OK] {package} 설치됨")
        except ImportError:
            print(f"  [X] {package} 미설치")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n[WARNING] 다음 패키지가 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("[INFO] 다음 명령어로 설치하세요:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    
    return True

def generate_test_videos():
    """테스트용 샘플 비디오 생성"""
    print("\n[INFO] 테스트 비디오 생성 중...")
    
    # 샘플 비디오 생성 스크립트 실행
    try:
        subprocess.run([sys.executable, 'src/generate_sample_video.py'], check=True)
        print("  [OK] 샘플 비디오 생성 완료")
        return True
    except subprocess.CalledProcessError:
        print("  [FAIL] 샘플 비디오 생성 실패")
        print("  수동으로 실행하세요: python src/generate_sample_video.py")
        return False
    except FileNotFoundError:
        print("  [ERROR] generate_sample_video.py 파일을 찾을 수 없습니다")
        return False

def create_test_scripts():
    """테스트 실행 스크립트 생성"""
    print("\n[INFO] 테스트 스크립트 생성 중...")
    
    # Windows 배치 파일
    bat_content = """@echo off
echo ======================================
echo 포커 MAM 테스트 환경
echo ======================================
echo.

echo 1. 웹 서버 시작 (기본 모드)
echo 2. 웹 서버 시작 (디버그 모드)
echo 3. 고속 분석 테스트
echo 4. 기본 분석 테스트
echo 5. 모든 테스트 실행
echo 6. 종료
echo.

set /p choice=선택하세요 (1-6): 

if "%choice%"=="1" (
    echo 웹 서버를 시작합니다...
    python run_poker_app.py
) else if "%choice%"=="2" (
    echo 디버그 모드로 웹 서버를 시작합니다...
    python run_poker_app.py dev
) else if "%choice%"=="3" (
    echo 고속 분석 테스트를 실행합니다...
    python test_fast_detector.py
) else if "%choice%"=="4" (
    echo 기본 분석 테스트를 실행합니다...
    python -m src.hand_boundary_detector
) else if "%choice%"=="5" (
    echo 모든 테스트를 실행합니다...
    python run_all_tests.py
) else if "%choice%"=="6" (
    exit
) else (
    echo 잘못된 선택입니다.
)

pause
"""
    
    with open('test_menu.bat', 'w') as f:
        f.write(bat_content)
    print("  [OK] test_menu.bat 생성 완료")
    
    # Python 테스트 실행기
    py_content = """#!/usr/bin/env python
\"\"\"
간단한 테스트 실행기
\"\"\"
import subprocess
import sys

def run_test(test_name, command):
    print(f"\\n{'='*60}")
    print(f"테스트: {test_name}")
    print(f"{'='*60}")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"\\n[OK] {test_name} 완료")
    except subprocess.CalledProcessError:
        print(f"\\n[FAIL] {test_name} 실패")

if __name__ == "__main__":
    print("포커 MAM 간단 테스트")
    print("="*60)
    
    # 1. 샘플 비디오로 고속 분석 테스트
    if len(sys.argv) > 1 and sys.argv[1] == "fast":
        run_test("고속 분석 (60fps 샘플링)", 
                f"{sys.executable} test_fast_detector.py test_videos/sample_poker_tournament.mp4")
    
    # 2. 웹 서버 테스트
    elif len(sys.argv) > 1 and sys.argv[1] == "web":
        print("웹 브라우저에서 http://localhost:5000 접속")
        run_test("웹 서버", f"{sys.executable} run_poker_app.py")
    
    else:
        print("사용법:")
        print("  python run_simple_test.py fast  # 고속 분석 테스트")
        print("  python run_simple_test.py web   # 웹 서버 실행")
"""
    
    with open('run_simple_test.py', 'w') as f:
        f.write(py_content)
    print("  [OK] run_simple_test.py 생성 완료")
    
    return True

def main():
    """메인 설정 함수"""
    print("="*60)
    print("포커 MAM 테스트 환경 설정")
    print("="*60)
    
    # 1. 디렉토리 설정
    if not setup_directories():
        print("\n[ERROR] 디렉토리 생성 실패")
        return
    
    # 2. 의존성 확인
    if not check_dependencies():
        print("\n[WARNING] 일부 패키지가 설치되지 않았습니다")
        print("계속 진행하시겠습니까? (y/n): ", end='')
        if input().lower() != 'y':
            return
    
    # 3. 테스트 비디오 생성
    generate_test_videos()
    
    # 4. 테스트 스크립트 생성
    create_test_scripts()
    
    print("\n" + "="*60)
    print("테스트 환경 설정 완료!")
    print("="*60)
    print("\n다음 명령어로 테스트를 시작하세요:")
    print("  - Windows: test_menu.bat")
    print("  - Python: python run_simple_test.py [fast|web]")
    print("  - 웹 UI: python run_poker_app.py")
    print("\n웹 UI 접속: http://localhost:5000")

if __name__ == "__main__":
    main()