# 🚀 Poker MAM 배포 가이드

이 가이드는 Poker MAM 시스템을 다양한 환경에 배포하는 방법을 안내합니다.

## 📋 목차
1. [로컬 개발 환경](#로컬-개발-환경)
2. [Docker 컨테이너 배포](#docker-컨테이너-배포)
3. [클라우드 플랫폼 배포](#클라우드-플랫폼-배포)
4. [프로덕션 환경 설정](#프로덕션-환경-설정)
5. [모니터링 및 유지보수](#모니터링-및-유지보수)

## 🔧 로컬 개발 환경

### 빠른 시작
```bash
# 저장소 클론
git clone https://github.com/your-username/Archive-MAM.git
cd Archive-MAM

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 종속성 설치
pip install -r requirements.txt

# 개발 서버 실행
python run_poker_app.py dev
```

### 환경 확인
```bash
# 시스템 요구사항 확인
python run_poker_app.py check

# 필요 시 자동 설치
python run_poker_app.py install
```

## 🐳 Docker 컨테이너 배포

### 단일 컨테이너 실행
```bash
# Docker 이미지 빌드
docker build -t poker-mam .

# 컨테이너 실행
docker run -d \
  --name poker-mam-app \
  -p 5000:5000 \
  -v $(pwd)/temp_videos:/app/temp_videos \
  -v $(pwd)/analysis_results:/app/analysis_results \
  poker-mam
```

### Docker Compose 사용 (권장)
```bash
# 메인 애플리케이션 실행
docker-compose up -d

# 기존 시스템과 함께 실행 (선택)
docker-compose --profile legacy up -d

# 개발 환경 실행
docker-compose --profile dev up -d
```

### Docker Hub 배포
```bash
# 이미지 태그 설정
docker tag poker-mam your-username/poker-mam:latest

# Docker Hub에 푸시
docker push your-username/poker-mam:latest
```

## ☁️ 클라우드 플랫폼 배포

### AWS EC2 배포

#### 1. EC2 인스턴스 설정
```bash
# Amazon Linux 2 기준
sudo yum update -y
sudo yum install -y docker git

# Docker 시작
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 애플리케이션 배포
```bash
# 저장소 클론
git clone https://github.com/your-username/Archive-MAM.git
cd Archive-MAM

# 환경 변수 설정
echo "FLASK_ENV=production" > .env
echo "FLASK_DEBUG=0" >> .env

# 애플리케이션 실행
docker-compose up -d

# 보안 그룹에서 5000 포트 열기 (AWS 콘솔)
```

### Google Cloud Run 배포

#### 1. Google Cloud SDK 설정
```bash
# gcloud CLI 설치 후
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 2. 컨테이너 배포
```bash
# 컨테이너 빌드 및 배포
gcloud run deploy poker-mam \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900
```

### Heroku 배포

#### 1. Heroku CLI 설정
```bash
# Heroku CLI 설치 후
heroku login
heroku create your-poker-mam-app
```

#### 2. 컨테이너 배포
```bash
# Heroku Container Registry 로그인
heroku container:login

# 컨테이너 빌드 및 푸시
heroku container:push web -a your-poker-mam-app
heroku container:release web -a your-poker-mam-app

# 환경 변수 설정
heroku config:set FLASK_ENV=production -a your-poker-mam-app
heroku config:set MAX_FILE_SIZE=10737418240 -a your-poker-mam-app
```

### Azure Container Instances 배포

```bash
# Azure CLI 로그인
az login

# 리소스 그룹 생성
az group create --name poker-mam-rg --location eastus

# 컨테이너 인스턴스 생성
az container create \
  --resource-group poker-mam-rg \
  --name poker-mam-app \
  --image your-username/poker-mam:latest \
  --dns-name-label poker-mam-unique \
  --ports 5000 \
  --memory 4 \
  --cpu 2
```

## 🏭 프로덕션 환경 설정

### Nginx 리버스 프록시 설정

#### nginx.conf
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 파일 업로드 크기 제한
    client_max_body_size 10G;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 긴 분석 시간을 위한 타임아웃 설정
        proxy_read_timeout 1800;
        proxy_connect_timeout 1800;
        proxy_send_timeout 1800;
    }

    # 정적 파일 직접 서빙
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### HTTPS 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo crontab -e
# 추가: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 환경 변수 설정
```bash
# /etc/environment 또는 .env 파일
FLASK_ENV=production
FLASK_DEBUG=0
MAX_FILE_SIZE=10737418240
TEMP_VIDEO_DIR=/app/temp_videos
RESULTS_DIR=/app/analysis_results
SECRET_KEY=your-super-secret-key-here
```

### 로그 관리
```bash
# 로그 디렉토리 생성
mkdir -p /var/log/poker-mam

# systemd 서비스 설정 (/etc/systemd/system/poker-mam.service)
[Unit]
Description=Poker MAM Analysis System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app
ExecStart=/usr/bin/python3 run_poker_app.py prod --port 5000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 📊 모니터링 및 유지보수

### 헬스체크 엔드포인트
```python
# poker_analyzer_app.py에 추가
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })
```

### 로그 모니터링
```bash
# 애플리케이션 로그 확인
docker logs poker-mam-app -f

# 시스템 로그 확인
journalctl -u poker-mam -f
```

### 성능 모니터링
```bash
# 리소스 사용량 확인
docker stats poker-mam-app

# 디스크 사용량 확인
df -h
du -sh temp_videos/ analysis_results/
```

### 백업 스크립트
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# 분석 결과 백업
tar -czf "$BACKUP_DIR/analysis_results_$DATE.tar.gz" analysis_results/

# 로그 백업
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /var/log/poker-mam/

# 오래된 백업 정리 (30일 이상)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 자동 업데이트 스크립트
```bash
#!/bin/bash
# update.sh
cd /app

# 최신 코드 가져오기
git pull origin main

# 컨테이너 재시작
docker-compose down
docker-compose build
docker-compose up -d

echo "Update completed: $(date)"
```

## 🔧 트러블슈팅

### 일반적인 문제들

#### 1. 메모리 부족
```bash
# 스왑 메모리 추가
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 2. 디스크 공간 부족
```bash
# 임시 파일 정리
find temp_videos/ -mtime +7 -delete
find analysis_results/ -mtime +30 -delete

# Docker 이미지 정리
docker system prune -a
```

#### 3. 포트 충돌
```bash
# 포트 사용 확인
netstat -tlnp | grep :5000

# 프로세스 종료
sudo kill -9 PID
```

## 📈 성능 최적화

### 웹 서버 설정
```python
# Gunicorn 설정 (gunicorn.conf.py)
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 1800
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
```

### 캐싱 설정
```nginx
# Nginx 캐싱
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /api/ {
    # API 응답 캐싱 (선택적)
    proxy_cache_valid 200 1m;
}
```

## 🔐 보안 설정

### 방화벽 설정
```bash
# UFW 방화벽 설정 (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSL/TLS 보안 강화
```nginx
# nginx.conf 보안 헤더
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

---

## 📞 지원

배포 과정에서 문제가 발생하면:
- [GitHub Issues](https://github.com/your-username/Archive-MAM/issues)
- [배포 FAQ](https://github.com/your-username/Archive-MAM/wiki/Deployment-FAQ)
- [커뮤니티 디스커션](https://github.com/your-username/Archive-MAM/discussions)

**성공적인 배포를 위해 이 가이드를 단계별로 따라하세요! 🚀**