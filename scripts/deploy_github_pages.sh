#!/bin/bash

echo "🚀 GitHub Pages 배포 스크립트"
echo "============================="

# Git 초기화 확인
if [ ! -d ".git" ]; then
    echo "Git 저장소가 아닙니다. 초기화합니다..."
    git init
fi

# 변경사항 추가
echo "📦 변경사항 추가 중..."
git add index.html
git add online_ui_learning.html
git add advanced_ui_learning.html
git add smart_ui_detector.html
git add ui_marking_tool.html
git add *.css *.js 2>/dev/null || true

# 커밋
echo "💾 커밋 생성 중..."
git commit -m "Add online UI learning system for GitHub Pages" || echo "변경사항이 없습니다."

# GitHub Pages 브랜치 설정
echo "🌿 GitHub Pages 브랜치 설정..."
git branch -M main

# 리모트 확인
if ! git remote | grep -q origin; then
    echo "⚠️  GitHub 리모트가 설정되지 않았습니다."
    echo "다음 명령을 실행하세요:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/archive-mam.git"
    exit 1
fi

# Push
echo "📤 GitHub에 푸시 중..."
git push -u origin main

echo ""
echo "✅ 배포 완료!"
echo "다음 단계:"
echo "1. GitHub 저장소로 이동: https://github.com/YOUR_USERNAME/archive-mam"
echo "2. Settings → Pages"
echo "3. Source: Deploy from a branch"
echo "4. Branch: main, Folder: / (root)"
echo "5. Save 클릭"
echo ""
echo "몇 분 후 다음 주소에서 확인 가능:"
echo "https://YOUR_USERNAME.github.io/archive-mam/"
echo "https://YOUR_USERNAME.github.io/archive-mam/online_ui_learning.html"