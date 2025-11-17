# M5: Clipping Service

**담당**: DevOps Engineer / Backend Engineer (Eve)
**버전**: 1.0.0
**배포**: Local Agent (NAS Server) + Cloud Run (API)

---

## 개요

Pub/Sub 기반 비동기 비디오 클리핑 서비스입니다.

### 주요 기능

- ✅ Pub/Sub 비동기 처리
- ✅ FFmpeg 고속 클리핑 (-c copy)
- ✅ GCS 업로드 및 Signed URL
- ✅ High Availability (Primary + Standby)
- ✅ systemd Daemon

---

## 아키텍처

```
User (M6) → POST /v1/clip/request
    ↓
Pub/Sub Topic (clipping-requests)
    ↓
Local Agent (nas-server-01, subscribes)
    ├─ FFmpeg: ffmpeg -i input.mp4 -ss START -to END -c copy output.mp4
    ├─ GCS Upload: gs://gg-subclips/hand_id.mp4
    └─ Pub/Sub Publish (clipping-complete)
    ↓
M6 polls /v1/clip/{request_id}/status
    ↓
Signed URL → User Download (7일 유효)
```

**예상 처리 시간**: 2분 핸드 → ~30초

---

## API 스펙

**OpenAPI 3.0**: `openapi.yaml`

### 주요 엔드포인트

```bash
# 클리핑 요청
POST /v1/clip/request

# 상태 조회
GET /v1/clip/{request_id}/status

# Agent 상태 (관리자)
GET /v1/admin/agents

# Failover (관리자)
POST /v1/admin/agents/{agent_id}/failover
```

---

## Local Agent 구현

### systemd Service

```ini
# /etc/systemd/system/clipping-agent.service
[Unit]
Description=POKER-BRAIN Clipping Agent
After=network.target

[Service]
Type=simple
User=poker
WorkingDirectory=/opt/clipping-agent
ExecStart=/opt/clipping-agent/venv/bin/python src/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Agent 코드

```python
# src/agent.py
from google.cloud import pubsub_v1, storage
import ffmpeg

class ClippingAgent:
    def __init__(self, agent_id="nas-server-01"):
        self.agent_id = agent_id
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = "projects/gg-poker/subscriptions/clipping-worker"

    def callback(self, message):
        data = json.loads(message.data)

        # 1. FFmpeg 클리핑 (고속 -c copy)
        output = f"/tmp/{data['hand_id']}.mp4"
        ffmpeg.input(
            data['nas_video_path'],
            ss=data['start_seconds'],
            to=data['end_seconds']
        ).output(
            output,
            vcodec='copy',  # Re-encoding 없음 (빠름)
            acodec='copy'
        ).run(overwrite_output=True)

        # 2. GCS 업로드
        gcs_path = f"gs://gg-subclips/{data['hand_id']}.mp4"
        storage_client = storage.Client()
        bucket = storage_client.bucket("gg-subclips")
        blob = bucket.blob(f"{data['hand_id']}.mp4")
        blob.upload_from_filename(output)

        # 3. Signed URL 생성
        url = blob.generate_signed_url(expiration=timedelta(days=7))

        # 4. 완료 알림
        publisher = pubsub_v1.PublisherClient()
        publisher.publish("projects/gg-poker/topics/clipping-complete", json.dumps({
            "request_id": data['request_id'],
            "status": "completed",
            "download_url": url
        }).encode())

        message.ack()

    def run(self):
        self.subscriber.subscribe(self.subscription_path, callback=self.callback)
        while True:
            time.sleep(60)

if __name__ == "__main__":
    agent = ClippingAgent()
    agent.run()
```

---

## High Availability

### Primary + Standby 설정

```
nas-server-01 (Primary):
  - Active: 모든 메시지 처리
  - Heartbeat: 매 30초

nas-server-02 (Standby):
  - Standby: 대기
  - Health Check: Primary 상태 확인 (매 30초)
  - Failover: Primary 3회 연속 실패 시 자동 전환
```

### Failover 로직

```python
# src/health_checker.py
def check_primary():
    try:
        response = requests.get("http://nas-server-01:8005/health")
        return response.status_code == 200
    except:
        return False

# Standby Agent
primary_failures = 0
while True:
    if not check_primary():
        primary_failures += 1
        if primary_failures >= 3:
            # Failover: Standby → Primary
            switch_to_primary()
    else:
        primary_failures = 0
    time.sleep(30)
```

---

## 배포

### Local Agent 배포

```bash
# NAS 서버에서 실행
cd /opt/clipping-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# systemd 등록
sudo cp clipping-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable clipping-agent
sudo systemctl start clipping-agent

# 상태 확인
sudo systemctl status clipping-agent
```

### Cloud Run API 배포

```bash
gcloud run deploy clipping-service \
  --source . \
  --region us-central1
```

---

**담당자**: aiden.kim@ggproduction.net
**최종 업데이트**: 2025-11-17
