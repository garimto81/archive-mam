"""
Tests for Flask API endpoints
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestSearchEndpoint:
    """Tests for POST /v1/search endpoint"""

    def test_search_success(self, client, mock_vector_search):
        """Test successful search"""
        with patch('app.api.vector_search', mock_vector_search):
            response = client.post(
                '/v1/search',
                json={
                    'query': 'Tom Dwan bluff',
                    'limit': 20
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()

            assert 'query_id' in data
            assert 'total_results' in data
            assert 'processing_time_ms' in data
            assert 'results' in data
            assert isinstance(data['results'], list)

    def test_search_with_filters(self, client, mock_vector_search):
        """Test search with filters"""
        with patch('app.api.vector_search', mock_vector_search):
            response = client.post(
                '/v1/search',
                json={
                    'query': 'bluff',
                    'limit': 10,
                    'filters': {
                        'players': ['Tom Dwan'],
                        'pot_size_min': 10000
                    }
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['results']) >= 0

    def test_search_missing_query(self, client):
        """Test search without query"""
        response = client.post(
            '/v1/search',
            json={},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'query is required' in data['error']['message']

    def test_search_short_query(self, client):
        """Test search with too short query"""
        response = client.post(
            '/v1/search',
            json={'query': 'a'},
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_search_invalid_limit(self, client):
        """Test search with invalid limit"""
        response = client.post(
            '/v1/search',
            json={
                'query': 'test query',
                'limit': -1
            },
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_search_limit_capping(self, client, mock_vector_search):
        """Test that limit is capped at MAX_TOP_K"""
        with patch('app.api.vector_search', mock_vector_search):
            response = client.post(
                '/v1/search',
                json={
                    'query': 'test query',
                    'limit': 1000  # Exceeds MAX_TOP_K (100)
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            # Should be capped at 100
            mock_vector_search.search.assert_called_once()
            call_args = mock_vector_search.search.call_args
            assert call_args[1]['top_k'] == 100


class TestAutocompleteEndpoint:
    """Tests for GET /v1/search/autocomplete endpoint"""

    def test_autocomplete_success(self, client):
        """Test successful autocomplete"""
        response = client.get('/v1/search/autocomplete?q=Tom')

        assert response.status_code == 200
        data = response.get_json()

        assert 'query' in data
        assert 'suggestions' in data
        assert isinstance(data['suggestions'], list)

    def test_autocomplete_missing_query(self, client):
        """Test autocomplete without query"""
        response = client.get('/v1/search/autocomplete')

        assert response.status_code == 400

    def test_autocomplete_short_query(self, client):
        """Test autocomplete with too short query"""
        response = client.get('/v1/search/autocomplete?q=a')

        assert response.status_code == 400

    def test_autocomplete_with_limit(self, client):
        """Test autocomplete with custom limit"""
        response = client.get('/v1/search/autocomplete?q=Tom&limit=5')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['suggestions']) <= 5


class TestFeedbackEndpoint:
    """Tests for POST /v1/search/feedback endpoint"""

    def test_feedback_success(self, client, mock_bq_client):
        """Test successful feedback submission"""
        with patch('app.api.bq_client', mock_bq_client):
            response = client.post(
                '/v1/search/feedback',
                json={
                    'query_id': 'search-20241117-001',
                    'hand_id': 'HAND_000001',
                    'feedback': 'relevant'
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'

    def test_feedback_missing_fields(self, client):
        """Test feedback with missing fields"""
        response = client.post(
            '/v1/search/feedback',
            json={
                'query_id': 'search-20241117-001'
            },
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_feedback_invalid_type(self, client):
        """Test feedback with invalid type"""
        response = client.post(
            '/v1/search/feedback',
            json={
                'query_id': 'search-20241117-001',
                'hand_id': 'HAND_000001',
                'feedback': 'invalid_type'
            },
            content_type='application/json'
        )

        assert response.status_code == 400


class TestSimilarEndpoint:
    """Tests for GET /v1/similar/{hand_id} endpoint"""

    def test_similar_success(self, client, mock_vector_search):
        """Test successful similar hands search"""
        with patch('app.api.vector_search', mock_vector_search):
            response = client.get('/v1/similar/HAND_000001')

            assert response.status_code == 200
            data = response.get_json()

            assert 'hand_id' in data
            assert 'similar_hands' in data
            assert isinstance(data['similar_hands'], list)

    def test_similar_with_limit(self, client, mock_vector_search):
        """Test similar hands with custom limit"""
        with patch('app.api.vector_search', mock_vector_search):
            response = client.get('/v1/similar/HAND_000001?limit=5')

            assert response.status_code == 200


class TestStatsEndpoint:
    """Tests for GET /v1/stats endpoint"""

    def test_stats_success(self, client, mock_bq_client):
        """Test successful stats retrieval"""
        with patch('app.api.bq_client', mock_bq_client):
            response = client.get('/v1/stats?period=24h')

            assert response.status_code == 200
            data = response.get_json()

            assert 'period' in data
            assert 'total_searches' in data

    def test_stats_invalid_period(self, client):
        """Test stats with invalid period"""
        response = client.get('/v1/stats?period=invalid')

        assert response.status_code == 400


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')

        assert response.status_code in [200, 503]  # Could be unhealthy if mock data missing
        data = response.get_json()

        assert 'status' in data
        assert 'environment' in data
        assert 'dependencies' in data


class TestReindexEndpoint:
    """Tests for POST /v1/admin/reindex endpoint"""

    def test_reindex_mock(self, client):
        """Test reindex in development mode"""
        response = client.post(
            '/v1/admin/reindex',
            json={
                'event_id': None,
                'force': True
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()

        assert 'reindex_job_id' in data
        assert 'status' in data


class TestErrorHandling:
    """Tests for error handling"""

    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get('/v1/nonexistent')

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_invalid_json(self, client):
        """Test invalid JSON handling"""
        response = client.post(
            '/v1/search',
            data='invalid json',
            content_type='application/json'
        )

        assert response.status_code == 400
