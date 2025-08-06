# Poker MAM 프로덕션 배포 가이드

## 개요

이 문서는 Poker MAM 시스템을 프로덕션 환경에 배포하는 방법을 설명합니다.

## 배포 옵션

### 1. Docker Compose (권장)

가장 간단하고 안정적인 배포 방법입니다.

#### 사전 요구사항
- Docker 20.10+
- Docker Compose v2+
- 최소 4GB RAM, 20GB 디스크 공간

#### 배포 단계

1. **리포지토리 클론**
   ```bash
   git clone <repository-url>
   cd Archive-MAM
   ```

2. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일 편집
   ```

3. **디렉토리 권한 설정**
   ```bash
   mkdir -p uploads clips videos analysis_results
   chmod 755 uploads clips videos analysis_results
   ```

4. **서비스 시작**
   ```bash
   docker-compose up -d
   ```

5. **상태 확인**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

#### 서비스 접속
- **프론트엔드**: http://localhost (또는 도메인)
- **API 문서**: http://localhost:8000/docs
- **Redis**: localhost:6379

### 2. 수동 배포

더 세밀한 제어가 필요한 경우 수동 배포를 선택할 수 있습니다.

#### 백엔드 배포

1. **Python 환경 설정**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **시스템 의존성 설치**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ffmpeg tesseract-ocr tesseract-ocr-eng
   
   # CentOS/RHEL
   sudo yum install ffmpeg tesseract
   
   # macOS
   brew install ffmpeg tesseract
   ```

3. **데이터베이스 초기화**
   ```bash
   python -c "from src.database import create_db_tables; create_db_tables()"
   ```

4. **Redis 시작**
   ```bash
   redis-server
   ```

5. **Celery Worker 시작**
   ```bash
   python run_celery.py
   ```

6. **API 서버 시작**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
   ```

#### 프론트엔드 배포

1. **빌드**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **웹 서버 설정**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/frontend/build;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       location /api/ {
           proxy_pass http://localhost:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 프로덕션 설정

### 환경 변수

`.env` 파일 예시:
```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost/poker_mam

# Redis
REDIS_URL=redis://localhost:6379/0

# 보안
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# 외부 서비스
SENTRY_DSN=your-sentry-dsn

# 파일 저장소
UPLOAD_PATH=/var/poker-mam/uploads
CLIPS_PATH=/var/poker-mam/clips

# 로깅
LOG_LEVEL=INFO
LOG_FILE=/var/log/poker-mam/app.log
```

### 데이터베이스 (PostgreSQL 권장)

1. **PostgreSQL 설치 및 설정**
   ```bash
   sudo apt-get install postgresql postgresql-contrib
   sudo -u postgres createuser poker_mam
   sudo -u postgres createdb poker_mam_db -O poker_mam
   ```

2. **연결 문자열 업데이트**
   ```env
   DATABASE_URL=postgresql://poker_mam:password@localhost/poker_mam_db
   ```

### 보안 설정

1. **방화벽 설정**
   ```bash
   # UFW 사용 예시
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **SSL/TLS 인증서**
   ```bash
   # Let's Encrypt 사용
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

3. **사용자 권한**
   ```bash
   # 전용 사용자 생성
   sudo useradd -r -s /bin/false poker-mam
   sudo chown -R poker-mam:poker-mam /var/poker-mam
   ```

## 모니터링 및 로깅

### 로그 설정

1. **systemd 로그**
   ```bash
   journalctl -u poker-mam-api -f
   journalctl -u poker-mam-celery -f
   ```

2. **애플리케이션 로그**
   ```bash
   tail -f /var/log/poker-mam/app.log
   tail -f /var/log/poker-mam/celery.log
   ```

### 헬스체크

1. **API 상태 확인**
   ```bash
   curl -f http://localhost:8000/
   ```

2. **자동 모니터링 스크립트**
   ```bash
   #!/bin/bash
   # health-check.sh
   if ! curl -f http://localhost:8000/ > /dev/null 2>&1; then
       echo "API 서버가 응답하지 않습니다" | mail -s "Poker MAM Alert" admin@domain.com
       systemctl restart poker-mam-api
   fi
   ```

### 백업

1. **데이터베이스 백업**
   ```bash
   # 매일 자동 백업
   0 2 * * * pg_dump poker_mam_db > /backup/poker_mam_$(date +\%Y\%m\%d).sql
   ```

2. **파일 백업**
   ```bash
   # 업로드된 파일 백업
   0 3 * * * rsync -av /var/poker-mam/uploads/ /backup/uploads/
   ```

## 성능 최적화

### 1. 웹 서버 최적화

```nginx
# worker 프로세스 수 설정
worker_processes auto;

# 연결 제한
worker_connections 1024;

# 버퍼 크기 최적화
client_body_buffer_size 128k;
client_max_body_size 2G;

# 캐싱 설정
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 2. 데이터베이스 최적화

```sql
-- 인덱스 생성
CREATE INDEX idx_hands_video_id ON hands(video_id);
CREATE INDEX idx_hands_start_time ON hands(start_time_s);
CREATE INDEX idx_videos_status ON videos(status);

-- 통계 업데이트
ANALYZE;
```

### 3. Redis 설정

```conf
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 트러블슈팅

### 일반적인 문제

1. **메모리 부족**
   ```bash
   # 메모리 사용량 확인
   free -h
   docker stats
   
   # Celery worker 수 조정
   celery -A src.celery_app worker --concurrency=2
   ```

2. **디스크 공간 부족**
   ```bash
   # 오래된 로그 파일 정리
   find /var/log -name "*.log" -mtime +30 -delete
   
   # 임시 파일 정리
   rm -rf /tmp/celery-*
   ```

3. **포트 충돌**
   ```bash
   # 포트 사용 확인
   netstat -tlnp | grep :8000
   lsof -i :8000
   ```

### 로그 분석

```bash
# 에러 로그 필터링
grep ERROR /var/log/poker-mam/app.log | tail -50

# 성능 이슈 확인
grep "slow" /var/log/nginx/access.log

# Celery 작업 실패 확인
grep FAILURE /var/log/poker-mam/celery.log
```

## 업데이트 및 유지보수

### 롤링 업데이트

1. **Docker Compose 업데이트**
   ```bash
   docker-compose pull
   docker-compose up -d --no-deps backend
   docker-compose up -d --no-deps frontend
   ```

2. **수동 배포 업데이트**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   python -c "from src.database import create_db_tables; create_db_tables()"
   systemctl restart poker-mam-api
   systemctl restart poker-mam-celery
   ```

### 정기 유지보수

- **매주**: 로그 분석 및 성능 확인
- **매월**: 보안 업데이트 및 백업 검증
- **분기별**: 전체 시스템 성능 검토 및 최적화

## 지원 및 문의

- **GitHub**: [프로젝트 리포지토리]
- **이슈 트래킹**: GitHub Issues
- **문서**: 프로젝트 Wiki