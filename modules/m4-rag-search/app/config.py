"""
Configuration management for M4 RAG Search Service

Supports development (mock data) and production (real Vertex AI) modes
via POKER_ENV environment variable.
"""
import os
from typing import Optional


class Config:
    """Base configuration"""
    # Environment
    ENV = os.getenv('POKER_ENV', 'development')
    DEBUG = ENV == 'development'

    # GCP Project
    GCP_PROJECT = os.getenv('GCP_PROJECT', 'gg-poker')
    GCP_REGION = os.getenv('GCP_REGION', 'us-central1')

    # BigQuery
    BQ_DATASET = 'prod' if ENV == 'production' else 'dev'
    BQ_HAND_TABLE = f'{BQ_DATASET}.hand_summary'
    BQ_EMBEDDING_TABLE = f'{BQ_DATASET}.hand_embeddings'
    BQ_SEARCH_LOG_TABLE = f'{BQ_DATASET}.search_logs'
    BQ_FEEDBACK_TABLE = f'{BQ_DATASET}.search_feedback'

    # Vertex AI
    VERTEX_AI_LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'textembedding-gecko@004')
    EMBEDDING_DIMENSION = 768

    # Search Configuration
    DEFAULT_TOP_K = 20
    MAX_TOP_K = 100
    MIN_QUERY_LENGTH = 2

    # Re-ranking
    ENABLE_RERANKING = ENV == 'production'
    RERANK_TOP_N = 50  # Re-rank top 50 results before returning top_k

    # Autocomplete
    AUTOCOMPLETE_LIMIT = 10
    AUTOCOMPLETE_MIN_QUERY_LENGTH = 2

    # Mock Data Paths (for development)
    MOCK_HAND_DATA_PATH = os.getenv(
        'MOCK_HAND_DATA_PATH',
        '../../mock_data/bigquery/hand_summary_mock.json'
    )
    MOCK_EMBEDDING_DATA_PATH = os.getenv(
        'MOCK_EMBEDDING_DATA_PATH',
        '../../mock_data/embeddings/hand_embeddings_mock.json'
    )

    # API Server
    PORT = int(os.getenv('PORT', 8004))
    HOST = os.getenv('HOST', '0.0.0.0')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Authentication
    REQUIRE_AUTH = ENV == 'production'
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key')

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.ENV == 'development'

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return cls.ENV == 'production'

    @classmethod
    def get_mock_data_path(cls, data_type: str) -> str:
        """Get absolute path to mock data file"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        if data_type == 'hands':
            rel_path = cls.MOCK_HAND_DATA_PATH
        elif data_type == 'embeddings':
            rel_path = cls.MOCK_EMBEDDING_DATA_PATH
        else:
            raise ValueError(f"Unknown data type: {data_type}")

        # Convert relative path to absolute
        return os.path.join(base_dir, rel_path)


class DevelopmentConfig(Config):
    """Development configuration (mock data)"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Production configuration (real Vertex AI)"""
    DEBUG = False
    ENV = 'production'
    REQUIRE_AUTH = True


def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('POKER_ENV', 'development')

    if env == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()
