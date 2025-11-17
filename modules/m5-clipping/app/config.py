"""
Configuration management for M5 Clipping Service.

Handles environment-specific settings for development vs production.
"""

import os
from typing import Dict, Any


class Config:
    """Base configuration class."""

    # Environment
    ENV = os.getenv('POKER_ENV', 'development')
    DEBUG = ENV == 'development'

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # GCP Project
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gg-poker-dev')

    # Pub/Sub Topics
    CLIPPING_REQUESTS_TOPIC = os.getenv('CLIPPING_REQUESTS_TOPIC', 'clipping-requests')
    CLIPPING_COMPLETE_TOPIC = os.getenv('CLIPPING_COMPLETE_TOPIC', 'clipping-complete')
    CLIPPING_REQUESTS_SUBSCRIPTION = os.getenv(
        'CLIPPING_REQUESTS_SUBSCRIPTION',
        'clipping-requests-sub'
    )

    # GCS Storage
    GCS_BUCKET = os.getenv('GCS_BUCKET', 'gg-subclips')
    SIGNED_URL_EXPIRY_HOURS = int(os.getenv('SIGNED_URL_EXPIRY_HOURS', '168'))  # 7 days

    # Local Storage (Development)
    MOCK_CLIPS_DIR = os.getenv('MOCK_CLIPS_DIR', '/tmp/mock-clips')

    # FFmpeg
    FFMPEG_TIMEOUT_SECONDS = int(os.getenv('FFMPEG_TIMEOUT_SECONDS', '300'))  # 5 minutes

    # Request ID Pattern
    REQUEST_ID_PREFIX = 'clip'

    @classmethod
    def get_pubsub_emulator_host(cls) -> str | None:
        """Get Pub/Sub emulator host if in development mode."""
        if cls.ENV == 'development':
            return os.getenv('PUBSUB_EMULATOR_HOST', 'localhost:8085')
        return None

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode."""
        return cls.ENV == 'development'

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'env': cls.ENV,
            'debug': cls.DEBUG,
            'gcp_project_id': cls.GCP_PROJECT_ID,
            'clipping_requests_topic': cls.CLIPPING_REQUESTS_TOPIC,
            'clipping_complete_topic': cls.CLIPPING_COMPLETE_TOPIC,
            'gcs_bucket': cls.GCS_BUCKET,
            'signed_url_expiry_hours': cls.SIGNED_URL_EXPIRY_HOURS,
            'pubsub_emulator_host': cls.get_pubsub_emulator_host(),
        }


class DevelopmentConfig(Config):
    """Development configuration with Pub/Sub Emulator."""
    DEBUG = True
    ENV = 'development'

    @classmethod
    def setup_emulator(cls):
        """Set up Pub/Sub emulator environment variable."""
        emulator_host = cls.get_pubsub_emulator_host()
        if emulator_host:
            os.environ['PUBSUB_EMULATOR_HOST'] = emulator_host


class ProductionConfig(Config):
    """Production configuration with real GCP services."""
    DEBUG = False
    ENV = 'production'

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production

    # GCP Project
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gg-poker-prod')

    # GCS
    GCS_BUCKET = os.getenv('GCS_BUCKET', 'gg-subclips')

    @classmethod
    def validate(cls):
        """Validate production configuration."""
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production")

        if not os.getenv('GCP_PROJECT_ID'):
            raise ValueError("GCP_PROJECT_ID must be set in production")


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv('POKER_ENV', 'development')

    if env == 'production':
        config = ProductionConfig
        config.validate()
    else:
        config = DevelopmentConfig
        config.setup_emulator()

    return config
