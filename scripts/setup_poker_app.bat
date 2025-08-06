@echo off
echo 🃏 포커 대회 영상 분석기 설치 스크립트
echo =====================================

echo.
echo 📋 시스템 요구사항 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았거나 PATH에 없습니다.
    echo    Python 3.8 이상을 설치하고 PATH에 추가하세요.
    echo    다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 설치 확인됨

echo.
echo 📦 필수 종속성 설치 중...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 종속성 설치 실패
    echo    네트워크 연결을 확인하고 다시 시도하세요.
    pause
    exit /b 1
)

echo ✅ 종속성 설치 완료

echo.
echo 📁 필요한 디렉토리 생성 중...
mkdir temp_videos 2>nul
mkdir analysis_results 2>nul
mkdir static\results 2>nul

echo ✅ 디렉토리 설정 완료

echo.
echo 🔍 시스템 검사 실행...
python run_poker_app.py check

if errorlevel 1 (
    echo ❌ 시스템 검사 실패
    echo    위의 오류를 확인하고 수정하세요.
    pause
    exit /b 1
)

echo.
echo ✅ 설치 완료!
echo.
echo 🚀 실행 방법:
echo    개발 모드: python run_poker_app.py dev
echo    또는: run_dev.bat
echo.
echo 🌐 브라우저에서 http://localhost:5000 접속
echo.
pause