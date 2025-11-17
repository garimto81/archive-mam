# 📄 **PRD (업데이트 버전 v1.2)**

### *RAG = Vertex AI / Video = NAS + AWS S3 Hybrid Architecture*

---

## 1. 개요 (변경 없음 + 확장 반영)

GGProduction은 NSUS ATI 팀이 만든 **핸드 분석 로우 데이터**를 기반으로
Google Cloud Vertex AI를 활용한 RAG 검색 시스템을 구축하고,
영상 데이터(NAS)를 기반으로 **서브클립 생성 및 글로벌 배포** 기능을 제공한다.

---

## 2. 시스템 핵심 요약 (업데이트 반영)

### 데이터/AI 영역

* **Vertex AI 기반 RAG 시스템**
* LLM Summarization
* Embedding / Vector Search
* Metadata Indexing
* Hand→Video 타임코드 매핑

### 영상 영역

* **원본 영상: NAS 저장**
* **서브클립 생성: NAS → FFmpeg → GCS or NAS**
* **Global Access: AWS S3 업로드 (선택적 / 정책 기반)**
* 필요 시 CloudFront CDN으로 글로벌 지사에서 빠르게 다운로드 가능

---

# 3. 기능 요구사항 업데이트

## 3.1 RAG 시스템: Google Vertex AI로 확정 (신규 명시)

### FR-AI1. Summarization Engine

* Vertex AI Gemini 기반 Summarization API 사용

### FR-AI2. Embedding Engine

* `vertex-ai textembedding-004` 또는 `multimodalembedding` 모델 사용
* 한글/영문 모두 지원

### FR-AI3. Vector Store

* Vertex AI Vector Search (유사도 검색)

### FR-AI4. RAG Pipeline

* Vertex AI RAG API 기반
* Retrieval → Augmentation → LLM Response

### FR-AI5. Security & Access

* IAM 기반 Project별 접근 제어
* NSUS ATI / GGProduction 내부만 접근 허용

---

# 4. 영상 저장/전송 구조 업데이트

## 4.1 현재 (Phase 1)

### FR-V1. Video Source = On-prem NAS

* 모든 Day별 Full Footage 파일은 NAS에 저장
* API는 NAS SMB/NFS 경로를 참조하여 타임코드 기반 ffmpeg 처리
* Random Access의 지연 시간이 매우 짧으므로 NAS 유지

### FR-V2. Subclip Creation

* Subclip 생성 시:

  ```
  ffmpeg -ss {start} -to {end} -i /nas/videos/ft1_day3.mp4 -c copy {hand_id}.mp4
  ```
* 생성 파일은:

  * NAS `/subclips/hand_id.mp4`
  * 또는 GCS 업로드(옵션)

---

## 4.2 향후 (Phase 2)

### FR-V3. Global Access (AWS S3)

* 완성된 subclip은 자동으로:

  ```
  AWS S3: s3://ggpocket-hands/{event}/{hand_id}.mp4
  ```
* S3 업로드 후:

  * CloudFront CDN
  * Signed URL (5분·1시간·24시간 등 옵션)

### FR-V4. Hybrid Pipeline

핵심은 “영상 원본은 NAS, 배포는 AWS”.

구조:

```
           NAS (원본 영상)
                |
           FFmpeg Subclip
                |
      ┌─────────┴─────────┐
      |                   |
   GCS 저장             AWS S3 업로드
      |                   |
   내부 팀 사용       전세계 지사/파트너 접근
```

---

# 5. 전체 아키텍처 업데이트

```
                NSUS ATI Raw Data
                        |
                     BigQuery
                (Hand Normalize)
                        |
      ┌────────────┬─────────────┐
      |             |             |
 Summary LLM   Tagging LLM   Embedding Model
(Vertex AI)    (Vertex AI)   (Vertex AI)
      └────────────┴─────────────┘
            Vertex AI Vector Search
                        |
                  RAG Search API
                        |
                Web UI / Ops Tool
                        |
           ┌────────────┴─────────────┐
           |                            |
   (Playback) Video Player           Subclip API
           |                            |
      NAS 원본 영상              FFmpeg@NAS → GCS/S3
```

---

# 6. 요구사항 요약 (업데이트 반영)

| 영역            | 기술                      |
| ------------- | ----------------------- |
| RAG           | Vertex AI               |
| Embedding     | Vertex AI TextEmbedding |
| Summarization | Gemini                  |
| Vector Store  | Vertex AI Vector Search |
| 영상 원본         | NAS                     |
| 서브클립 생성       | FFmpeg (NAS)            |
| 글로벌 유통        | AWS S3 + CloudFront     |

---

# 7. Phase Roadmap (신규)

### Phase 1 — 내부용 RAG + NAS 기반 서브클립

* NAS → FFmpeg → 내부용 subclip
* 내부 종편팀용 빠른 검색/하이라이트 생성
* Vertex AI RAG 완성

### Phase 2 — AWS S3 글로벌 확장

* 자동 S3 업로드
* CloudFront CDN
* 지사/외주/파트너가 영상 접근 가능

### Phase 3 — AI Highlight 자동 생성

* Video Embedding 추가
* 리액션/샷 자동 추출
* RAG + Vision 기반 자동 하이라이트 패키지

