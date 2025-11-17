"""
GCS (Google Cloud Storage) uploader for proxy videos
"""
import os
import logging
from google.cloud import storage
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)


class GCSUploader:
    """Upload video files to Google Cloud Storage"""

    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or config.GCS_BUCKET
        self.client = storage.Client(project=config.PROJECT_ID)
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(
        self,
        local_path: str,
        blob_name: str,
        content_type: str = "video/mp4",
        timeout: int = 600
    ) -> str:
        """
        Upload file to GCS

        Args:
            local_path: Local file path
            blob_name: GCS blob name (path in bucket)
            content_type: MIME type (default: video/mp4)
            timeout: Upload timeout in seconds (default: 600)

        Returns:
            GCS URI (gs://bucket/blob)

        Raises:
            ValueError: If local file doesn't exist
            RuntimeError: If upload fails
        """
        if not os.path.exists(local_path):
            raise ValueError(f"Local file does not exist: {local_path}")

        file_size = os.path.getsize(local_path)
        logger.info(f"Uploading {local_path} to gs://{self.bucket_name}/{blob_name} ({file_size / 1024 / 1024:.2f} MB)")

        try:
            blob = self.bucket.blob(blob_name)
            blob.content_type = content_type

            # Upload with chunked transfer for large files
            blob.upload_from_filename(
                local_path,
                timeout=timeout,
                checksum="md5"  # Verify upload integrity
            )

            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"Upload successful: {gcs_uri}")

            return gcs_uri

        except Exception as e:
            error_msg = f"GCS upload failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_public_url(self, blob_name: str) -> str:
        """
        Get public URL for a GCS blob

        Args:
            blob_name: GCS blob name

        Returns:
            Public HTTPS URL
        """
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

    def get_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> str:
        """
        Generate signed URL for temporary access

        Args:
            blob_name: GCS blob name
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL
        """
        from datetime import timedelta

        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        return url

    def blob_exists(self, blob_name: str) -> bool:
        """
        Check if blob exists in GCS

        Args:
            blob_name: GCS blob name

        Returns:
            True if exists, False otherwise
        """
        blob = self.bucket.blob(blob_name)
        return blob.exists()

    def delete_blob(self, blob_name: str) -> None:
        """
        Delete blob from GCS

        Args:
            blob_name: GCS blob name
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted blob: gs://{self.bucket_name}/{blob_name}")
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            raise
