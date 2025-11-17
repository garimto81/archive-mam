"""
Pytest configuration and fixtures for M4 RAG Search tests
"""
import os
import pytest
import json
from unittest.mock import Mock, MagicMock

# Set test environment
os.environ['POKER_ENV'] = 'development'

from app.api import app as flask_app
from app.config import get_config


@pytest.fixture
def app():
    """Flask app fixture"""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def config():
    """Configuration fixture"""
    return get_config()


@pytest.fixture
def mock_hand_data():
    """Mock hand summary data"""
    return [
        {
            "hand_id": "HAND_000001",
            "tournament_id": "WSOP_2024_032",
            "table_number": 68,
            "hand_number": 1,
            "pot_size": 45685,
            "winner": "Tom Dwan",
            "timestamp": "2025-09-24T14:19:14.545483",
            "players": [
                {"name": "Tom Dwan", "position": 1, "stack": 14819},
                {"name": "Phil Ivey", "position": 2, "stack": 43091}
            ]
        },
        {
            "hand_id": "HAND_000002",
            "tournament_id": "WSOP_2024_010",
            "table_number": 27,
            "hand_number": 2,
            "pot_size": 32100,
            "winner": "Phil Hellmuth",
            "timestamp": "2025-09-24T15:20:30.123456",
            "players": [
                {"name": "Phil Hellmuth", "position": 1, "stack": 50000},
                {"name": "Daniel Negreanu", "position": 2, "stack": 48000}
            ]
        }
    ]


@pytest.fixture
def mock_embedding_data():
    """Mock embedding data"""
    return [
        {
            "hand_id": "HAND_000001",
            "embedding": [0.1] * 768  # 768-dim vector
        },
        {
            "hand_id": "HAND_000002",
            "embedding": [0.2] * 768
        }
    ]


@pytest.fixture
def mock_search_result():
    """Mock search result"""
    return {
        'results': [
            {
                'hand_id': 'HAND_000001',
                'relevance_score': 0.92,
                'summary_text': 'Tom Dwan wins $45,685 pot',
                'tournament_id': 'WSOP_2024_032',
                'pot_size': 45685,
                'winner': 'Tom Dwan',
                'players': ['Tom Dwan', 'Phil Ivey'],
                'timestamp': '2025-09-24T14:19:14.545483'
            }
        ],
        'total_results': 1,
        'processing_time_ms': 150
    }


@pytest.fixture
def mock_bq_client(monkeypatch, mock_search_result):
    """Mock BigQuery client"""
    mock_client = MagicMock()

    # Mock search_hands method
    mock_client.search_hands.return_value = mock_search_result['results']

    # Mock log_search method
    mock_client.log_search.return_value = None

    # Mock save_feedback method
    mock_client.save_feedback.return_value = None

    # Mock get_search_stats method
    mock_client.get_search_stats.return_value = {
        'period': '24h',
        'total_searches': 125,
        'unique_users': 15
    }

    # Mock data attributes
    mock_client._mock_hands = []
    mock_client._mock_embeddings = []

    return mock_client


@pytest.fixture
def mock_embedding_service(monkeypatch):
    """Mock embedding service"""
    mock_service = MagicMock()

    # Mock generate_embedding method
    mock_service.generate_embedding.return_value = [0.1] * 768

    # Mock generate_embeddings_batch method
    mock_service.generate_embeddings_batch.return_value = [[0.1] * 768, [0.2] * 768]

    return mock_service


@pytest.fixture
def mock_vector_search(monkeypatch, mock_search_result):
    """Mock vector search"""
    mock_search = MagicMock()

    # Mock search method
    mock_search.search.return_value = mock_search_result

    # Mock find_similar method
    mock_search.find_similar.return_value = [
        {
            'hand_id': 'HAND_000002',
            'relevance_score': 0.88,
            'tournament_id': 'WSOP_2024_010'
        }
    ]

    return mock_search
