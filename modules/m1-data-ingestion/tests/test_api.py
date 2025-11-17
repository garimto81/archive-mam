"""
Unit tests for Flask API endpoints
"""
import json
import pytest
from unittest.mock import Mock, patch

from app.api import app, job_status_store, generate_job_id


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config['TESTING'] = True

    # Clear job store before each test
    job_status_store.clear()

    with app.test_client() as client:
        yield client


class TestIngestEndpoint:
    """Test POST /v1/ingest endpoint"""

    @patch('app.api.run_pipeline_async')
    def test_ingest_valid_request(self, mock_run_pipeline, client):
        """Test ingestion with valid request"""
        response = client.post('/v1/ingest', json={
            'gcs_path': 'gs://gg-poker-ati/sample.jsonl',
            'event_id': 'wsop2024_me',
            'tournament_day': 1
        })

        assert response.status_code == 202
        data = response.get_json()

        assert 'job_id' in data
        assert data['status'] == 'queued'
        assert data['gcs_path'] == 'gs://gg-poker-ati/sample.jsonl'
        assert data['event_id'] == 'wsop2024_me'
        assert 'created_at' in data

    @patch('app.api.run_pipeline_async')
    def test_ingest_cash_game_no_tournament_day(self, mock_run_pipeline, client):
        """Test ingestion for cash game (no tournament_day)"""
        response = client.post('/v1/ingest', json={
            'gcs_path': 'gs://gg-poker-ati/cash_game.jsonl',
            'event_id': 'gg_live_cash',
            'tournament_day': None
        })

        assert response.status_code == 202
        data = response.get_json()

        assert 'job_id' in data
        assert data['status'] == 'queued'

    def test_ingest_missing_gcs_path(self, client):
        """Test ingestion without gcs_path"""
        response = client.post('/v1/ingest', json={
            'event_id': 'wsop2024_me',
            'tournament_day': 1
        })

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert data['error']['code'] == 'INVALID_REQUEST'
        assert 'gcs_path' in data['error']['message']

    def test_ingest_missing_event_id(self, client):
        """Test ingestion without event_id"""
        response = client.post('/v1/ingest', json={
            'gcs_path': 'gs://gg-poker-ati/sample.jsonl',
            'tournament_day': 1
        })

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert data['error']['code'] == 'INVALID_REQUEST'
        assert 'event_id' in data['error']['message']

    def test_ingest_invalid_gcs_path_format(self, client):
        """Test ingestion with invalid GCS path"""
        response = client.post('/v1/ingest', json={
            'gcs_path': 'not-a-gcs-path',
            'event_id': 'wsop2024_me'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'gs://' in data['error']['message']

    def test_ingest_invalid_file_extension(self, client):
        """Test ingestion with non-JSONL file"""
        response = client.post('/v1/ingest', json={
            'gcs_path': 'gs://gg-poker-ati/sample.json',  # .json instead of .jsonl
            'event_id': 'wsop2024_me'
        })

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert '.jsonl' in data['error']['message']

    def test_ingest_empty_body(self, client):
        """Test ingestion with empty request body"""
        response = client.post('/v1/ingest', json=None)

        assert response.status_code == 400


class TestStatusEndpoint:
    """Test GET /v1/ingest/{job_id}/status endpoint"""

    def test_get_status_existing_job(self, client):
        """Test getting status of existing job"""
        # Create a job
        job_id = 'ingest-20241117-001'
        job_status_store[job_id] = {
            'job_id': job_id,
            'status': 'completed',
            'gcs_path': 'gs://gg-poker-ati/sample.jsonl',
            'rows_processed': 1500,
            'rows_failed': 0
        }

        response = client.get(f'/v1/ingest/{job_id}/status')

        assert response.status_code == 200
        data = response.get_json()

        assert data['job_id'] == job_id
        assert data['status'] == 'completed'
        assert data['rows_processed'] == 1500

    def test_get_status_nonexistent_job(self, client):
        """Test getting status of non-existent job"""
        response = client.get('/v1/ingest/ingest-99999999-999/status')

        assert response.status_code == 404
        data = response.get_json()

        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'

    def test_get_status_processing_job(self, client):
        """Test getting status of job in progress"""
        job_id = 'ingest-20241117-002'
        job_status_store[job_id] = {
            'job_id': job_id,
            'status': 'processing',
            'gcs_path': 'gs://gg-poker-ati/sample.jsonl',
            'rows_processed': 850,
            'started_at': '2024-11-17T10:00:00Z',
            'completed_at': None
        }

        response = client.get(f'/v1/ingest/{job_id}/status')

        assert response.status_code == 200
        data = response.get_json()

        assert data['status'] == 'processing'
        assert data['rows_processed'] == 850
        assert data['completed_at'] is None


class TestStatsEndpoint:
    """Test GET /v1/stats endpoint"""

    @patch('app.api.get_bigquery_client')
    def test_get_stats_default_period(self, mock_get_client, client):
        """Test getting stats with default period (24h)"""
        # Mock BigQuery client
        mock_client = Mock()
        mock_client.get_stats.return_value = {
            'period': '24h',
            'total_hands': 15000,
            'total_events': 5,
            'last_ingestion_timestamp': '2024-11-17T12:00:00Z'
        }
        mock_get_client.return_value = mock_client

        response = client.get('/v1/stats')

        assert response.status_code == 200
        data = response.get_json()

        assert data['period'] == '24h'
        assert data['total_hands'] == 15000
        assert data['total_events'] == 5

    @patch('app.api.get_bigquery_client')
    def test_get_stats_custom_period(self, mock_get_client, client):
        """Test getting stats with custom period"""
        mock_client = Mock()
        mock_client.get_stats.return_value = {
            'period': '7d',
            'total_hands': 100000,
            'total_events': 25
        }
        mock_get_client.return_value = mock_client

        response = client.get('/v1/stats?period=7d')

        assert response.status_code == 200
        data = response.get_json()

        assert data['period'] == '7d'
        mock_client.get_stats.assert_called_once_with(period='7d', event_id=None)

    @patch('app.api.get_bigquery_client')
    def test_get_stats_filter_by_event(self, mock_get_client, client):
        """Test getting stats filtered by event_id"""
        mock_client = Mock()
        mock_client.get_stats.return_value = {
            'period': '24h',
            'total_hands': 5000,
            'total_events': 1
        }
        mock_get_client.return_value = mock_client

        response = client.get('/v1/stats?event_id=wsop2024_me')

        assert response.status_code == 200
        mock_client.get_stats.assert_called_once_with(period='24h', event_id='wsop2024_me')

    def test_get_stats_invalid_period(self, client):
        """Test getting stats with invalid period"""
        response = client.get('/v1/stats?period=invalid')

        assert response.status_code == 400
        data = response.get_json()

        assert 'error' in data
        assert 'period' in data['error']['message']


class TestHealthEndpoint:
    """Test GET /health endpoint"""

    @patch('app.api.get_bigquery_client')
    def test_health_check_healthy(self, mock_get_client, client):
        """Test health check when all dependencies are OK"""
        mock_client = Mock()
        mock_client.validate_connection.return_value = True
        mock_get_client.return_value = mock_client

        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()

        assert data['status'] == 'healthy'
        assert data['version'] == '1.0.0'
        assert 'dependencies' in data
        assert data['dependencies']['bigquery'] == 'ok'

    @patch('app.api.get_bigquery_client')
    def test_health_check_degraded(self, mock_get_client, client):
        """Test health check when BigQuery is down"""
        mock_client = Mock()
        mock_client.validate_connection.return_value = False
        mock_get_client.return_value = mock_client

        response = client.get('/health')

        assert response.status_code == 503
        data = response.get_json()

        assert data['status'] == 'degraded'


class TestJobIdGeneration:
    """Test job ID generation"""

    def test_generate_job_id_format(self):
        """Test job ID format is correct"""
        job_id = generate_job_id()

        # Should match pattern: ingest-YYYYMMDD-NNN
        assert job_id.startswith('ingest-')

        parts = job_id.split('-')
        assert len(parts) == 3
        assert parts[0] == 'ingest'
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 3  # NNN (zero-padded)

    def test_generate_job_id_sequence(self):
        """Test job IDs increment sequentially"""
        job_status_store.clear()

        job_id_1 = generate_job_id()
        job_status_store[job_id_1] = {}

        job_id_2 = generate_job_id()
        job_status_store[job_id_2] = {}

        # Extract sequence numbers
        seq_1 = int(job_id_1.split('-')[-1])
        seq_2 = int(job_id_2.split('-')[-1])

        assert seq_2 == seq_1 + 1


class TestErrorHandling:
    """Test error handling"""

    def test_404_endpoint_not_found(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get('/v1/nonexistent')

        assert response.status_code == 404
        data = response.get_json()

        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
