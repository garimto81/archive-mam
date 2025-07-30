@echo off
echo Poker MAM Quick Test Script
echo ==========================
echo.

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo [2/4] Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    pause
    exit /b 1
)

echo.
echo [3/4] Checking FFmpeg...
ffmpeg -version 2>nul | findstr "version"
if errorlevel 1 (
    echo WARNING: FFmpeg not found! Video clip generation will not work.
)

echo.
echo [4/4] Checking project structure...
if exist "src\main.py" (
    echo Backend files: OK
) else (
    echo ERROR: Backend files not found!
)

if exist "frontend\package.json" (
    echo Frontend files: OK
) else (
    echo ERROR: Frontend files not found!
)

if exist "videos\sample_poker_video.mp4" (
    echo Sample video: OK
) else (
    echo Sample video not found. Generating...
    python -m src.generate_sample_video
)

echo.
echo ==========================
echo Environment check complete!
echo.
echo To start the system:
echo 1. Start Redis (in WSL): redis-server
echo 2. Run: start_backend.bat
echo 3. Run: start_frontend.bat
echo.
pause