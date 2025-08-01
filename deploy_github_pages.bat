@echo off
echo ========================================
echo   GitHub Pages 배포 스크립트
echo ========================================
echo.

REM Git 초기화 확인
git status >nul 2>&1
if errorlevel 1 (
    echo Git 저장소가 아닙니다. 초기화합니다...
    git init
)

REM 변경사항 추가
echo [1/4] 변경사항 추가 중...
git add index.html
git add online_ui_learning.html
git add advanced_ui_learning.html
git add smart_ui_detector.html
git add ui_marking_tool.html

REM 커밋
echo [2/4] 커밋 생성 중...
git commit -m "Add online UI learning system for GitHub Pages"

REM GitHub Pages 브랜치 설정
echo [3/4] 브랜치 설정...
git branch -M main

REM Push
echo [4/4] GitHub에 푸시 중...
git push -u origin main

echo.
echo ========================================
echo   배포 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. GitHub 저장소로 이동
echo 2. Settings - Pages
echo 3. Source: Deploy from a branch
echo 4. Branch: main, Folder: / (root)
echo 5. Save 클릭
echo.
echo 몇 분 후 확인:
echo https://garimto81.github.io/archive-mam/
echo https://garimto81.github.io/archive-mam/online_ui_learning.html
echo.
pause