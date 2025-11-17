"""
Configuration for M3 Timecode Validation Service
"""
import os

# Environment
POKER_ENV = os.getenv('POKER_ENV', 'development')
IS_PRODUCTION = POKER_ENV == 'production'

# GCP Configuration
PROJECT_ID = 'gg-poker'
REGION = 'us-central1'

# BigQuery Configuration
if IS_PRODUCTION:
    DATASET = 'prod'
    HAND_TABLE = f'{DATASET}.hand_summary'
    VIDEO_TABLE = f'{DATASET}.video_files'
    VALIDATION_TABLE = f'{DATASET}.timecode_validation'
else:
    DATASET = 'dev'
    HAND_TABLE = f'{DATASET}.hand_summary_mock'
    VIDEO_TABLE = f'{DATASET}.video_files_mock'
    VALIDATION_TABLE = f'{DATASET}.timecode_validation_mock'

# Mock Data Paths (Development only)
MOCK_HAND_DATA = os.getenv(
    'BIGQUERY_MOCK_DATA',
    'mock_data/bigquery/hand_summary_mock.json'
)
MOCK_VIDEO_DATA = os.getenv(
    'VIDEO_MOCK_DATA',
    'mock_data/bigquery/video_files_mock.json'
)

# Vision API Configuration
VISION_API_ENABLED = os.getenv('VISION_API_ENABLED', 'true').lower() == 'true'
VISION_CONFIDENCE_THRESHOLD = float(os.getenv('VISION_CONFIDENCE_THRESHOLD', '0.5'))

# sync_score Configuration
SYNC_SCORE_WEIGHTS = {
    'vision': 50.0,
    'duration': 30.0,
    'player_count': 20.0
}

# Validation Thresholds
PERFECT_SYNC_THRESHOLD = 90.0
GOOD_SYNC_THRESHOLD = 80.0
NEEDS_OFFSET_THRESHOLD = 60.0

# FFmpeg Configuration
FFMPEG_PATH = os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')
FRAME_EXTRACT_QUALITY = int(os.getenv('FRAME_EXTRACT_QUALITY', '2'))  # 1-31, lower is better

# GCS Configuration
GCS_BUCKET_PROXY = 'gg-poker-proxy'
GCS_BUCKET_VALIDATION = 'gg-poker-validation-frames'

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = int(os.getenv('PORT', '8003'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true' and not IS_PRODUCTION

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
