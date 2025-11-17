"""
Tests for Vector Search
"""
import pytest
from unittest.mock import patch, MagicMock

from app.vector_search import VectorSearch, get_vector_search


class TestVectorSearch:
    """Tests for VectorSearch class"""

    def test_search_basic(self, mock_embedding_service, mock_bq_client):
        """Test basic search functionality"""
        with patch('app.vector_search.get_embedding_service', return_value=mock_embedding_service):
            with patch('app.vector_search.get_bigquery_client', return_value=mock_bq_client):
                search = VectorSearch()

                mock_bq_client.search_hands.return_value = [
                    {
                        'hand_id': 'HAND_000001',
                        'relevance_score': 0.92,
                        'summary_text': 'Tom Dwan wins',
                        'tournament_id': 'WSOP_2024_032'
                    }
                ]

                result = search.search("Tom Dwan", top_k=10)

                assert 'results' in result
                assert 'total_results' in result
                assert 'processing_time_ms' in result
                assert len(result['results']) == 1

    def test_search_with_filters(self, mock_embedding_service, mock_bq_client):
        """Test search with filters"""
        with patch('app.vector_search.get_embedding_service', return_value=mock_embedding_service):
            with patch('app.vector_search.get_bigquery_client', return_value=mock_bq_client):
                search = VectorSearch()

                filters = {
                    'players': ['Tom Dwan'],
                    'pot_size_min': 10000
                }

                mock_bq_client.search_hands.return_value = []

                result = search.search("bluff", top_k=10, filters=filters)

                # Verify filters were passed to BigQuery client
                mock_bq_client.search_hands.assert_called_once()
                call_args = mock_bq_client.search_hands.call_args
                assert call_args[1]['filters'] == filters

    def test_search_short_query(self):
        """Test search with too short query"""
        search = VectorSearch()

        with pytest.raises(ValueError, match="Query must be at least"):
            search.search("a", top_k=10)

    def test_search_top_k_capping(self, mock_embedding_service, mock_bq_client):
        """Test that top_k is capped at MAX_TOP_K"""
        with patch('app.vector_search.get_embedding_service', return_value=mock_embedding_service):
            with patch('app.vector_search.get_bigquery_client', return_value=mock_bq_client):
                search = VectorSearch()

                mock_bq_client.search_hands.return_value = []

                result = search.search("test", top_k=1000)

                # Verify top_k was capped
                call_args = mock_bq_client.search_hands.call_args
                assert call_args[1]['top_k'] <= 100

    def test_find_similar_mock(self):
        """Test find similar in mock mode"""
        search = VectorSearch()

        similar = search.find_similar("HAND_000001", top_k=5)

        assert isinstance(similar, list)
        assert len(similar) <= 5
        assert all('hand_id' in hand for hand in similar)
        assert all('relevance_score' in hand for hand in similar)

    def test_singleton_pattern(self):
        """Test singleton pattern"""
        search1 = get_vector_search()
        search2 = get_vector_search()

        assert search1 is search2

    def test_search_timing_info(self, mock_embedding_service, mock_bq_client):
        """Test that search returns timing information"""
        with patch('app.vector_search.get_embedding_service', return_value=mock_embedding_service):
            with patch('app.vector_search.get_bigquery_client', return_value=mock_bq_client):
                search = VectorSearch()

                mock_bq_client.search_hands.return_value = []

                result = search.search("test query", top_k=10)

                assert 'processing_time_ms' in result
                assert isinstance(result['processing_time_ms'], int)
                assert result['processing_time_ms'] >= 0


class TestSearchResultFormatting:
    """Tests for search result formatting"""

    def test_result_structure(self, mock_embedding_service, mock_bq_client):
        """Test that results have correct structure"""
        with patch('app.vector_search.get_embedding_service', return_value=mock_embedding_service):
            with patch('app.vector_search.get_bigquery_client', return_value=mock_bq_client):
                search = VectorSearch()

                mock_bq_client.search_hands.return_value = [
                    {
                        'hand_id': 'HAND_000001',
                        'relevance_score': 0.92,
                        'summary_text': 'Test summary',
                        'tournament_id': 'WSOP_2024_032',
                        'pot_size': 50000,
                        'players': ['Tom Dwan', 'Phil Ivey']
                    }
                ]

                result = search.search("test", top_k=10)

                assert len(result['results']) == 1
                hand = result['results'][0]

                assert 'hand_id' in hand
                assert 'relevance_score' in hand
                assert 'summary_text' in hand
