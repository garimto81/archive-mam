# Backend Server Start Script
# 백엔드 서버 실행 스크립트 (포트 9000)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Backend Server Starting (Port 9000)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 가상환경 활성화
Write-Host "`n[1/3] Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# .env 파일 확인
Write-Host "[2/3] Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copying from .env.poc..." -ForegroundColor Red
    Copy-Item "..\.env.poc" ".env"
}

# 서버 실행
Write-Host "[3/3] Starting FastAPI server on http://localhost:9000..." -ForegroundColor Yellow
Write-Host "`nAPI Documentation: http://localhost:9000/docs" -ForegroundColor Green
Write-Host "Health Check: http://localhost:9000/health" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Magenta

uvicorn app.main:app --reload --port 9000
