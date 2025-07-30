# 🐙 GitHub 저장소 설정 가이드

## 1. GitHub 저장소 생성

### 웹 브라우저에서:
1. https://github.com 접속
2. 우상단 "+" 버튼 클릭 → "New repository" 선택
3. 저장소 설정:
   - **Repository name**: `Archive-MAM` 또는 `Poker-MAM`
   - **Description**: `🃏 AI-powered poker tournament video analysis system with hand boundary detection and length classification`
   - **Public/Private**: Public 권장 (오픈소스 프로젝트)
   - **Initialize this repository with**: 체크 해제 (기존 코드가 있으므로)

### 명령어로 원격 저장소 연결:
```bash
# GitHub 저장소 생성 후 실행 (your-username을 실제 GitHub 사용자명으로 변경)
cd C:\claude\Archive-MAM

# 원격 저장소 추가
git remote add origin https://github.com/your-username/Archive-MAM.git

# 기본 브랜치 설정
git branch -M main

# 첫 번째 푸시
git push -u origin main
```

## 2. GitHub CLI 사용 (선택사항)

GitHub CLI가 설치되어 있다면:
```bash
# GitHub CLI로 저장소 생성
gh repo create Archive-MAM --public --description "🃏 AI-powered poker tournament video analysis system"

# 원격 저장소 연결 및 푸시
git remote add origin https://github.com/$(gh api user --jq .login)/Archive-MAM.git
git push -u origin main
```

## 3. 저장소 설정 최적화

### Branch Protection Rules 설정:
1. GitHub 저장소 → Settings → Branches
2. "Add rule" 클릭
3. Branch name pattern: `main`
4. 다음 옵션 활성화:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging

### Issues 템플릿 생성:
```bash
mkdir -p .github/ISSUE_TEMPLATE
```

**Bug Report** (`.github/ISSUE_TEMPLATE/bug_report.md`):
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. Windows 10, Ubuntu 20.04]
- Python version: [e.g. 3.9.7]
- Browser: [e.g. chrome, safari]

**Additional context**
Add any other context about the problem here.
```

**Feature Request** (`.github/ISSUE_TEMPLATE/feature_request.md`):
```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

### Pull Request 템플릿 생성:
**Pull Request Template** (`.github/pull_request_template.md`):
```markdown
## Description
Brief description of changes made in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots to help explain the changes.

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
```

## 4. GitHub Actions 워크플로우

### CI/CD 파이프라인 (`.github/workflows/ci.yml`):
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python run_poker_app.py check
        pytest test/ -v --cov=src/
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  docker:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t poker-mam .
    
    - name: Test Docker container
      run: |
        docker run -d --name test-container -p 5000:5000 poker-mam
        sleep 30
        curl -f http://localhost:5000/health || exit 1
        docker stop test-container
```

### 자동 배포 워크플로우 (`.github/workflows/deploy.yml`):
```yaml
name: Deploy to Production

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Cloud Run
      uses: google-github-actions/deploy-cloudrun@v1
      with:
        service: poker-mam
        image: gcr.io/PROJECT_ID/poker-mam:${{ github.sha }}
        region: us-central1
        credentials: ${{ secrets.GCP_CREDENTIALS }}
```

## 5. 보안 설정

### Secrets 관리:
1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. 다음 secrets 추가:
   - `GCP_CREDENTIALS`: Google Cloud 서비스 계정 키
   - `DOCKER_USERNAME`: Docker Hub 사용자명
   - `DOCKER_PASSWORD`: Docker Hub 토큰
   - `HEROKU_API_KEY`: Heroku API 키

### Dependabot 설정 (`.github/dependabot.yml`):
```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## 6. 최종 커밋 및 푸시

```bash
# GitHub 템플릿 및 워크플로우 추가
git add .github/
git commit -m "feat: Add GitHub templates and CI/CD workflows

- Add issue and PR templates for better collaboration
- Implement CI/CD pipeline with Python testing and Docker builds
- Add automated deployment workflows for cloud platforms
- Configure Dependabot for dependency updates
- Set up security scanning and code quality checks

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 원격 저장소에 푸시
git push -u origin main
```

## 7. 온라인 접속 URL

저장소 생성 후 다음 URL들을 통해 접속 가능:

### 저장소 URL:
- **GitHub**: `https://github.com/your-username/Archive-MAM`
- **Clone URL**: `https://github.com/your-username/Archive-MAM.git`

### 배포된 애플리케이션 URL (예시):
- **Heroku**: `https://your-poker-mam-app.herokuapp.com`
- **Google Cloud Run**: `https://poker-mam-xxxxx-uc.a.run.app`
- **AWS EC2**: `http://your-ec2-ip:5000`
- **Azure**: `https://poker-mam-unique.eastus.azurecontainer.io:5000`

### 문서 및 위키:
- **README**: `https://github.com/your-username/Archive-MAM#readme`
- **Wiki**: `https://github.com/your-username/Archive-MAM/wiki`
- **Issues**: `https://github.com/your-username/Archive-MAM/issues`
- **Discussions**: `https://github.com/your-username/Archive-MAM/discussions`

---

**이제 GitHub에서 프로젝트를 관리하고 전 세계 개발자들과 협업할 수 있습니다! 🌍✨**