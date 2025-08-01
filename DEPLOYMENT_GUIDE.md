# 🚀 초보자를 위한 GitHub Pages 배포 가이드

이 가이드는 초보 개발자를 위한 **GitHub Pages 기반 간단 배포** 방법을 안내합니다.

## 📋 목차
1. [GitHub Pages 배포](#github-pages-배포)
2. [로컬 개발 환경](#로컬-개발-환경)
3. [프로젝트 업데이트](#프로젝트-업데이트)
4. [문제 해결](#문제-해결)

## 🌐 GitHub Pages 배포

### 1단계: GitHub 저장소 생성
```bash
# 1. GitHub.com에서 새 저장소 생성
# - Repository name: archive-mam
# - Public 선택
# - README 체크 해제

# 2. 로컬에서 저장소 클론
git clone https://github.com/your-username/archive-mam.git
cd archive-mam
```

### 2단계: 파일 업로드
```bash
# 프로젝트 파일들을 저장소에 복사 후
git add .
git commit -m "Initial commit: Add poker analyzer files"
git push origin main
```

### 3단계: GitHub Pages 활성화
1. GitHub 저장소 페이지 → **Settings** 클릭
2. 왼쪽 메뉴에서 **Pages** 클릭
3. **Source** → **Deploy from a branch** 선택
4. **Branch** → **main** 선택
5. **Save** 클릭

### 4단계: 접속 확인
- 5-10분 후 `https://your-username.github.io/archive-mam/` 접속
- 초록색 체크 표시가 나타나면 배포 완료

## 🔧 로컬 개발 환경

### 간단한 로컬 서버 실행
```bash
# Python이 설치되어 있다면
cd archive-mam
python -m http.server 8000

# 브라우저에서 http://localhost:8000 접속
```

### Visual Studio Code 사용 (권장)
1. **Live Server** 확장 프로그램 설치
2. `index.html` 파일 우클릭 → **Open with Live Server**
3. 자동으로 브라우저에서 열림

## 📦 프로젝트 업데이트

### 변경사항 반영하기
```bash
# 1. 파일 수정 후
git add .
git commit -m "Update: 변경 내용 설명"
git push origin main

# 2. 5-10분 후 자동으로 웹사이트 업데이트
```

### 주요 파일들
- `index.html` - 메인 페이지
- `unified_ui_recognition.html` - 통합 UI 인식 시스템
- `optimized_ui_recognition.html` - 고속 UI 인식 시스템
- `README.md` - 프로젝트 설명

## 🔍 문제 해결

### 자주 발생하는 문제들

#### 1. 웹사이트가 안 열려요
**해결방법:**
```bash
# Actions 탭에서 배포 상태 확인
# GitHub 저장소 → Actions → 최근 워크플로우 확인
# 빨간 X 표시가 있으면 오류 발생, 로그 확인
```

#### 2. 변경사항이 반영 안 돼요
**해결방법:**
- 5-10분 정도 기다리기
- 브라우저 캐시 삭제 (Ctrl+F5)
- GitHub Pages 설정 다시 확인

#### 3. 파일이 업로드 안 돼요
**해결방법:**
```bash
# 파일 상태 확인
git status

# 강제로 모든 변경사항 추가
git add -A
git commit -m "Force update all files"
git push origin main
```

#### 4. 브라우저에서 파일이 로드 안 돼요
**해결방법:**
- 파일 경로 확인 (대소문자 구분)
- 특수문자나 공백이 있는 파일명 변경
- 브라우저 개발자 도구(F12)에서 오류 확인

## 📱 모바일에서 확인하기

스마트폰에서도 접속 가능:
- `https://your-username.github.io/archive-mam/`
- 모든 기능이 모바일에서도 작동

## 🎯 배포 체크리스트

배포 전 확인사항:
- [ ] 모든 파일이 GitHub에 업로드됨
- [ ] `index.html` 파일이 루트 디렉토리에 있음
- [ ] GitHub Pages 설정이 `main` 브랜치로 되어 있음
- [ ] 5-10분 후 웹사이트 접속 확인
- [ ] 모바일에서도 접속 확인

## 💡 유용한 팁

### Git 기본 명령어
```bash
# 현재 상태 확인
git status

# 변경사항 확인
git diff

# 이전 커밋으로 되돌리기
git reset --hard HEAD~1

# 강제 푸시 (주의해서 사용)
git push origin main --force
```

### 파일 구조 유지하기
```
archive-mam/
├── index.html (메인 페이지)
├── unified_ui_recognition.html
├── optimized_ui_recognition.html
├── README.md
└── assets/ (이미지, CSS, JS 파일들)
```

---

## 📞 도움이 필요하면

- **GitHub 저장소**: Issues 탭에서 질문 남기기
- **로컬 테스트**: VS Code + Live Server 사용 권장
- **오류 해결**: 브라우저 F12 → Console 탭에서 오류 확인

**🎉 이제 GitHub Pages로 간단하게 배포할 수 있습니다!**