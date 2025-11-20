# Full Stack Server Start Script
# 백엔드 + 프론트엔드 동시 실행 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Full Stack Development Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Backend 서버 실행 (새 창)
Write-Host "[1/2] Starting Backend Server (Port 9000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; .\start_backend.ps1"

# 2초 대기
Start-Sleep -Seconds 2

# Frontend 서버 실행 (새 창)
Write-Host "[2/2] Starting Frontend Server (Port 9001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; .\start_frontend.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Servers are starting in new windows!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:9000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:9001" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop servers, close the PowerShell windows or press Ctrl+C in each window." -ForegroundColor Yellow
