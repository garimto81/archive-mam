# Frontend Server Start Script
# 프론트엔드 서버 실행 스크립트 (포트 9001)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Frontend Server Starting (Port 9001)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# .env.local 파일 확인 및 생성
Write-Host "`n[1/2] Checking .env.local file..." -ForegroundColor Yellow
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating .env.local file..." -ForegroundColor Yellow
    @"
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:9000

# Environment
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_ENABLE_MOCK_DATA=false
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_DEBUG=true
"@ | Out-File -FilePath ".env.local" -Encoding UTF8
    Write-Host ".env.local created successfully!" -ForegroundColor Green
}

# 서버 실행
Write-Host "[2/2] Starting Next.js server on http://localhost:9001..." -ForegroundColor Yellow
Write-Host "`nFrontend URL: http://localhost:9001" -ForegroundColor Green
Write-Host "Backend API: http://localhost:9000" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Magenta

npm run dev -- -p 9001
