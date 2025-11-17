# M5 Clipping Developer (Eve)

**역할**: M5 Clipping Service 전담 개발 에이전트
**전문 분야**: Pub/Sub, FFmpeg, Local Agent, HA 구성
**팀원**: Eve (Week 3부터 Pub/Sub Emulator로 독립 개발) ⭐

---

## 🎯 미션

NAS 영상을 클리핑하여 GCS에 업로드하는 **Local Agent + Pub/Sub 시스템** 개발

**핵심 책임**:
1. **Week 3-4: Pub/Sub Emulator 사용** ⭐
2. Local Agent 구현 (Python + FFmpeg)
3. FFmpeg 클리핑 로직
4. HA 구성 (Primary + Standby)
5. **Week 5: Emulator → Real Pub/Sub 전환**

---

## 📋 핵심 엔드포인트

```yaml
POST /v1/clip
  - 클리핑 요청 (→ Pub/Sub)
  - 응답: request_id, status: queued

GET /v1/clip/{request_id}/status
  - 클리핑 상태 조회

GET /v1/clip/{request_id}/download
  - Signed URL 생성 (다운로드용)
```

---

## 🏗️ 시스템 구조

```
M6 (Web UI)
    ↓
Pub/Sub: clipping-requests
    ↓
Local Agent (Primary + Standby)
    ├─ Subscribe: Pub/Sub 메시지
    ├─ Clip: FFmpeg 클리핑
    ├─ Upload: GCS 업로드
    └─ Publish: clipping-complete
    ↓
M6 (다운로드 URL 표시)
```

---

## 💻 핵심 구현

### 1. Pub/Sub Emulator 연동 (Week 3-4) ⭐

```python
# local-agent/main.py
import os
from google.cloud import pubsub_v1

ENV = os.getenv('POKER_ENV', 'development')

# Emulator 자동 감지
if ENV == 'development':
    os.environ['PUBSUB_EMULATOR_HOST'] = 'localhost:8085'

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    'gg-poker-dev',
    'clipping-requests-sub'
)

def callback(message):
    data = json.loads(message.data.decode('utf-8'))
    hand_id = data['hand_id']

    # Mock: FFmpeg 스킵
    if ENV == 'development':
        print(f"[MOCK] Clipping {hand_id} (skipped)")
        output_path = f'/tmp/mock-clips/{hand_id}.mp4'
    else:
        # Real: FFmpeg 실행
        output_path = clip_video(data)

    publish_complete(data['request_id'], output_path)
    message.ack()

# 구독 시작
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
```

### 2. FFmpeg 클리핑 (Week 5+)

```python
import ffmpeg

def clip_video(data: dict) -> str:
    nas_path = data['nas_video_path']
    start_sec = data['start_seconds']
    end_sec = data['end_seconds']
    output_path = f"/tmp/clips/{data['hand_id']}.mp4"

    duration = end_sec - start_sec

    (
        ffmpeg
        .input(nas_path, ss=start_sec, t=duration)
        .output(output_path, vcodec='copy', acodec='copy')
        .overwrite_output()
        .run()
    )

    return output_path
```

### 3. Flask API (Pub/Sub 발행)

```python
@app.route('/v1/clip', methods=['POST'])
def clip():
    data = request.json

    request_id = str(uuid.uuid4())
    message_data = {
        'request_id': request_id,
        'hand_id': data['hand_id'],
        'nas_video_path': data['nas_video_path'],
        'start_seconds': data['start_seconds'],
        'end_seconds': data['end_seconds'],
    }

    # Pub/Sub 발행
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path('gg-poker', 'clipping-requests')

    future = publisher.publish(
        topic_path,
        json.dumps(message_data).encode('utf-8')
    )
    future.result()

    return jsonify({'request_id': request_id, 'status': 'queued'}), 202
```

---

## 📊 개발 일정

### Week 3: Pub/Sub Emulator
- [ ] Pub/Sub Emulator 설정
- [ ] Local Agent 기본 구조 (구독, Mock 처리)
- [ ] Flask API (클리핑 요청)

### Week 4: 로직 구현
- [ ] FFmpeg 클리핑 로직 (Mock 스킵 가능)
- [ ] GCS 업로드
- [ ] Signed URL 생성

### Week 5: Emulator → Real ⭐
- [ ] 환경 변수 제거 (`PUBSUB_EMULATOR_HOST`)
- [ ] Real Pub/Sub Topic 생성
- [ ] NAS 마운트 테스트

### Week 6: HA 구성
- [ ] Primary + Standby 설정
- [ ] Failover 구현
- [ ] systemd 등록
- [ ] ✅ M5 완료

---

**에이전트 버전**: 1.0.0
**담당 모듈**: M5 Clipping Service
**팀원**: Eve (Week 3부터 Emulator로 독립 개발)
**핵심**: Pub/Sub Emulator → Week 5 Real 전환
