"""
Configuration for Local Agent (Clipping Worker).

Handles agent-specific settings and environment detection.
"""

import os
import socket


class AgentConfig:
    """Local agent configuration."""

    # Environment
    ENV = os.getenv('POKER_ENV', 'development')

    # Agent Identity
    AGENT_ID = os.getenv('AGENT_ID', socket.gethostname())
    AGENT_ROLE = os.getenv('AGENT_ROLE', 'primary')  # primary or standby

    # GCP Project
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'gg-poker-dev')

    # Pub/Sub
    CLIPPING_REQUESTS_SUBSCRIPTION = os.getenv(
        'CLIPPING_REQUESTS_SUBSCRIPTION',
        'clipping-requests-sub'
    )
    CLIPPING_COMPLETE_TOPIC = os.getenv(
        'CLIPPING_COMPLETE_TOPIC',
        'clipping-complete'
    )

    # GCS
    GCS_BUCKET = os.getenv('GCS_BUCKET', 'gg-subclips')

    # Processing
    TEMP_CLIPS_DIR = os.getenv('TEMP_CLIPS_DIR', '/tmp/clips')
    MAX_CONCURRENT_CLIPS = int(os.getenv('MAX_CONCURRENT_CLIPS', '3'))
    CLIP_TIMEOUT_SECONDS = int(os.getenv('CLIP_TIMEOUT_SECONDS', '300'))  # 5 min

    # Heartbeat
    HEARTBEAT_INTERVAL_SECONDS = int(os.getenv('HEARTBEAT_INTERVAL_SECONDS', '30'))

    # Pub/Sub Emulator (Development)
    PUBSUB_EMULATOR_HOST = os.getenv('PUBSUB_EMULATOR_HOST', 'localhost:8085')

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode."""
        return cls.ENV == 'development'

    @classmethod
    def setup_emulator(cls):
        """Set up Pub/Sub emulator for development."""
        if cls.is_development():
            os.environ['PUBSUB_EMULATOR_HOST'] = cls.PUBSUB_EMULATOR_HOST

    @classmethod
    def get_temp_clips_dir(cls) -> str:
        """Get and create temp clips directory."""
        os.makedirs(cls.TEMP_CLIPS_DIR, exist_ok=True)
        return cls.TEMP_CLIPS_DIR
