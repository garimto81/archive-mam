"""
Google Cloud Storage client for M5 Clipping Service.

Handles video clip uploads and signed URL generation.
Supports both development (mock) and production modes.
"""

import logging
import os
from datetime import timedelta, datetime
from typing import Optional
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.config import get_config

logger = logging.getLogger(__name__)


class GCSClient:
    """Google Cloud Storage client for clip uploads."""

    def __init__(self):
        self.config = get_config()
        self.is_development = self.config.is_development()

        if not self.is_development:
            self.client = storage.Client(project=self.config.GCP_PROJECT_ID)
            self.bucket = self.client.bucket(self.config.GCS_BUCKET)
            logger.info(f"GCSClient initialized: bucket={self.config.GCS_BUCKET}")
        else:
            # Development mode: use local mock storage
            self.mock_storage_path = self.config.MOCK_CLIPS_DIR
            os.makedirs(self.mock_storage_path, exist_ok=True)
            logger.info(f"GCSClient in MOCK mode: dir={self.mock_storage_path}")

    def upload_clip(
        self,
        local_path: str,
        hand_id: str,
        content_type: str = 'video/mp4'
    ) -> str:
        """
        Upload a video clip to GCS.

        Args:
            local_path: Path to local video file
            hand_id: Hand identifier (used as filename)
            content_type: MIME type

        Returns:
            GCS path (gs://bucket/filename)

        Raises:
            Exception: If upload fails
        """
        blob_name = f"{hand_id}.mp4"

        if self.is_development:
            # Mock: Copy to local directory
            return self._mock_upload(local_path, blob_name)

        try:
            blob = self.bucket.blob(blob_name)

            # Upload file with metadata
            blob.upload_from_filename(
                local_path,
                content_type=content_type,
                timeout=300  # 5 minutes timeout
            )

            # Set cache control and lifecycle
            blob.cache_control = 'public, max-age=86400'  # 1 day
            blob.patch()

            gcs_path = f"gs://{self.config.GCS_BUCKET}/{blob_name}"

            logger.info(
                f"Uploaded clip to GCS: local={local_path}, "
                f"gcs={gcs_path}, size={blob.size}"
            )

            return gcs_path

        except GoogleCloudError as e:
            logger.error(f"GCS upload failed: {e}")
            raise Exception(f"Failed to upload to GCS: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during GCS upload: {e}")
            raise

    def _mock_upload(self, local_path: str, blob_name: str) -> str:
        """Mock upload for development mode."""
        import shutil

        mock_path = os.path.join(self.mock_storage_path, blob_name)

        # Copy file to mock directory
        shutil.copy2(local_path, mock_path)

        gcs_path = f"gs://{self.config.GCS_BUCKET}/{blob_name}"

        logger.info(f"[MOCK] Uploaded clip: {local_path} -> {mock_path}")

        return gcs_path

    def generate_signed_url(
        self,
        hand_id: str,
        expiry_hours: Optional[int] = None
    ) -> tuple[str, str]:
        """
        Generate a signed URL for downloading a clip.

        Args:
            hand_id: Hand identifier
            expiry_hours: URL expiry time in hours (default: from config)

        Returns:
            Tuple of (signed_url, expiry_timestamp)

        Raises:
            Exception: If URL generation fails
        """
        blob_name = f"{hand_id}.mp4"
        expiry_hours = expiry_hours or self.config.SIGNED_URL_EXPIRY_HOURS

        if self.is_development:
            # Mock: Return a fake signed URL
            return self._mock_signed_url(blob_name, expiry_hours)

        try:
            blob = self.bucket.blob(blob_name)

            # Check if blob exists
            if not blob.exists():
                raise Exception(f"Clip not found in GCS: {blob_name}")

            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiry_hours),
                method="GET"
            )

            expiry_timestamp = (
                datetime.utcnow() + timedelta(hours=expiry_hours)
            ).isoformat() + 'Z'

            logger.info(
                f"Generated signed URL: blob={blob_name}, "
                f"expiry={expiry_hours}h"
            )

            return url, expiry_timestamp

        except GoogleCloudError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise Exception(f"Failed to generate download URL: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error generating signed URL: {e}")
            raise

    def _mock_signed_url(self, blob_name: str, expiry_hours: int) -> tuple[str, str]:
        """Generate mock signed URL for development."""
        mock_url = (
            f"http://localhost:8005/mock-download/"
            f"{blob_name}?expires={expiry_hours}h"
        )

        expiry_timestamp = (
            datetime.utcnow() + timedelta(hours=expiry_hours)
        ).isoformat() + 'Z'

        logger.info(f"[MOCK] Generated signed URL: {mock_url}")

        return mock_url, expiry_timestamp

    def get_blob_size(self, hand_id: str) -> Optional[int]:
        """
        Get the size of a blob in bytes.

        Args:
            hand_id: Hand identifier

        Returns:
            File size in bytes, or None if not found
        """
        blob_name = f"{hand_id}.mp4"

        if self.is_development:
            # Mock: Get local file size
            mock_path = os.path.join(self.mock_storage_path, blob_name)
            if os.path.exists(mock_path):
                return os.path.getsize(mock_path)
            return None

        try:
            blob = self.bucket.blob(blob_name)
            if blob.exists():
                blob.reload()  # Refresh metadata
                return blob.size
            return None

        except Exception as e:
            logger.error(f"Failed to get blob size: {e}")
            return None

    def delete_clip(self, hand_id: str) -> bool:
        """
        Delete a clip from GCS.

        Args:
            hand_id: Hand identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        blob_name = f"{hand_id}.mp4"

        if self.is_development:
            # Mock: Delete local file
            mock_path = os.path.join(self.mock_storage_path, blob_name)
            if os.path.exists(mock_path):
                os.remove(mock_path)
                logger.info(f"[MOCK] Deleted clip: {mock_path}")
                return True
            return False

        try:
            blob = self.bucket.blob(blob_name)
            if blob.exists():
                blob.delete()
                logger.info(f"Deleted clip from GCS: {blob_name}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete clip: {e}")
            return False


# Global GCS client instance
_gcs_client = None


def get_gcs_client() -> GCSClient:
    """Get the global GCS client instance (singleton)."""
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = GCSClient()
    return _gcs_client
