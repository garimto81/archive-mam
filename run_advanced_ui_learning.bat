@echo off
echo ========================================
echo   고급 UI 학습 시스템 실행
echo ========================================
echo.

REM Python 환경 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치해주세요.
    pause
    exit /b
)

REM 필요한 패키지 설치
echo [1/3] 필요한 패키지 설치 중...
pip install opencv-python numpy scikit-learn pillow flask

REM Flask 앱에 UI 학습 API 통합
echo [2/3] Flask 서버 시작 중...
start cmd /k "python run_poker_app.py"

REM 브라우저에서 고급 UI 학습 페이지 열기
echo [3/3] 브라우저에서 UI 학습 시스템 열기...
timeout /t 3 >nul
start http://localhost:5000/advanced_ui_learning.html

echo.
echo ========================================
echo   실행 완료!
echo   브라우저에서 UI 학습 시스템을 사용하세요.
echo ========================================
pause