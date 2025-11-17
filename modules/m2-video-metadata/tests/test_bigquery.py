"""
Unit tests for BigQuery Client
"""
import pytest
from unittest.mock import patch, MagicMock
from app.bigquery_client import BigQueryClient


@pytest.fixture
def mock_bq_client():
    """Mock BigQuery client"""
    with patch('app.bigquery_client.bigquery.Client') as mock_client:
        yield mock_client


def test_bigquery_client_initialization(mock_bq_client):
    """Test BigQuery client initialization"""
    client = BigQueryClient()
    assert client.table_id == "gg-poker.prod.video_files"


def test_ensure_table_exists_already_exists(mock_bq_client):
    """Test table creation when table already exists"""
    mock_bq_client.return_value.get_table.return_value = MagicMock()

    client = BigQueryClient()
    client.ensure_table_exists()

    mock_bq_client.return_value.get_table.assert_called_once()
    mock_bq_client.return_value.create_table.assert_not_called()


def test_ensure_table_exists_creates_new(mock_bq_client):
    """Test table creation when table doesn't exist"""
    from google.cloud.exceptions import NotFound

    mock_bq_client.return_value.get_table.side_effect = NotFound("Table not found")

    client = BigQueryClient()
    client.ensure_table_exists()

    mock_bq_client.return_value.create_table.assert_called_once()


def test_insert_video_metadata_success(mock_bq_client):
    """Test successful metadata insertion"""
    mock_bq_client.return_value.insert_rows_json.return_value = []  # No errors

    videos = [
        {
            'video_id': 'wsop2024_me_d1_t1',
            'event_id': 'wsop2024_me',
            'duration_seconds': 3600
        }
    ]

    client = BigQueryClient()
    client.insert_video_metadata(videos)

    mock_bq_client.return_value.insert_rows_json.assert_called_once()


def test_insert_video_metadata_errors(mock_bq_client):
    """Test metadata insertion with errors"""
    mock_bq_client.return_value.insert_rows_json.return_value = [
        {'index': 0, 'errors': [{'message': 'Invalid schema'}]}
    ]

    videos = [{'video_id': 'test'}]

    client = BigQueryClient()

    with pytest.raises(RuntimeError, match="BigQuery insert errors"):
        client.insert_video_metadata(videos)


def test_insert_video_metadata_empty_list(mock_bq_client):
    """Test insertion with empty list"""
    client = BigQueryClient()
    client.insert_video_metadata([])

    # Should not call insert
    mock_bq_client.return_value.insert_rows_json.assert_not_called()


def test_upsert_video_metadata(mock_bq_client):
    """Test upsert operation"""
    mock_query_job = MagicMock()
    mock_bq_client.return_value.query.return_value = mock_query_job

    video = {
        'video_id': 'wsop2024_me_d1_t1',
        'event_id': 'wsop2024_me',
        'tournament_day': 1,
        'table_number': 1
    }

    client = BigQueryClient()
    client.upsert_video_metadata(video)

    mock_bq_client.return_value.query.assert_called_once()
    mock_query_job.result.assert_called_once()


def test_upsert_video_metadata_no_video_id(mock_bq_client):
    """Test upsert without video_id"""
    video = {'event_id': 'wsop2024_me'}

    client = BigQueryClient()

    with pytest.raises(ValueError, match="video_id is required"):
        client.upsert_video_metadata(video)


def test_get_video_by_id_found(mock_bq_client):
    """Test getting video by ID - found"""
    mock_row = MagicMock()
    mock_row.__iter__ = lambda self: iter([('video_id', 'test'), ('duration', 3600)])

    mock_bq_client.return_value.query.return_value = [mock_row]

    client = BigQueryClient()
    video = client.get_video_by_id('test_video_id')

    assert video is not None


def test_get_video_by_id_not_found(mock_bq_client):
    """Test getting video by ID - not found"""
    mock_bq_client.return_value.query.return_value = []

    client = BigQueryClient()
    video = client.get_video_by_id('nonexistent_id')

    assert video is None


def test_list_videos(mock_bq_client):
    """Test listing videos"""
    mock_rows = [MagicMock(), MagicMock()]
    for row in mock_rows:
        row.__iter__ = lambda self: iter([('video_id', 'test')])

    mock_bq_client.return_value.query.return_value = mock_rows

    client = BigQueryClient()
    videos = client.list_videos(limit=10, offset=0)

    assert len(videos) == 2


def test_list_videos_with_event_filter(mock_bq_client):
    """Test listing videos with event filter"""
    mock_bq_client.return_value.query.return_value = []

    client = BigQueryClient()
    videos = client.list_videos(event_id='wsop2024_me', limit=100, offset=0)

    # Should include WHERE clause
    call_args = mock_bq_client.return_value.query.call_args
    query = call_args[0][0]
    assert 'WHERE' in query


def test_get_stats(mock_bq_client):
    """Test statistics retrieval"""
    mock_row = {
        'total_files_scanned': 100,
        'total_storage_bytes': 1000000000,
        'proxies_generated': 90,
        'avg_duration_seconds': 3600.5,
        'last_scan_at': '2024-11-17T10:00:00Z'
    }

    mock_bq_client.return_value.query.return_value = [mock_row]

    client = BigQueryClient()
    stats = client.get_stats(period='24h')

    assert stats['period'] == '24h'
    assert stats['total_files_scanned'] == 100
    assert stats['proxies_generated'] == 90


def test_get_stats_error(mock_bq_client):
    """Test statistics retrieval with error"""
    mock_bq_client.return_value.query.side_effect = Exception("Query failed")

    client = BigQueryClient()
    stats = client.get_stats(period='7d')

    assert stats == {}
