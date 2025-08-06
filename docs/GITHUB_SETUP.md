# 🐙 초보자를 위한 GitHub 저장소 설정 가이드

## 1. GitHub 저장소 생성 (웹에서)

### 단계별 설정:
1. https://github.com 접속 후 로그인
2. 우상단 "+" 버튼 클릭 → "New repository" 선택
3. 저장소 설정:
   - **Repository name**: `archive-mam`
   - **Description**: `🃏 AI 기반 포커 영상 분석 도구`
   - **Public** 선택 (무료 GitHub Pages 사용 가능)
   - **Add a README file** 체크 해제 (기존 파일이 있으므로)

### 저장소 연결:
```bash
# 로컬 프로젝트 폴더에서 실행
cd your-project-folder

# Git 초기화 (처음만)
git init

# 원격 저장소 연결
git remote add origin https://github.com/your-username/archive-mam.git

# 첫 번째 업로드
git add .
git commit -m "Initial commit: Add poker analyzer project"
git branch -M main
git push -u origin main
```

## 2. GitHub Pages 자동 배포 설정

### 간단한 방법:
1. GitHub 저장소 → **Settings** 탭
2. 왼쪽 메뉴 → **Pages**
3. **Source** → **Deploy from a branch**
4. **Branch** → **main** 선택
5. **Save** 클릭

### 자동 배포 확인:
- 5-10분 후 `https://your-username.github.io/archive-mam/` 접속
- 변경사항을 push할 때마다 자동으로 업데이트

## 3. 기본 파일들 설정

### README.md 작성:
```markdown
# 🃏 Poker Hand Analyzer

AI 기반 포커 영상 분석 도구

## 🚀 온라인 데모
https://your-username.github.io/archive-mam/

## 📋 주요 기능
- 포커 영상 업로드 및 분석
- AI 기반 핸드 자동 감지
- 결과 JSON 다운로드

## 💻 사용 방법
1. 웹사이트 접속
2. 영상 파일 업로드
3. 분석 결과 확인
```

### .gitignore 파일 생성:
```bash
# .gitignore 파일 내용
.DS_Store
Thumbs.db
*.log
node_modules/
temp_videos/
*.tmp
```

## 4. 일상적인 업데이트 방법

### 변경사항 반영:
```bash
# 1. 파일 수정 후
git add .
git commit -m "Update: 변경 내용을 간단히 설명"
git push origin main

# 2. 자동으로 웹사이트 업데이트 (5-10분 소요)
```

### 커밋 메시지 예시:
```bash
git commit -m "Add: 새로운 기능 추가"
git commit -m "Fix: 버그 수정"
git commit -m "Update: UI 개선"
git commit -m "Docs: 문서 업데이트"
```

## 5. 브랜치 관리 (선택사항)

### 기본 브랜치만 사용:
```bash
# main 브랜치에서 모든 작업
git add .
git commit -m "변경사항"
git push origin main
```

### 개발/배포 분리 (고급):
```bash
# 개발 브랜치 생성
git checkout -b develop
git push -u origin develop

# 개발 완료 후 main으로 병합
git checkout main
git merge develop
git push origin main
```

## 6. 문제 해결

### 자주 발생하는 오류들:

#### 1. "Permission denied" 오류
**해결방법:**
```bash
# Personal Access Token 사용
# GitHub → Settings → Developer settings → Personal access tokens
# 토큰 생성 후 비밀번호 대신 사용
```

#### 2. "Repository not found" 오류
**해결방법:**
```bash
# 원격 저장소 URL 확인
git remote -v

# URL 수정
git remote set-url origin https://github.com/your-username/archive-mam.git
```

#### 3. "Cannot push to main branch" 오류
**해결방법:**
```bash
# 강제 푸시 (주의해서 사용)
git push origin main --force

# 또는 pull 후 다시 push
git pull origin main
git push origin main
```

## 7. 유용한 Git 명령어

### 기본 명령어:
```bash
# 현재 상태 확인
git status

# 변경사항 보기
git diff

# 커밋 히스토리 보기
git log --oneline

# 마지막 커밋 취소
git reset --soft HEAD~1

# 파일 추가 취소
git reset HEAD filename.html
```

### 브랜치 관리:
```bash
# 현재 브랜치 확인
git branch

# 새 브랜치 생성 및 이동
git checkout -b new-feature

# 브랜치 삭제
git branch -d branch-name
```

## 8. GitHub 저장소 관리

### 저장소 설정:
- **Settings → General**: 저장소 이름, 설명 변경
- **Settings → Pages**: GitHub Pages 설정 확인
- **Code → Add file**: 웹에서 직접 파일 추가/편집 가능

### 협업 설정 (선택사항):
- **Settings → Manage access**: 협업자 추가
- **Issues**: 버그 리포트, 기능 요청 관리
- **Discussions**: 일반적인 토론

## 9. 백업 및 복원

### 프로젝트 백업:
```bash
# 전체 저장소 복제
git clone https://github.com/your-username/archive-mam.git backup-folder

# 또는 ZIP 다운로드
# GitHub 저장소 → Code → Download ZIP
```

### 복원 방법:
```bash
# 새 폴더에서 저장소 복제
git clone https://github.com/your-username/archive-mam.git
cd archive-mam

# 최신 상태로  업데이트
git pull origin main
```

---

## 📞 도움이 필요할 때

- **Git 기초**: https://git-scm.com/docs
- **GitHub 가이드**: https://guides.github.com/
- **GitHub Pages**: https://pages.github.com/
- **문제 해결**: GitHub Issues 탭에서 질문

**🎉 이제 GitHub로 프로젝트를 관리할 수 있습니다!**