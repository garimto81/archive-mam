@echo off
echo =================================
echo 포커 핸드 고속 분석 실행
echo =================================
echo.

REM Python 환경 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Python이 설치되어 있지 않습니다.
    echo https://www.python.org 에서 Python을 설치하세요.
    pause
    exit /b 1
)

REM 테스트 스크립트 실행
echo 고속 분석 테스트를 시작합니다...
echo.

if "%1"=="" (
    echo 샘플 비디오로 테스트를 실행합니다.
    python test_fast_detector.py
) else (
    echo 지정된 비디오 파일: %1
    python test_fast_detector.py "%1"
)

echo.
echo =================================
echo 테스트 완료
echo =================================
pause