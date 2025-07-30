#!/usr/bin/env python
"""
전체 테스트 실행 스크립트
"""
import os
import sys
import subprocess
import time
import httpx
from pathlib import Path

def check_server_running(url, timeout=5):
    """서버가 실행 중인지 확인"""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
            return response.status_code == 200
    except:
        return False

def run_command(cmd, description):
    """명령어 실행 및 결과 반환"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - 성공")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - 실패")
            if result.stderr:
                print("에러 출력:")
                print(result.stderr)
            if result.stdout:
                print("표준 출력:")
                print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ {description} - 예외 발생: {e}")
        return False

def main():
    """메인 테스트 실행 함수"""
    print("🚀 Poker MAM 전체 테스트 실행")
    print("=" * 60)
    
    # 현재 디렉토리가 프로젝트 루트인지 확인
    if not Path("src/main.py").exists():
        print("❌ 프로젝트 루트 디렉토리에서 실행해주세요.")
        return False
    
    test_results = []
    
    # 1. 환경 확인
    print("\n🔍 환경 확인 중...")
    
    # Python 버전 확인
    python_version = run_command("python --version", "Python 버전 확인")
    test_results.append(("Python 버전", python_version))
    
    # 필수 패키지 확인
    opencv_check = run_command("python -c \"import cv2; print('OpenCV:', cv2.__version__)\"", "OpenCV 확인")
    test_results.append(("OpenCV", opencv_check))
    
    numpy_check = run_command("python -c \"import numpy; print('NumPy:', numpy.__version__)\"", "NumPy 확인")
    test_results.append(("NumPy", numpy_check))
    
    # 2. 백엔드 서버 확인
    print("\n🔍 백엔드 서버 상태 확인...")
    backend_running = check_server_running("http://localhost:8000")
    
    if not backend_running:
        print("❌ 백엔드 서버가 실행되지 않았습니다.")
        print("run_test_server.bat 또는 run_api.py를 실행해주세요.")
        return False
    else:
        print("✅ 백엔드 서버 실행 중")
    
    # 3. 단위 테스트 실행
    unit_test = run_command("python test/test_video_analysis.py", "비디오 분석 단위 테스트")
    test_results.append(("단위 테스트", unit_test))
    
    # 4. API 통합 테스트 실행
    api_test = run_command("python test/test_api_endpoints.py", "API 통합 테스트")
    test_results.append(("API 통합 테스트", api_test))
    
    # 5. 성능 테스트 실행
    performance_test = run_command("python test/performance_test.py", "성능 테스트")
    test_results.append(("성능 테스트", performance_test))
    
    # 6. 프론트엔드 테스트 (선택사항)
    frontend_running = check_server_running("http://localhost:3000")
    
    if frontend_running:
        print("\n🔍 프론트엔드 서버 감지됨, E2E 테스트 실행...")
        
        # Chrome 드라이버 확인
        chrome_check = run_command("chromedriver --version", "Chrome 드라이버 확인")
        
        if chrome_check:
            frontend_test = run_command("python test/test_frontend.py --headless", "프론트엔드 E2E 테스트")
            test_results.append(("프론트엔드 E2E 테스트", frontend_test))
        else:
            print("⚠️  Chrome 드라이버가 없어 프론트엔드 테스트를 건너뜁니다.")
    else:
        print("⚠️  프론트엔드 서버가 실행되지 않아 E2E 테스트를 건너뜁니다.")
    
    # 7. 코드 품질 검사 (선택사항)
    print("\n🔍 코드 품질 검사...")
    
    # Flake8 검사
    flake8_check = run_command("flake8 src/ --max-line-length=100 --ignore=E501,W503", "Flake8 코드 스타일 검사")
    test_results.append(("코드 스타일 검사", flake8_check))
    
    # 8. 보안 검사 (선택사항)
    security_check = run_command("python -c \"import safety; print('Safety:', safety.__version__)\"", "보안 검사 도구 확인")
    if security_check:
        safety_test = run_command("safety check", "보안 취약점 검사")
        test_results.append(("보안 검사", safety_test))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n총 테스트: {total_tests}개")
    print(f"성공: {passed_tests}개")
    print(f"실패: {failed_tests}개")
    
    if failed_tests == 0:
        print("\n🎉 모든 테스트가 성공했습니다!")
        return True
    else:
        print(f"\n⚠️  {failed_tests}개의 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)