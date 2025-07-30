@echo off
echo Starting Poker MAM Backend Services
echo ==================================
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting services...
echo.

echo [1] Starting Celery Worker in new window...
start "Celery Worker" cmd /k "venv\Scripts\activate && python run_celery.py"

timeout /t 3 /nobreak > nul

echo [2] Starting FastAPI Server in new window...
start "FastAPI Server" cmd /k "venv\Scripts\activate && python run_api.py"

timeout /t 3 /nobreak > nul

echo.
echo Backend services started!
echo.
echo API Documentation: http://localhost:8000/docs
echo.
echo Press any key to open API docs in browser...
pause > nul
start http://localhost:8000/docs