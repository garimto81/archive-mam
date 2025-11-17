"""
Unit tests for GCS Uploader
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from app.gcs_uploader import GCSUploader


@pytest.fixture
def mock_gcs_client():
    """Mock GCS client and bucket"""
    with patch('app.gcs_uploader.storage.Client') as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        yield mock_client, mock_bucket, mock_blob


@pytest.fixture
def temp_file():
    """Create temporary file for upload"""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        f.write(b'test video data')
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_gcs_uploader_initialization():
    """Test GCS uploader initialization"""
    with patch('app.gcs_uploader.storage.Client'):
        uploader = GCSUploader(bucket_name="test-bucket")
        assert uploader.bucket_name == "test-bucket"


def test_upload_file_success(mock_gcs_client, temp_file):
    """Test successful file upload"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client

    uploader = GCSUploader(bucket_name="test-bucket")
    gcs_uri = uploader.upload_file(temp_file, "test/video.mp4")

    assert gcs_uri == "gs://test-bucket/test/video.mp4"
    mock_blob.upload_from_filename.assert_called_once()


def test_upload_file_not_exists(mock_gcs_client):
    """Test upload with non-existent file"""
    uploader = GCSUploader()

    with pytest.raises(ValueError, match="Local file does not exist"):
        uploader.upload_file('/nonexistent/file.mp4', 'test/video.mp4')


def test_upload_file_with_content_type(mock_gcs_client, temp_file):
    """Test upload with custom content type"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client

    uploader = GCSUploader()
    uploader.upload_file(temp_file, "test/video.mp4", content_type="video/quicktime")

    assert mock_blob.content_type == "video/quicktime"


def test_upload_file_error(mock_gcs_client, temp_file):
    """Test handling of upload errors"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client
    mock_blob.upload_from_filename.side_effect = Exception("Network error")

    uploader = GCSUploader()

    with pytest.raises(RuntimeError, match="GCS upload failed"):
        uploader.upload_file(temp_file, "test/video.mp4")


def test_get_public_url(mock_gcs_client):
    """Test public URL generation"""
    uploader = GCSUploader(bucket_name="test-bucket")
    url = uploader.get_public_url("path/to/video.mp4")

    assert url == "https://storage.googleapis.com/test-bucket/path/to/video.mp4"


def test_get_signed_url(mock_gcs_client):
    """Test signed URL generation"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client
    mock_blob.generate_signed_url.return_value = "https://signed-url.com/video.mp4"

    uploader = GCSUploader()
    url = uploader.get_signed_url("path/to/video.mp4", expiration_minutes=120)

    assert "signed-url.com" in url
    mock_blob.generate_signed_url.assert_called_once()


def test_blob_exists_true(mock_gcs_client):
    """Test blob existence check - exists"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client
    mock_blob.exists.return_value = True

    uploader = GCSUploader()
    exists = uploader.blob_exists("path/to/video.mp4")

    assert exists is True


def test_blob_exists_false(mock_gcs_client):
    """Test blob existence check - not exists"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client
    mock_blob.exists.return_value = False

    uploader = GCSUploader()
    exists = uploader.blob_exists("path/to/video.mp4")

    assert exists is False


def test_delete_blob(mock_gcs_client):
    """Test blob deletion"""
    mock_client, mock_bucket, mock_blob = mock_gcs_client

    uploader = GCSUploader()
    uploader.delete_blob("path/to/video.mp4")

    mock_blob.delete.assert_called_once()
