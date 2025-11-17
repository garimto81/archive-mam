# M3: Timecode Validation Service (Phase 0)

**담당**: Backend Engineer (Charlie)
**버전**: 1.0.0
**배포**: Cloud Run
**Phase**: Phase 0 (필수 사전 작업)

---

## 개요

ATI 타임스탬프와 NAS 영상 타임코드의 동기화를 검증하는 Phase 0 핵심 서비스입니다.

### 주요 기능

- ✅ Vision API 기반 포커 장면 감지
- ✅ sync_score 자동 계산 (0-100점)
- ✅ Offset 자동 계산
- ✅ 수동 매칭 인터페이스
- ✅ 배치 검증 (1000 hands)

---

## sync_score 알고리즘

```python
sync_score = (
    vision_confidence * 50 +    # Vision API 신뢰도
    duration_match * 30 +        # 길이 매칭
    player_count * 20            # 플레이어 수 매칭
)

# 판정 기준
if score >= 90:  "완벽 동기화"
elif score >= 80: "양호 (사용 가능)"
elif score >= 60: "Offset 계산 필요"
else: "수동 매칭 필요"
```

---

## API 스펙

**OpenAPI 3.0**: `openapi.yaml`

### 주요 엔드포인트

```bash
# 단일 검증
POST /v1/validate

# 배치 검증
POST /v1/validate/batch

# 수동 매칭
POST /v1/manual/match

# Offset 적용
POST /v1/offset/apply
```

---

## 로컬 개발

### Vision API 설정

```bash
# Vision API 활성화
gcloud services enable vision.googleapis.com

# Service Account 권한
gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:validation-sa@gg-poker.iam.gserviceaccount.com" \
  --role="roles/cloudvision.admin"
```

### 환경 설정

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```txt
google-cloud-vision==3.4.5
google-cloud-bigquery==3.13.0
ffmpeg-python==0.2.0
flask==3.0.0
pytest==7.4.3
```

---

## 핵심 로직

```python
# src/validator.py
from google.cloud import vision

def validate_timecode(hand, video_path) -> dict:
    # 1. 프레임 추출
    frame = extract_frame(video_path, hand.timestamp_start)

    # 2. Vision API 호출
    client = vision.ImageAnnotatorClient()
    objects = client.object_localization(image=frame)

    # 3. 포커 장면 감지
    poker_objects = ["table", "playing card", "poker chip"]
    confidence = sum(obj.score for obj in objects if obj.name in poker_objects) / len(poker_objects)

    # 4. sync_score 계산
    score = confidence * 50 + duration_match * 30 + player_count * 20

    # 5. Offset 계산 (필요 시)
    offset = calculate_offset(hand, video_path) if score < 80 else 0

    return {
        "sync_score": score,
        "is_synced": score >= 80,
        "calculated_offset": offset
    }
```

---

## 배포

```bash
gcloud run deploy timecode-validation-service \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 60s
```

---

**담당자**: aiden.kim@ggproduction.net
**최종 업데이트**: 2025-11-17
