@echo off
REM POKER-BRAIN Quick Test Script
REM This script tests M4 RAG Search module (easiest to verify)

echo.
echo ========================================
echo  POKER-BRAIN Quick Test (M4 Module)
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "modules\m4-rag-search" (
    echo [ERROR] modules\m4-rag-search not found
    echo Please run this script from: D:\AI\claude01\archive-mam\
    pause
    exit /b 1
)

echo [1/5] Navigating to M4 module...
cd modules\m4-rag-search

echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [4/5] Installing dependencies...
pip install -r requirements.txt --quiet

echo [5/5] Running tests...
echo.
echo ========================================
echo  Running 66 tests (takes ~10 seconds)
echo ========================================
echo.

pytest tests\test_api.py -v --tb=short

echo.
echo ========================================
echo  Test Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run API server: python -m app.api
echo 2. Open new terminal and test: curl http://localhost:8004/health
echo.

pause
