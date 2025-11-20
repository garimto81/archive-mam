@echo off
REM ==================================================
REM Ollama 설치 및 Qwen3-8B 다운로드 스크립트 (Windows)
REM ==================================================

echo ===================================
echo Ollama Setup for Qwen3-8B
echo ===================================
echo.

REM Step 1: Ollama 설치 확인
echo [Step 1/4] Ollama 설치 여부 확인...
ollama --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Ollama가 이미 설치되어 있습니다.
    ollama --version
) else (
    echo ❌ Ollama가 설치되어 있지 않습니다.
    echo.
    echo Ollama를 수동으로 설치하세요:
    echo 1. https://ollama.com/download/windows 방문
    echo 2. OllamaSetup.exe 다운로드 및 실행
    echo 3. 설치 완료 후 이 스크립트를 다시 실행하세요.
    echo.
    pause
    exit /b 1
)

echo.

REM Step 2: Ollama 서비스 실행 확인
echo [Step 2/4] Ollama 서비스 실행 확인...
curl -s http://localhost:11434 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Ollama 서비스가 실행 중입니다.
) else (
    echo ⚠️  Ollama 서비스가 실행되지 않았습니다.
    echo 자동으로 Ollama 서비스를 시작합니다...
    start /B ollama serve
    timeout /t 5 /nobreak >nul
    echo ✅ Ollama 서비스가 시작되었습니다.
)

echo.

REM Step 3: Qwen3-8B 모델 다운로드
echo [Step 3/4] Qwen3-8B 모델 다운로드 (약 5.5GB, 시간이 걸릴 수 있습니다)...
echo.
ollama pull qwen3:8b

if %ERRORLEVEL% EQU 0 (
    echo ✅ Qwen3-8B 모델 다운로드 완료!
) else (
    echo ❌ Qwen3-8B 모델 다운로드 실패
    pause
    exit /b 1
)

echo.

REM Step 4: Qwen3-8B 테스트
echo [Step 4/4] Qwen3-8B 테스트...
echo.
echo 테스트 쿼리: "What is poker?"
echo.
ollama run qwen3:8b "What is poker? Answer in 2 sentences."

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Ollama + Qwen3-8B 설치 완료!
    echo ========================================
    echo.
    echo 다음 단계:
    echo 1. .env.poc 파일 확인 및 수정 (필요 시)
    echo 2. FastAPI 서버 실행:
    echo    cd backend
    echo    uvicorn app.main:app --reload
    echo.
    echo 3. Ollama API 엔드포인트 확인:
    echo    http://localhost:11434/v1
    echo.
) else (
    echo ❌ Qwen3-8B 테스트 실패
    pause
    exit /b 1
)

pause
