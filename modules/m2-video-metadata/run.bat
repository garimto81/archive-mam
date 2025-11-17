@echo off
REM M2 Video Metadata Service - Windows Run Script

echo M2 Video Metadata Service - Starting...

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: FFmpeg is not installed
    echo Install FFmpeg: choco install ffmpeg
    exit /b 1
)

REM Load .env if exists
if exist .env (
    echo Loading .env file...
    for /f "tokens=*" %%a in (.env) do set %%a
)

REM Create virtual environment if needed
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run tests if --test flag
if "%1"=="--test" (
    echo Running tests...
    pytest tests/ -v --cov=app
)

REM Start server
set PORT=8002
echo Starting Flask server on port %PORT%...
echo Health check: http://localhost:%PORT%/health
echo.

python -m app.api
