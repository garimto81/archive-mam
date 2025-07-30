#!/usr/bin/env python
"""
포커 대회 영상 분석 앱 실행 스크립트
개발 및 프로덕션 환경에서 실행 가능
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_dependencies():
    """필수 종속성 확인"""
    required_packages = [
        'flask', 'cv2', 'numpy', 'yt_dlp', 'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("다음 패키지가 설치되지 않았습니다:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n설치 방법:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def setup_directories():
    """필요한 디렉토리 생성"""
    directories = [
        'temp_videos',
        'analysis_results', 
        'static/results',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("디렉토리 설정 완료")

def run_development_server():
    """개발 서버 실행"""
    print("개발 서버 시작 중...")
    print("브라우저에서 http://localhost:5000 접속")
    
    # Flask 앱 실행
    from poker_analyzer_app import app
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

def run_production_server(port=5000, workers=4):
    """프로덕션 서버 실행 (Gunicorn 사용)"""
    try:
        import gunicorn
    except ImportError:
        print("Gunicorn이 설치되지 않았습니다.")
        print("설치 방법: pip install gunicorn")
        return False
    
    print(f"프로덕션 서버 시작 (포트: {port}, 워커: {workers})")
    
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', str(workers),
        '--timeout', '300',  # 5분 타임아웃 (긴 분석 시간 고려)
        '--worker-class', 'sync',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        'poker_analyzer_app:app'
    ]
    
    subprocess.run(cmd)

def install_dependencies():
    """종속성 설치"""
    print("종속성 설치 중...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("종속성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"종속성 설치 실패: {e}")
        return False

def check_system_requirements():
    """시스템 요구사항 확인"""
    print("시스템 요구사항 확인 중...")
    
    # Python 버전 확인
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("Python 3.8 이상이 필요합니다.")
        return False
    
    print(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 메모리 확인
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.total < 4 * 1024 * 1024 * 1024:  # 4GB
            print("권장 메모리: 4GB 이상 (현재: {:.1f}GB)".format(memory.total / 1024**3))
        else:
            print(f"메모리: {memory.total / 1024**3:.1f}GB")
    except ImportError:
        print("psutil 패키지가 없어 메모리 확인을 건너뜀")
    
    # 디스크 공간 확인
    try:
        import shutil
        disk_usage = shutil.disk_usage('.')
        free_gb = disk_usage.free / 1024**3
        if free_gb < 5:
            print(f"권장 디스크 공간: 5GB 이상 (현재: {free_gb:.1f}GB)")
        else:
            print(f"디스크 공간: {free_gb:.1f}GB 사용 가능")
    except:
        print("디스크 공간 확인 실패")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='포커 대회 영상 분석 앱',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 개발 모드로 실행
  python run_poker_app.py dev
  
  # 프로덕션 모드로 실행
  python run_poker_app.py prod --port 8000 --workers 6
  
  # 종속성 설치
  python run_poker_app.py install
  
  # 시스템 체크
  python run_poker_app.py check
        """
    )
    
    parser.add_argument('mode', choices=['dev', 'prod', 'install', 'check'],
                       help='실행 모드')
    parser.add_argument('--port', type=int, default=5000,
                       help='서버 포트 (기본값: 5000)')
    parser.add_argument('--workers', type=int, default=4,
                       help='프로덕션 워커 수 (기본값: 4)')
    parser.add_argument('--skip-check', action='store_true',
                       help='종속성 확인 건너뛰기')
    
    args = parser.parse_args()
    
    print("포커 대회 영상 분석기")
    print("=" * 50)
    
    if args.mode == 'check':
        # 시스템 요구사항 확인
        if check_system_requirements():
            print("시스템 요구사항 충족")
        
        # 종속성 확인
        if check_dependencies():
            print("모든 종속성 설치됨")
        else:
            print("종속성 문제 발견")
            return 1
        
        return 0
    
    elif args.mode == 'install':
        # 종속성 설치
        if install_dependencies():
            print("설치 완료")
            return 0
        else:
            return 1
    
    # 서버 실행 모드
    if not args.skip_check:
        if not check_system_requirements():
            print("시스템 요구사항을 확인하세요")
            return 1
        
        if not check_dependencies():
            print("필수 종속성을 설치하세요: python run_poker_app.py install")
            return 1
    
    # 디렉토리 설정
    setup_directories()
    
    if args.mode == 'dev':
        run_development_server()
    elif args.mode == 'prod':
        run_production_server(args.port, args.workers)
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
        sys.exit(0)
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        sys.exit(1)