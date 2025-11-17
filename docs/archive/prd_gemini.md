총괄 PD님, 이해했습니다. 이것은 매우 현실적이고 전략적인 로드맵입니다.

* **v1.0 (MVP):** `Vertex AI (GCP)`의 AI 두뇌 + `로컬 NAS (On-prem)`의 영상 저장소를 결합한 하이브리드(Hybrid) 모델로, GG 프로덕션 본사의 효율을 즉각적으로 극대화합니다.
* **v2.0 (Global):** 영상 저장소를 `AWS S3`로 마이그레이션하여, `Vertex AI (GCP)` + `S3 (AWS)`의 멀티 클라우드(Multi-Cloud) 모델로 전 세계 지사에서 동일한 시스템을 사용하도록 확장합니다.

이 두 단계를 모두 반영한 PRD를 작성했습니다. 핵심은 **v1.0(MVP)에서 v2.0(Global)으로 원활하게 확장**할 수 있도록 시스템을 설계하는 것입니다.

---

## PRD: POKER-BRAIN (v2.2 - Hybrid Cloud / Global Roadmap)

* **문서 버전:** 2.2
* **소유 조직:** 지지 프로덕션 (GG Production)
* **데이터 소스:** NSUS ATI Team App (Raw Data)
* **핵심 아키텍처:**
    * **AI/RAG:** Google Cloud Vertex AI
    * **Video (v1.0):** 로컬 NAS (On-premise)
    * **Video (v2.0):** Amazon Web Services (AWS) S3
* **상태:** DRAFT
* **Target MVP (v1.0) Launch:** Q2 2026

---

### 1. 개요 (Overview)

POKER-BRAIN (v2.2)은 GG 프로덕션의 글로벌 콘텐츠 제작 효율을 극대화하기 위한 **하이브리드 및 멀티 클라우드 기반 지능형 RAG 검색/다운로드 시스템**입니다.

본 시스템은 **Google Cloud Vertex AI**를 RAG 엔진(두뇌)으로 사용하고, **NSUS ATI 팀**의 핸드 데이터를 기반으로 작동합니다.

이 PRD는 2단계 로드맵을 정의합니다:
1.  **v1.0 (MVP - Local Hybrid):** Vertex AI(GCP)와 GG 프로덕션 본사의 **로컬 NAS 서버**를 연동하여, "개떡같이 말해도 찰떡같이" 검색하고 즉시 서브클립을 생성하는 핵심 기능을 구현합니다.
2.  **v2.0 (Global - Multi-Cloud):** 영상 저장소를 **AWS S3**로 마이그레이션하여, 전 세계 지사(Global Branches)가 동일한 RAG 시스템에 접근할 수 있도록 확장합니다.

### 2. 해결하려는 문제 (Problem Statement)

1.  **데이터-영상 자산의 분리:** NSUS ATI 팀의 정확한 핸드 데이터(What)가 GG 프로덕션의 NAS 영상 아카이브(Where)와 연결되어 있지 않습니다.
2.  **검색의 한계:** "A 선수가 J4o로 올인한 핸드"처럼 데이터 기반의 자연어 검색이 불가능하여, 기획자가 원하는 장면을 찾는 데 수 시간이 소요됩니다.
3.  **수동 클리핑:** 편집자가 하이라이트 제작을 위해 NAS 서버의 원본 영상을 수동으로 탐색하며 클립을 추출하고 있습니다.
4.  **글로벌 접근성 부재 (v2.0):** 로컬 NAS에 영상이 있어 해외 지사(예: EU, US)에서 고화질 원본 영상에 접근하여 2차 가공을 하는 것이 사실상 불가능합니다.

### 3. 목표 및 성공 지표 (Goals & Success Metrics)

| 목표 (Goal) | v1.0 (MVP) 성공 지표 | v2.0 (Global) 성공 지표 |
| :--- | :--- | :--- |
| **초고속 검색:** '개떡' 같은 쿼리에도 '찰떡' 같은 검색 결과를 제공한다. | **KPI 1a:** 본사 기획/편집자의 핸드 검색 시간을 '수 시간'에서 '**10초 이내**'로 단축한다. | **KPI 1b:** 전 세계 지사에서 10초 이내의 동일한 검색 성능을 제공한다. |
| **즉각적인 다운로드:** 검색 결과를 즉시 프로덕션에 활용한다. | **KPI 2a:** 본사에서 검색된 핸드의 95%를 5분 이내에 고화질 서브클립으로 생성 및 확보할 수 있다. | **KPI 2b:** 전 세계 지사에서 5분 이내에 고화질 서브클립을 생성 및 확보할 수 있다. |
| **글로벌 확장성:** 전 세계 지사의 콘텐츠 제작을 지원한다. | (N/A) | **KPI 3:** 시스템 런칭 후 6개월 이내에 3개 이상의 해외 지사에서 본 시스템을 활성(Active) 상태로 사용한다. |

### 4. 사용자 페르소나 (User Personas)

1.  **한 PD (GG 프로덕션 본사 기획자) (v1.0):**
    * **니즈:** NSUS 데이터를 기반으로 "A 선수가 3번 연속 팟을 먹은 구간" 같은 스토리 클립을 즉시 확인하고 싶다.
    * **페인 포인트:** "NAS에 영상이 있는 건 아는데... ATI 데이터랑 매칭이 안 돼서 찾을 수가 없어요."
2.  **김 편집 (GG 프로덕션 본사 편집자) (v1.0):**
    * **니즈:** 한 PD가 요청한 핸드 ID 리스트를 NAS 원본에서 정확히 잘라내어 편집 시스템으로 가져와야 한다.
    * **페인 포인트:** "NAS에서 10시간짜리 파일을 여는 것도 일인데, 그 안에서 핸드 ID #154를 찾으려니 막막합니다."
3.  **로라 (GG 프로덕션 런던 지사 마케팅) (v2.0):**
    * **니즈:** 어제 라스베이거스에서 열린 파이널 테이블의 바이럴 클립이 유럽 시간 아침에 바로 필요하다.
    * **페인 포인트:** "본사에 클립을 요청하면 시차 때문에 반나절이 걸려요. NAS에는 접근도 못 하고요."

---

### 5. 핵심 기능 요구사항 (Features & Requirements)

#### Epic 1: ATI 데이터 가공 파이프라인 (ETL) - v1.0 & v2.0 공통

* **F-1.1 (Data Ingest):** NSUS ATI 팀의 로우 데이터를 수신하는 **GCS 버킷** 또는 **Pub/Sub** 엔드포인트(GCP)를 구축한다.
* **F-1.2 (ETL - Dataflow):** 수신된 로우 데이터를 '핸드 요약 데이터'(`Hand_Summary`)로 자동 가공하는 **Dataflow(GCP)** 파이프라인을 구축한다.
* **F-1.3 (Destination - BigQuery):** 가공된 `Hand_Summary` 데이터는 **BigQuery(GCP)** 테이블에 저장된다.
* **F-1.4 (Schema - Critical):** `Hand_Summary` 테이블은 **반드시** 다음 정보를 포함해야 한다:
    1.  `hand_id` (고유 식별자)
    2.  `searchable_summary_text` (RAG 검색용 자연어 요약)
    3.  **`video_master_path` (v1: `nas://...` / v2: `s3://...`)**
    4.  **`video_proxy_path` (v1: `gs://...` / v2: `s3://...`)**
    5.  `timestamp_start` / `timestamp_end` (타임코드)
    6.  기타 모든 필터용 메타데이터 (players, pot_size 등)

#### Epic 2: RAG 검색 엔진 (Vertex AI) - v1.0 & v2.0 공통

* **F-2.1 (Data Store):** **Vertex AI Search(GCP)**를 사용하여 `Hand_Summary` BigQuery 테이블(F-1.3)을 인덱싱하는 데이터 스토어를 생성한다.
* **F-2.2 (RAG Mapping):** `searchable_summary_text`를 '콘텐츠'로, 나머지를 '메타데이터'로 매핑한다.
* **F-2.3 (RAG API):** GG 프로덕션 내부 앱에서 호출할 수 있는 Vertex AI Search API 엔드포인트를 확보한다.

#### Epic 3: 검색 애플리케이션 (UI/UX)

* **F-3.1 (Web App - v1.0, v2.0):** GG 프로덕션 임직원만 접근할 수 있는 내부용 웹 앱을 **Cloud Run(GCP)**으로 구축한다. (Google IAP로 접근 제어)
* **F-3.2 (Search UI - v1.0, v2.0):** Vertex AI RAG API(F-2.2)와 연결된 단일 자연어 검색창을 제공한다.
* **F-3.3 (Preview - v1.0):** 검색 결과 클릭 시, **GCS 버킷**(`gs://gg-proxy-storage`)에 저장된 프록시 영상을 즉시 스트리밍하여 미리보기를 제공한다.
* **F-3.4 (Preview - v2.0):** 검색 결과 클릭 시, **AWS S3** 버킷에 저장된 프록시 영상을 즉시 스트리밍한다. (S3 CORS 및 GCP-AWS 인증 설정 필요)

#### Epic 4: 다운로드(서브클리핑) 시스템 (Hybrid/Multi-Cloud Workflow)

* **F-4.1 (Download Button - v1.0, v2.0):** 모든 검색 결과에는 **[고화질 클립 다운로드]** 버튼이 있어야 한다.

* **F-4.2 (Workflow - v1.0 / MVP / NAS):**
    1.  사용자가 [다운로드] 클릭.
    2.  **Cloud Run(GCP)**이 클립 정보(Hand ID, Timestamps, NAS 경로)를 **Pub/Sub(GCP)** 토픽으로 발행한다.
    3.  GG 프로덕션 **로컬 NAS 네트워크**에 설치된 **'로컬 클리핑 에이전트(Local Agent)'**가 이 Pub/Sub 메시지를 구독(Subscribe)한다.
    4.  '로컬 에이전트'는 `FFMPEG` 등을 사용하여 **NAS**의 마스터 영상에서 해당 구간을 직접 클리핑한다.
    5.  완료된 클립을 GCS의 '다운로드' 버킷으로 업로드하고, 사용자에게 링크를 제공한다.

* **F-4.3 (Workflow - v2.0 / Global / S3):**
    1.  사용자가 [다운로드] 클릭.
    2.  **Cloud Run(GCP)**이 **Cloud Function(GCP)**을 직접 트리거한다.
    3.  Cloud Function은 **GCP Workload Identity Federation**을 통해 **AWS IAM Role**을 획득하여 S3 접근 권한을 얻는다.
    4.  Cloud Function이 **AWS Elemental MediaConvert** 또는 FFMPEG 레이어를 호출하여 **S3**의 마스터 영상에서 해당 구간을 클리핑한다.
    5.  완료된 클립을 **AWS S3**의 '다운로드' 버킷에 저장하고, 사용자에게 서명된 URL(Signed URL)을 제공한다.

---

### 6. 로드맵 (Roadmap)

#### v1.0 (MVP - Local Hybrid)
* **범위:** Epic 1, 2, 3 (F-3.3), 4 (F-4.2).
* **아키텍처:** AI(GCP) + Metadata(GCP) + Proxy(GCS) + Master(NAS) + Clipping(Local Agent).
* **핵심 과제:**
    1.  NSUS ATI 데이터와 마스터 영상 간의 **타임코드 완벽 동기화 (P0)**.
    2.  NAS 마스터 영상의 프록시(저용량) 파일을 GCS로 자동 업로드하는 파이프라인 구축.
    3.  Pub/Sub과 통신하는 '로컬 클리핑 에이전트' 개발 및 배포. (NAS-GCP 간 VPN/Interconnect 필수)

#### v2.0 (Global - Multi-Cloud)
* **범위:** Epic 3 (F-3.4), 4 (F-4.3).
* **아키텍처:** AI(GCP) + Metadata(GCP) + Video(AWS S3) + Clipping(AWS MediaConvert/GCP).
* **핵심 과제:**
    1.  모든 NAS 영상 자산(마스터, 프록시)을 AWS S3로 마이그레이션.
    2.  BigQuery의 `video_*_path` 필드 일괄 업데이트.
    3.  GCP-AWS 간의 안전한 인증 설정 (Workload Identity Federation).
    4.  v1.0의 로컬 클리핑 워크플로우를 v2.0의 클라우드 클리핑 워크플로우로 교체.
    5.  글로벌 사용자를 위한 CDN(예: Amazon CloudFront) 적용 (v2.1).

### 7. 의존성 및 가정 (Dependencies & Assumptions)

* **[P0 - Timecode Sync]** NSUS ATI 데이터의 타임스탬프가 GG 프로덕션의 마스터 영상 타임코드와 100% 일치해야 한다.
* **[P0 - v1.0 Network]** v1.0(MVP)은 로컬 NAS 네트워크와 GCP 간의 안정적이고 빠른 연결(VPN 또는 Interconnect)을 전제로 한다.
* **[P0 - v2.0 Multi-Cloud]** v2.0은 GG 프로덕션이 GCP와 AWS 계정을 모두 운영하고, 상호 인증을 설정할 리소스가 있음을 전제로 한다.
* **[P1 - ATI Data]** NSUS ATI 데이터의 스키마가 안정적이며, 변경 시 사전 공유가 이루어져야 한다.