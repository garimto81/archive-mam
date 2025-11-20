"""
ATI 메타데이터 인덱싱 Cloud Function
v4.0.0 - Vertex AI Vector Search + BigQuery

GCS Pub/Sub 트리거:
- ATI가 GCS에 JSON 저장 시 자동 실행
- BigQuery에 메타데이터 삽입
- Vertex AI Embedding 생성 (향후 Vector Search 인덱싱)

Deployment:
    gcloud functions deploy index-ati-metadata \
        --runtime python311 \
        --trigger-bucket ati-metadata-prod \
        --entry-point process_ati_metadata \
        --region us-central1 \
        --set-env-vars GCP_PROJECT=gg-poker-prod
"""

import functions_framework
from google.cloud import storage, bigquery, aiplatform
from google.cloud.exceptions import GoogleCloudError
from vertexai.language_models import TextEmbeddingModel
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ATIMetadataProcessor:
    """ATI 메타데이터 처리 클래스"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.storage_client = storage.Client(project=project_id)
        self.bq_client = bigquery.Client(project=project_id)
        self.dataset_id = "poker_archive"
        self.table_id = "hands"

        # Vertex AI 초기화
        aiplatform.init(project=project_id, location="us-central1")
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """메타데이터 스키마 검증"""
        required_fields = [
            "hand_id", "tournament_id", "timestamp",
            "description", "hero_name", "pot_bb", "video_url"
        ]

        for field in required_fields:
            if field not in metadata:
                print(f"Missing required field: {field}")
                return False

        # 타입 검증
        if not isinstance(metadata["pot_bb"], (int, float)):
            print(f"Invalid pot_bb type: {type(metadata['pot_bb'])}")
            return False

        if not metadata["video_url"].startswith("gs://"):
            print(f"Invalid video_url format: {metadata['video_url']}")
            return False

        return True

    def transform_to_bigquery_row(
        self,
        metadata: Dict[str, Any],
        gcs_path: str
    ) -> Dict[str, Any]:
        """ATI 메타데이터 → BigQuery 행 변환"""
        now = datetime.utcnow()

        # 기본 행 생성
        row = {
            # 필수 필드
            "hand_id": metadata["hand_id"],
            "tournament_id": metadata["tournament_id"],
            "timestamp": metadata["timestamp"],
            "description": metadata["description"],
            "hero_name": metadata["hero_name"],
            "pot_bb": float(metadata["pot_bb"]),
            "video_url": metadata["video_url"],

            # 시스템 필드
            "created_date": now.date().isoformat(),
            "created_at": now.isoformat() + "Z",
            "gcs_source_path": gcs_path,
        }

        # 선택 필드 (있으면 추가)
        optional_fields = [
            "hand_number", "duration_seconds", "villain_name",
            "hero_position", "villain_position", "hero_stack_bb",
            "villain_stack_bb", "street", "hero_action", "result",
            "hand_type", "video_start_time", "video_end_time",
            "thumbnail_url", "ati_version", "ati_confidence"
        ]

        for field in optional_fields:
            if field in metadata:
                # Float 변환이 필요한 필드
                if field in ["hero_stack_bb", "villain_stack_bb",
                            "video_start_time", "video_end_time", "ati_confidence"]:
                    row[field] = float(metadata[field]) if metadata[field] is not None else None
                else:
                    row[field] = metadata[field]

        # ARRAY 필드
        if "action_sequence" in metadata:
            row["action_sequence"] = metadata["action_sequence"]

        if "tags" in metadata:
            row["tags"] = metadata["tags"]

        return row

    def insert_to_bigquery(self, row: Dict[str, Any]) -> bool:
        """BigQuery에 행 삽입"""
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"

        try:
            errors = self.bq_client.insert_rows_json(table_ref, [row])

            if errors:
                print(f"BigQuery insert errors: {errors}")
                return False

            print(f"✅ BigQuery insert successful: {row['hand_id']}")
            return True

        except GoogleCloudError as e:
            print(f"BigQuery insert failed: {e}")
            print(traceback.format_exc())
            return False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Vertex AI로 텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트 (description)

        Returns:
            768차원 임베딩 벡터 또는 None (실패 시)
        """
        try:
            # TextEmbedding-004 모델 사용
            embeddings = self.embedding_model.get_embeddings([text])

            if embeddings and len(embeddings) > 0:
                embedding_values = embeddings[0].values
                print(f"✅ Embedding generated: {len(embedding_values)} dimensions")
                return embedding_values
            else:
                print("❌ Embedding generation failed: empty response")
                return None

        except Exception as e:
            print(f"❌ Embedding generation error: {e}")
            print(traceback.format_exc())
            return None

    def save_embedding_to_gcs(
        self,
        hand_id: str,
        embedding: List[float],
        bucket_name: str = "ati-metadata-prod"
    ) -> bool:
        """임베딩을 GCS에 JSON으로 저장 (Vertex AI 인덱스 업로드용)

        Args:
            hand_id: 핸드 ID
            embedding: 임베딩 벡터
            bucket_name: GCS 버킷 이름

        Returns:
            성공 여부
        """
        try:
            # embeddings/ 폴더에 저장
            embedding_data = {
                "id": hand_id,
                "embedding": embedding
            }

            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(f"embeddings/{hand_id}.json")
            blob.upload_from_string(
                json.dumps(embedding_data),
                content_type="application/json"
            )

            print(f"✅ Embedding saved to GCS: embeddings/{hand_id}.json")
            return True

        except Exception as e:
            print(f"❌ Embedding save failed: {e}")
            print(traceback.format_exc())
            return False

    def process_gcs_file(self, bucket_name: str, file_name: str) -> bool:
        """GCS 파일 처리 메인 로직"""
        gcs_path = f"gs://{bucket_name}/{file_name}"

        print(f"Processing file: {gcs_path}")

        try:
            # 1. GCS에서 JSON 읽기
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(file_name)

            if not blob.exists():
                print(f"File not found: {gcs_path}")
                return False

            content = blob.download_as_text()
            metadata = json.loads(content)

            print(f"Loaded JSON: {metadata.get('hand_id', 'unknown')}")

            # 2. 스키마 검증
            if not self.validate_metadata(metadata):
                print("Schema validation failed")
                return False

            print("✅ Schema validation passed")

            # 3. BigQuery 행 변환
            bq_row = self.transform_to_bigquery_row(metadata, gcs_path)

            # 4. BigQuery 삽입
            success = self.insert_to_bigquery(bq_row)

            if not success:
                return False

            # 5. Vertex AI Embedding 생성 및 저장
            embedding = self.generate_embedding(metadata["description"])

            if embedding:
                # GCS에 임베딩 저장 (Vertex AI 인덱스 업로드용)
                embedding_saved = self.save_embedding_to_gcs(
                    metadata["hand_id"],
                    embedding,
                    bucket_name
                )

                if not embedding_saved:
                    print("⚠️  Embedding save failed, but continuing...")
            else:
                print("⚠️  Embedding generation failed, but continuing...")

            print(f"✅ Processing complete: {metadata['hand_id']}")
            return True

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return False

        except Exception as e:
            print(f"Unexpected error: {e}")
            print(traceback.format_exc())
            return False


@functions_framework.cloud_event
def process_ati_metadata(cloud_event):
    """
    Cloud Function Entry Point (GCS Pub/Sub 트리거)

    Args:
        cloud_event: CloudEvent with GCS object metadata

    Returns:
        None (로그만 출력)
    """
    import os

    try:
        # 환경변수에서 프로젝트 ID 가져오기
        project_id = os.environ.get("GCP_PROJECT", "gg-poker-prod")

        # 이벤트 데이터 추출
        data = cloud_event.data
        bucket_name = data["bucket"]
        file_name = data["name"]

        print("=" * 60)
        print(f"Cloud Function Triggered")
        print(f"Bucket: {bucket_name}")
        print(f"File: {file_name}")
        print("=" * 60)

        # embeddings/ 폴더 파일 건너뛰기 (무한 루프 방지)
        if file_name.startswith('embeddings/'):
            print(f"Skipping embedding file: {file_name}")
            return

        # JSON 파일만 처리 (디렉토리나 기타 파일 제외)
        if not file_name.endswith('.json'):
            print(f"Skipping non-JSON file: {file_name}")
            return

        # 프로세서 생성 및 실행
        processor = ATIMetadataProcessor(project_id)
        success = processor.process_gcs_file(bucket_name, file_name)

        if success:
            print("🎉 Processing completed successfully")
        else:
            print("❌ Processing failed")
            # 실패 시에도 에러를 raise하지 않음 (재시도 방지)
            # 필요 시 Dead Letter Queue 설정
    except Exception as e:
        print(f"FATAL ERROR in process_ati_metadata: {str(e)}")
        import traceback
        traceback.print_exc()


# 로컬 테스트용 (Cloud Functions 환경 외부)
if __name__ == "__main__":
    print("Local testing mode")
    print("Usage: python main.py")
    print("")
    print("To test:")
    print("  1. Set GCP_PROJECT environment variable")
    print("  2. Run: python -c 'from main import test_local; test_local()'")

    def test_local():
        """로컬 테스트 함수"""
        import os

        project_id = os.environ.get("GCP_PROJECT", "gg-poker-prod")
        processor = ATIMetadataProcessor(project_id)

        # 테스트 파일 경로
        test_bucket = "ati-metadata-prod"
        test_file = "test/ati_metadata_001.json"

        print(f"Testing with: gs://{test_bucket}/{test_file}")
        success = processor.process_gcs_file(test_bucket, test_file)

        if success:
            print("✅ Test passed")
        else:
            print("❌ Test failed")
