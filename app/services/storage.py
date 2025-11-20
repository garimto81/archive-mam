"""
GCS Storage 서비스
v4.0.0
"""

from google.cloud import storage
from datetime import timedelta
from urllib.parse import urlparse

from app.config import settings


class StorageService:
    """GCS Signed URL 생성 서비스"""

    def __init__(self):
        self.client = storage.Client(project=settings.GCP_PROJECT)

    def generate_signed_url(
        self,
        gcs_uri: str,
        expiration_seconds: int = None
    ) -> str:
        """GCS URI에서 Signed URL 생성

        Args:
            gcs_uri: GCS URI (gs://bucket/path/to/file.mp4)
            expiration_seconds: 만료 시간 (초), None이면 기본값 사용

        Returns:
            Signed URL (HTTPS)

        Raises:
            ValueError: 잘못된 GCS URI
        """
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")

        # gs://bucket/path 파싱
        parsed = urlparse(gcs_uri)
        bucket_name = parsed.netloc
        blob_name = parsed.path.lstrip("/")

        if not bucket_name or not blob_name:
            raise ValueError(f"Invalid GCS URI format: {gcs_uri}")

        # Signed URL 생성
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        expiration = timedelta(
            seconds=expiration_seconds or settings.SIGNED_URL_EXPIRATION
        )

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET"
        )

        return signed_url

    def get_video_signed_url(self, hand_id: str, video_url: str) -> str:
        """핸드 비디오 Signed URL 생성

        Args:
            hand_id: 핸드 ID (로깅용)
            video_url: GCS 비디오 경로

        Returns:
            Signed URL
        """
        try:
            signed_url = self.generate_signed_url(
                video_url,
                settings.SIGNED_URL_EXPIRATION
            )
            print(f"Generated signed URL for {hand_id}: {video_url}")
            return signed_url

        except Exception as e:
            print(f"Failed to generate signed URL for {hand_id}: {e}")
            raise
