@echo off
echo Starting Poker MAM Test Server (No Redis/Celery required)
echo =========================================================
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing minimal requirements...
pip install fastapi uvicorn -q

echo.
echo Starting test server...
echo.

python simple_backend_test.py