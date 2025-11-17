"""
Integration tests for Flask API
"""
import pytest
from unittest.mock import patch, MagicMock
from app.api import app


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] in ['healthy', 'degraded']
    assert 'version' in data
    assert 'dependencies' in data


@patch('app.api.scanner.scan_directory')
def test_start_scan(mock_scan, client):
    """Test starting a scan job"""
    mock_scan.return_value = []

    response = client.post('/v1/scan', json={
        'nas_path': '/nas/poker/2024/wsop',
        'recursive': True,
        'generate_proxy': False
    })

    assert response.status_code == 202
    data = response.get_json()
    assert 'scan_id' in data
    assert data['status'] == 'queued'


def test_start_scan_missing_path(client):
    """Test scan without nas_path"""
    response = client.post('/v1/scan', json={})

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_get_scan_status_not_found(client):
    """Test getting status of non-existent scan"""
    response = client.get('/v1/scan/nonexistent-scan-id/status')

    assert response.status_code == 404


@patch('app.api.bq_client.get_video_by_id')
def test_get_file_metadata(mock_get_video, client):
    """Test getting file metadata"""
    mock_get_video.return_value = {
        'video_id': 'test_video',
        'event_id': 'wsop2024_me',
        'duration_seconds': 3600,
        'resolution': '1920x1080'
    }

    response = client.get('/v1/files/test_video')

    assert response.status_code == 200
    data = response.get_json()
    assert data['video_id'] == 'test_video'


@patch('app.api.bq_client.get_video_by_id')
def test_get_file_metadata_not_found(mock_get_video, client):
    """Test getting metadata for non-existent file"""
    mock_get_video.return_value = None

    response = client.get('/v1/files/nonexistent')

    assert response.status_code == 404


@patch('app.api.bq_client.list_videos')
def test_list_files(mock_list, client):
    """Test listing files"""
    mock_list.return_value = [
        {'video_id': 'video1', 'duration_seconds': 3600},
        {'video_id': 'video2', 'duration_seconds': 7200}
    ]

    response = client.get('/v1/files?limit=10&offset=0')

    assert response.status_code == 200
    data = response.get_json()
    assert 'files' in data
    assert len(data['files']) == 2


@patch('app.api.bq_client.list_videos')
def test_list_files_with_event_filter(mock_list, client):
    """Test listing files with event filter"""
    mock_list.return_value = []

    response = client.get('/v1/files?event_id=wsop2024_me&limit=50')

    assert response.status_code == 200
    data = response.get_json()
    assert 'files' in data


@patch('app.api.bq_client.get_video_by_id')
def test_generate_proxy(mock_get_video, client):
    """Test proxy generation request"""
    mock_get_video.return_value = {
        'video_id': 'test_video',
        'event_id': 'wsop2024_me',
        'nas_file_path': '/nas/poker/test.mp4',
        'duration_seconds': 3600
    }

    response = client.post('/v1/proxy/generate', json={
        'file_id': 'test_video',
        'quality': 'medium'
    })

    assert response.status_code == 202
    data = response.get_json()
    assert 'proxy_job_id' in data
    assert data['status'] in ['queued', 'processing']


def test_generate_proxy_missing_file_id(client):
    """Test proxy generation without file_id"""
    response = client.post('/v1/proxy/generate', json={})

    assert response.status_code == 400


@patch('app.api.bq_client.get_video_by_id')
def test_generate_proxy_file_not_found(mock_get_video, client):
    """Test proxy generation for non-existent file"""
    mock_get_video.return_value = None

    response = client.post('/v1/proxy/generate', json={
        'file_id': 'nonexistent'
    })

    assert response.status_code == 404


def test_get_proxy_status_not_found(client):
    """Test getting status of non-existent proxy job"""
    response = client.get('/v1/proxy/nonexistent-job/status')

    assert response.status_code == 404


@patch('app.api.bq_client.get_stats')
@patch('app.api.bq_client.client.query')
def test_get_stats(mock_query, mock_get_stats, client):
    """Test getting statistics"""
    mock_get_stats.return_value = {
        'period': '24h',
        'total_files_scanned': 100,
        'proxies_generated': 90
    }
    mock_query.return_value = [{'total': 1000}]

    response = client.get('/v1/stats?period=24h')

    assert response.status_code == 200
    data = response.get_json()
    assert data['period'] == '24h'
    assert 'total_files_scanned' in data


def test_get_stats_invalid_period(client):
    """Test statistics with invalid period"""
    response = client.get('/v1/stats?period=invalid')

    assert response.status_code == 400


def test_404_handler(client):
    """Test 404 error handler"""
    response = client.get('/nonexistent/endpoint')

    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
