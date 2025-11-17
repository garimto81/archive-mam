"""
Tests for Google Cloud Storage client.

Tests upload, download URL generation, and development mock mode.
"""

import os
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.gcs_client import GCSClient, get_gcs_client


@pytest.fixture
def dev_gcs_client():
    """Create GCS client in development mode."""
    with patch('app.gcs_client.get_config') as mock_config:
        config = Mock()
        config.is_development.return_value = True
        config.MOCK_CLIPS_DIR = tempfile.mkdtemp()
        config.GCS_BUCKET = 'test-bucket'
        config.SIGNED_URL_EXPIRY_HOURS = 168
        mock_config.return_value = config

        client = GCSClient()
        yield client

        # Cleanup
        import shutil
        if os.path.exists(config.MOCK_CLIPS_DIR):
            shutil.rmtree(config.MOCK_CLIPS_DIR)


@pytest.fixture
def prod_gcs_client():
    """Create GCS client in production mode (mocked)."""
    with patch('app.gcs_client.get_config') as mock_config, \
         patch('app.gcs_client.storage.Client') as mock_storage:

        config = Mock()
        config.is_development.return_value = False
        config.GCP_PROJECT_ID = 'test-project'
        config.GCS_BUCKET = 'test-bucket'
        config.SIGNED_URL_EXPIRY_HOURS = 168
        mock_config.return_value = config

        # Mock storage client
        client = Mock()
        bucket = Mock()
        mock_storage.return_value = client
        client.bucket.return_value = bucket

        gcs_client = GCSClient()
        gcs_client.bucket = bucket

        yield gcs_client, bucket


class TestGCSClientDevelopment:
    """Tests for GCS client in development (mock) mode."""

    def test_init_development(self, dev_gcs_client):
        """Test initialization in development mode."""
        assert dev_gcs_client.is_development is True
        assert os.path.exists(dev_gcs_client.mock_storage_path)

    def test_upload_clip_mock(self, dev_gcs_client):
        """Test mock clip upload in development mode."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mp4') as tmp:
            tmp.write(b'fake video data')
            tmp_path = tmp.name

        try:
            gcs_path = dev_gcs_client.upload_clip(
                local_path=tmp_path,
                hand_id='test_hand_123'
            )

            # Check GCS path format
            assert gcs_path == 'gs://test-bucket/test_hand_123.mp4'

            # Check file was copied to mock directory
            mock_file = os.path.join(
                dev_gcs_client.mock_storage_path,
                'test_hand_123.mp4'
            )
            assert os.path.exists(mock_file)

        finally:
            os.remove(tmp_path)

    def test_generate_signed_url_mock(self, dev_gcs_client):
        """Test mock signed URL generation."""
        url, expires_at = dev_gcs_client.generate_signed_url('test_hand_123')

        # Check URL format
        assert 'localhost:8005/mock-download' in url
        assert 'test_hand_123.mp4' in url

        # Check expiry timestamp
        expires_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
        now = datetime.utcnow()
        assert expires_dt > now

    def test_get_blob_size_mock(self, dev_gcs_client):
        """Test getting blob size in mock mode."""
        # Create mock file
        mock_file = os.path.join(
            dev_gcs_client.mock_storage_path,
            'test_hand.mp4'
        )
        with open(mock_file, 'wb') as f:
            f.write(b'x' * 1024)  # 1KB

        size = dev_gcs_client.get_blob_size('test_hand')
        assert size == 1024

    def test_get_blob_size_not_found_mock(self, dev_gcs_client):
        """Test getting size of non-existent blob."""
        size = dev_gcs_client.get_blob_size('nonexistent_hand')
        assert size is None

    def test_delete_clip_mock(self, dev_gcs_client):
        """Test deleting clip in mock mode."""
        # Create mock file
        mock_file = os.path.join(
            dev_gcs_client.mock_storage_path,
            'test_hand.mp4'
        )
        with open(mock_file, 'wb') as f:
            f.write(b'test')

        # Delete
        result = dev_gcs_client.delete_clip('test_hand')
        assert result is True
        assert not os.path.exists(mock_file)

    def test_delete_clip_not_found_mock(self, dev_gcs_client):
        """Test deleting non-existent clip."""
        result = dev_gcs_client.delete_clip('nonexistent')
        assert result is False


class TestGCSClientProduction:
    """Tests for GCS client in production mode (mocked)."""

    def test_init_production(self, prod_gcs_client):
        """Test initialization in production mode."""
        client, bucket = prod_gcs_client
        assert client.is_development is False

    def test_upload_clip_success(self, prod_gcs_client):
        """Test successful clip upload."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.size = 1024000

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
            tmp.write(b'fake video data')
            tmp_path = tmp.name

        try:
            gcs_path = client.upload_clip(
                local_path=tmp_path,
                hand_id='test_hand_123'
            )

            # Check blob operations
            bucket.blob.assert_called_once_with('test_hand_123.mp4')
            blob.upload_from_filename.assert_called_once()
            blob.patch.assert_called_once()

            # Check returned path
            assert gcs_path == 'gs://test-bucket/test_hand_123.mp4'

        finally:
            os.remove(tmp_path)

    def test_upload_clip_failure(self, prod_gcs_client):
        """Test handling upload failure."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.upload_from_filename.side_effect = Exception("Upload failed")

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
            tmp.write(b'data')
            tmp_path = tmp.name

        try:
            with pytest.raises(Exception) as exc_info:
                client.upload_clip(
                    local_path=tmp_path,
                    hand_id='test_hand'
                )

            assert 'Upload failed' in str(exc_info.value)

        finally:
            os.remove(tmp_path)

    def test_generate_signed_url_success(self, prod_gcs_client):
        """Test successful signed URL generation."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.exists.return_value = True
        blob.generate_signed_url.return_value = 'https://storage.googleapis.com/signed-url'

        url, expires_at = client.generate_signed_url('test_hand')

        # Check URL
        assert url.startswith('https://storage.googleapis.com/')

        # Check expiry
        expires_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
        now = datetime.utcnow()
        expected_expiry = now + timedelta(hours=168)
        assert abs((expires_dt - expected_expiry).total_seconds()) < 5

    def test_generate_signed_url_blob_not_found(self, prod_gcs_client):
        """Test signed URL generation for non-existent blob."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.exists.return_value = False

        with pytest.raises(Exception) as exc_info:
            client.generate_signed_url('nonexistent_hand')

        assert 'not found' in str(exc_info.value).lower()

    def test_get_blob_size_success(self, prod_gcs_client):
        """Test getting blob size."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.exists.return_value = True
        blob.size = 2048000

        size = client.get_blob_size('test_hand')
        assert size == 2048000

    def test_get_blob_size_not_found(self, prod_gcs_client):
        """Test getting size of non-existent blob."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.exists.return_value = False

        size = client.get_blob_size('nonexistent')
        assert size is None

    def test_delete_clip_success(self, prod_gcs_client):
        """Test successful clip deletion."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.exists.return_value = True

        result = client.delete_clip('test_hand')
        assert result is True
        blob.delete.assert_called_once()

    def test_delete_clip_not_found(self, prod_gcs_client):
        """Test deleting non-existent clip."""
        client, bucket = prod_gcs_client

        blob = Mock()
        bucket.blob.return_value = blob
        blob.exists.return_value = False

        result = client.delete_clip('nonexistent')
        assert result is False


class TestGetGCSClient:
    """Tests for get_gcs_client singleton."""

    def test_get_gcs_client_singleton(self):
        """Test that get_gcs_client returns singleton."""
        # Clear singleton
        import app.gcs_client
        app.gcs_client._gcs_client = None

        with patch('app.gcs_client.get_config'):
            client1 = get_gcs_client()
            client2 = get_gcs_client()

            assert client1 is client2
