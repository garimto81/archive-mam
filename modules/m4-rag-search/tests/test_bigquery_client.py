"""
Tests for BigQuery Client
"""
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open

from app.bigquery_client import BigQueryClient, get_bigquery_client
from app.config import get_config


class TestBigQueryClientMock:
    """Tests for BigQuery client in development mode"""

    def test_mock_data_loading(self, mock_hand_data, mock_embedding_data):
        """Test loading mock data from JSON files"""
        mock_hands_json = json.dumps(mock_hand_data)
        mock_embeddings_json = json.dumps(mock_embedding_data)

        with patch('builtins.open', mock_open(read_data=mock_hands_json)) as m:
            # First call for hands, second for embeddings
            m.side_effect = [
                mock_open(read_data=mock_hands_json).return_value,
                mock_open(read_data=mock_embeddings_json).return_value
            ]

            client = BigQueryClient()

            # Data should be loaded
            assert client._mock_hands is not None
            assert client._mock_embeddings is not None

    def test_search_hands_mock(self):
        """Test mock search hands"""
        client = BigQueryClient()

        # Manually set mock data
        client._mock_hands = [
            {
                'hand_id': 'HAND_000001',
                'tournament_id': 'WSOP_2024_032',
                'pot_size': 50000,
                'winner': 'Tom Dwan',
                'players': [
                    {'name': 'Tom Dwan', 'position': 1},
                    {'name': 'Phil Ivey', 'position': 2}
                ]
            }
        ]

        client._mock_embeddings = [
            {'hand_id': 'HAND_000001', 'embedding': [0.1] * 768}
        ]

        results = client._search_hands_mock('Tom Dwan', top_k=10, filters=None)

        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]['hand_id'] == 'HAND_000001'
        assert 'relevance_score' in results[0]

    def test_apply_filters_mock_players(self):
        """Test applying player filters in mock mode"""
        client = BigQueryClient()

        hand = {
            'hand_id': 'HAND_000001',
            'players': [
                {'name': 'Tom Dwan'},
                {'name': 'Phil Ivey'}
            ]
        }

        filters = {'players': ['Tom Dwan']}

        assert client._apply_filters_mock(hand, filters) is True

        filters = {'players': ['Phil Hellmuth']}
        assert client._apply_filters_mock(hand, filters) is False

    def test_apply_filters_mock_pot_size(self):
        """Test applying pot size filters in mock mode"""
        client = BigQueryClient()

        hand = {
            'hand_id': 'HAND_000001',
            'pot_size': 50000
        }

        # Minimum pot size
        filters = {'pot_size_min': 30000}
        assert client._apply_filters_mock(hand, filters) is True

        filters = {'pot_size_min': 60000}
        assert client._apply_filters_mock(hand, filters) is False

        # Maximum pot size
        filters = {'pot_size_max': 60000}
        assert client._apply_filters_mock(hand, filters) is True

        filters = {'pot_size_max': 40000}
        assert client._apply_filters_mock(hand, filters) is False

    def test_apply_filters_mock_event_name(self):
        """Test applying event name filter in mock mode"""
        client = BigQueryClient()

        hand = {
            'hand_id': 'HAND_000001',
            'tournament_id': 'WSOP_2024_Main_Event'
        }

        filters = {'event_name_contains': 'WSOP'}
        assert client._apply_filters_mock(hand, filters) is True

        filters = {'event_name_contains': 'WPT'}
        assert client._apply_filters_mock(hand, filters) is False

    def test_log_search_mock(self, caplog):
        """Test search logging in mock mode"""
        client = BigQueryClient()

        client.log_search(
            query_id='search-20241117-001',
            query_text='Tom Dwan',
            user_id='user123',
            results_count=10,
            processing_time_ms=150
        )

        # Check that log message was written
        assert 'Search logged' in caplog.text

    def test_save_feedback_mock(self, caplog):
        """Test feedback saving in mock mode"""
        client = BigQueryClient()

        client.save_feedback(
            query_id='search-20241117-001',
            hand_id='HAND_000001',
            user_id='user123',
            feedback='relevant'
        )

        # Check that log message was written
        assert 'Feedback saved' in caplog.text

    def test_get_search_stats_mock(self):
        """Test getting search stats in mock mode"""
        client = BigQueryClient()

        stats = client.get_search_stats('24h')

        assert 'period' in stats
        assert 'total_searches' in stats
        assert 'unique_users' in stats
        assert stats['period'] == '24h'

    def test_singleton_pattern(self):
        """Test singleton pattern"""
        client1 = get_bigquery_client()
        client2 = get_bigquery_client()

        assert client1 is client2


class TestBigQueryClientProduction:
    """Tests for BigQuery client in production mode (mocked)"""

    @patch('app.bigquery_client.bigquery.Client')
    def test_production_client_initialization(self, mock_bq_class):
        """Test BigQuery client initialization in production"""
        config = get_config()
        original_env = config.ENV

        try:
            config.ENV = 'production'

            mock_client = MagicMock()
            mock_bq_class.return_value = mock_client

            client = BigQueryClient()

            # Should initialize real client
            assert client.client is not None

        finally:
            config.ENV = original_env

    @patch('app.bigquery_client.bigquery.Client')
    def test_search_hands_real_query_structure(self, mock_bq_class):
        """Test real search query structure"""
        config = get_config()
        original_env = config.ENV

        try:
            config.ENV = 'production'

            mock_client = MagicMock()
            mock_query_job = MagicMock()
            mock_query_job.result.return_value = []

            mock_client.query.return_value = mock_query_job
            mock_bq_class.return_value = mock_client

            client = BigQueryClient()

            query_embedding = [0.1] * 768
            results = client._search_hands_real(
                query_embedding=query_embedding,
                top_k=10,
                filters=None
            )

            # Verify query was called
            mock_client.query.assert_called_once()

        finally:
            config.ENV = original_env

    @patch('app.bigquery_client.bigquery.Client')
    def test_search_with_filters_real(self, mock_bq_class):
        """Test real search with filters"""
        config = get_config()
        original_env = config.ENV

        try:
            config.ENV = 'production'

            mock_client = MagicMock()
            mock_query_job = MagicMock()
            mock_query_job.result.return_value = []

            mock_client.query.return_value = mock_query_job
            mock_bq_class.return_value = mock_client

            client = BigQueryClient()

            filters = {
                'players': ['Tom Dwan'],
                'pot_size_min': 10000
            }

            query_embedding = [0.1] * 768
            results = client._search_hands_real(
                query_embedding=query_embedding,
                top_k=10,
                filters=filters
            )

            # Verify query was called
            mock_client.query.assert_called_once()

        finally:
            config.ENV = original_env
