"""
Tests for Flask API endpoints.

Covers all 6 API endpoints with comprehensive test cases.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.api import app
from app.status_tracker import get_tracker


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def tracker():
    """Get tracker instance and clear before each test."""
    tracker = get_tracker()
    tracker._requests.clear()
    return tracker


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_check_success(self, client):
        """Test health check returns 200."""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()

        assert 'status' in data
        assert 'api_status' in data
        assert data['api_status'] == 'ok'
        assert 'agents' in data
        assert 'queue_depth' in data

    def test_health_check_includes_environment(self, client):
        """Test health check includes environment info."""
        response = client.get('/health')
        data = response.get_json()

        assert 'environment' in data
        assert data['environment'] == 'development'


class TestClipRequestEndpoint:
    """Tests for POST /v1/clip/request endpoint."""

    @patch('app.api.publisher')
    def test_clip_request_success(self, mock_publisher, client, tracker):
        """Test successful clipping request."""
        mock_publisher.publish_clipping_request.return_value = 'msg-123'

        payload = {
            'hand_id': 'wsop2024_me_d3_h154',
            'nas_video_path': '/nas/poker/test.mp4',
            'start_seconds': 100,
            'end_seconds': 200,
            'output_quality': 'high'
        }

        response = client.post('/v1/clip/request', json=payload)

        assert response.status_code == 200
        data = response.get_json()

        assert 'request_id' in data
        assert data['hand_id'] == 'wsop2024_me_d3_h154'
        assert data['status'] == 'queued'
        assert 'estimated_duration_sec' in data
        assert 'queue_position' in data
        assert 'created_at' in data

        # Verify publisher was called
        mock_publisher.publish_clipping_request.assert_called_once()

    @patch('app.api.publisher')
    def test_clip_request_default_quality(self, mock_publisher, client):
        """Test clipping request with default quality."""
        mock_publisher.publish_clipping_request.return_value = 'msg-123'

        payload = {
            'hand_id': 'test_hand',
            'nas_video_path': '/nas/test.mp4',
            'start_seconds': 0,
            'end_seconds': 10
        }

        response = client.post('/v1/clip/request', json=payload)

        assert response.status_code == 200

        # Verify publisher was called with default quality
        call_args = mock_publisher.publish_clipping_request.call_args
        assert call_args[1]['output_quality'] == 'high'

    def test_clip_request_missing_field(self, client):
        """Test request with missing required field."""
        payload = {
            'hand_id': 'test_hand',
            # Missing nas_video_path
            'start_seconds': 0,
            'end_seconds': 10
        }

        response = client.post('/v1/clip/request', json=payload)

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'nas_video_path' in data['error']['message']

    def test_clip_request_invalid_time_range(self, client):
        """Test request with invalid time range."""
        payload = {
            'hand_id': 'test_hand',
            'nas_video_path': '/nas/test.mp4',
            'start_seconds': 200,
            'end_seconds': 100  # End before start
        }

        response = client.post('/v1/clip/request', json=payload)

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'start_seconds' in data['error']['message']

    def test_clip_request_exceeds_max_duration(self, client):
        """Test request exceeding maximum duration."""
        payload = {
            'hand_id': 'test_hand',
            'nas_video_path': '/nas/test.mp4',
            'start_seconds': 0,
            'end_seconds': 700  # 11+ minutes
        }

        response = client.post('/v1/clip/request', json=payload)

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'duration' in data['error']['message'].lower()

    def test_clip_request_invalid_quality(self, client):
        """Test request with invalid quality."""
        payload = {
            'hand_id': 'test_hand',
            'nas_video_path': '/nas/test.mp4',
            'start_seconds': 0,
            'end_seconds': 10,
            'output_quality': 'invalid'
        }

        response = client.post('/v1/clip/request', json=payload)

        assert response.status_code == 400


class TestClipStatusEndpoint:
    """Tests for GET /v1/clip/{request_id}/status endpoint."""

    def test_get_status_success(self, client, tracker):
        """Test getting status of existing request."""
        # Create a request
        request = tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        response = client.get('/v1/clip/clip-20241117-001/status')

        assert response.status_code == 200
        data = response.get_json()

        assert data['request_id'] == 'clip-20241117-001'
        assert data['hand_id'] == 'test_hand'
        assert data['status'] == 'queued'

    def test_get_status_not_found(self, client):
        """Test getting status of non-existent request."""
        response = client.get('/v1/clip/clip-20241117-999/status')

        assert response.status_code == 404
        data = response.get_json()

        assert 'error' in data
        assert 'not found' in data['error']['message'].lower()

    def test_get_status_invalid_format(self, client):
        """Test getting status with invalid request_id format."""
        response = client.get('/v1/clip/invalid-id/status')

        assert response.status_code == 400

    def test_get_status_completed(self, client, tracker):
        """Test getting status of completed request."""
        # Create and complete a request
        request = tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        tracker.update_status(
            'clip-20241117-001',
            status='completed',
            output_gcs_path='gs://bucket/test.mp4',
            file_size_bytes=1024000
        )

        response = client.get('/v1/clip/clip-20241117-001/status')

        assert response.status_code == 200
        data = response.get_json()

        assert data['status'] == 'completed'
        assert 'output_gcs_path' in data
        assert 'file_size_bytes' in data


class TestDownloadUrlEndpoint:
    """Tests for GET /v1/clip/{request_id}/download endpoint."""

    @patch('app.api.gcs_client')
    def test_get_download_url_success(self, mock_gcs, client, tracker):
        """Test getting download URL for completed clip."""
        # Create completed request
        tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        tracker.update_status(
            'clip-20241117-001',
            status='completed',
            output_gcs_path='gs://bucket/test.mp4',
            file_size_bytes=1024000
        )

        # Mock GCS signed URL
        mock_gcs.generate_signed_url.return_value = (
            'https://storage.googleapis.com/signed-url',
            '2024-11-24T14:00:00Z'
        )

        response = client.get('/v1/clip/clip-20241117-001/download')

        assert response.status_code == 200
        data = response.get_json()

        assert 'download_url' in data
        assert 'expires_at' in data
        assert data['request_id'] == 'clip-20241117-001'

        # Verify GCS client was called
        mock_gcs.generate_signed_url.assert_called_once_with('test_hand')

    def test_get_download_url_not_ready(self, client, tracker):
        """Test getting download URL for incomplete clip."""
        # Create queued request
        tracker.create_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        response = client.get('/v1/clip/clip-20241117-001/download')

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'not ready' in data['error']['message'].lower()

    def test_get_download_url_not_found(self, client):
        """Test getting download URL for non-existent request."""
        response = client.get('/v1/clip/clip-20241117-999/download')

        assert response.status_code == 404


class TestAdminAgentsEndpoint:
    """Tests for GET /v1/admin/agents endpoint."""

    def test_get_agents_success(self, client):
        """Test getting agent status."""
        response = client.get('/v1/admin/agents')

        assert response.status_code == 200
        data = response.get_json()

        assert 'agents' in data
        assert isinstance(data['agents'], list)
        assert len(data['agents']) > 0

        # Check agent structure
        agent = data['agents'][0]
        assert 'agent_id' in agent
        assert 'role' in agent
        assert 'status' in agent
        assert 'last_heartbeat' in agent
        assert 'queue_depth' in agent
        assert 'completed_clips_24h' in agent


class TestStatsEndpoint:
    """Tests for GET /v1/stats endpoint."""

    def test_get_stats_default_period(self, client, tracker):
        """Test getting stats with default period."""
        # Create some requests
        for i in range(5):
            tracker.create_request(
                request_id=f'clip-20241117-{i:03d}',
                hand_id=f'hand_{i}',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        # Complete some
        tracker.update_status('clip-20241117-000', 'completed')
        tracker.update_status('clip-20241117-001', 'completed')
        tracker.update_status('clip-20241117-002', 'failed')

        response = client.get('/v1/stats')

        assert response.status_code == 200
        data = response.get_json()

        assert data['period'] == '24h'
        assert data['total_requests'] == 5
        assert data['completed'] == 2
        assert data['failed'] == 1
        assert data['queued'] == 2
        assert 'success_rate' in data
        assert 'avg_processing_time_sec' in data

    def test_get_stats_7d_period(self, client):
        """Test getting stats for 7 days."""
        response = client.get('/v1/stats?period=7d')

        assert response.status_code == 200
        data = response.get_json()

        assert data['period'] == '7d'

    def test_get_stats_invalid_period(self, client):
        """Test getting stats with invalid period."""
        response = client.get('/v1/stats?period=invalid')

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
