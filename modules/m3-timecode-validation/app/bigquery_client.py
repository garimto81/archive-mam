"""
BigQuery Client for M3 Timecode Validation Service
Supports both Mock (development) and Real (production) BigQuery
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

from . import config

logger = logging.getLogger(__name__)


class BigQueryClient:
    """
    BigQuery client with Mock/Real data switching
    """

    def __init__(self):
        self.is_production = config.IS_PRODUCTION
        self.project_id = config.PROJECT_ID

        if self.is_production:
            self.client = bigquery.Client(project=self.project_id)
            logger.info("BigQuery client initialized for PRODUCTION")
        else:
            # Mock mode: Load JSON data
            self.mock_hands = self._load_mock_data(config.MOCK_HAND_DATA)
            self.mock_videos = self._load_mock_data(config.MOCK_VIDEO_DATA)
            logger.info("BigQuery client initialized for DEVELOPMENT (Mock mode)")

    def _load_mock_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load mock data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} records from {file_path}")
                return data
        except FileNotFoundError:
            logger.warning(f"Mock data file not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mock data: {e}")
            return []

    def get_hand_metadata(self, hand_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve hand metadata by hand_id

        Args:
            hand_id: Hand identifier

        Returns:
            Hand metadata dict or None if not found
        """
        if not self.is_production:
            # Mock mode
            for hand in self.mock_hands:
                if hand.get('hand_id') == hand_id:
                    logger.debug(f"Found mock hand: {hand_id}")
                    return self._normalize_hand_data(hand)
            logger.warning(f"Hand not found in mock data: {hand_id}")
            return None

        # Production mode
        query = f"""
        SELECT
            hand_id,
            timestamp_start_utc,
            timestamp_end_utc,
            duration_seconds,
            players,
            event_id,
            day,
            table_number
        FROM `{self.project_id}.{config.HAND_TABLE}`
        WHERE hand_id = @hand_id
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hand_id", "STRING", hand_id)
            ]
        )

        try:
            results = list(self.client.query(query, job_config=job_config))

            if not results:
                logger.warning(f"Hand not found: {hand_id}")
                return None

            row = results[0]
            return {
                'hand_id': row.hand_id,
                'timestamp_start_utc': row.timestamp_start_utc,
                'timestamp_end_utc': row.timestamp_end_utc,
                'duration_seconds': row.duration_seconds,
                'players': row.players,
                'event_id': row.event_id,
                'day': row.day,
                'table_number': row.table_number,
            }
        except GoogleAPIError as e:
            logger.error(f"BigQuery error fetching hand: {e}")
            return None

    def _normalize_hand_data(self, hand: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize mock hand data to match production schema"""
        # Convert string timestamps to datetime if needed
        timestamp_start = hand.get('timestamp_start_utc')
        timestamp_end = hand.get('timestamp_end_utc')

        if isinstance(timestamp_start, str):
            timestamp_start = datetime.fromisoformat(timestamp_start.replace('Z', '+00:00'))
        if isinstance(timestamp_end, str):
            timestamp_end = datetime.fromisoformat(timestamp_end.replace('Z', '+00:00'))

        return {
            'hand_id': hand.get('hand_id'),
            'timestamp_start_utc': timestamp_start,
            'timestamp_end_utc': timestamp_end,
            'duration_seconds': hand.get('duration_seconds'),
            'players': hand.get('players', []),
            'event_id': hand.get('event_id'),
            'day': hand.get('day'),
            'table_number': hand.get('table_number'),
        }

    def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve video metadata by video_id

        Args:
            video_id: Video identifier

        Returns:
            Video metadata dict or None if not found
        """
        if not self.is_production:
            # Mock mode
            for video in self.mock_videos:
                if video.get('video_id') == video_id:
                    logger.debug(f"Found mock video: {video_id}")
                    return video
            logger.warning(f"Video not found in mock data: {video_id}")
            return None

        # Production mode
        query = f"""
        SELECT
            video_id,
            gcs_proxy_path,
            duration_seconds,
            resolution,
            fps,
            codec
        FROM `{self.project_id}.{config.VIDEO_TABLE}`
        WHERE video_id = @video_id
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("video_id", "STRING", video_id)
            ]
        )

        try:
            results = list(self.client.query(query, job_config=job_config))

            if not results:
                logger.warning(f"Video not found: {video_id}")
                return None

            row = results[0]
            return {
                'video_id': row.video_id,
                'gcs_proxy_path': row.gcs_proxy_path,
                'duration_seconds': row.duration_seconds,
                'resolution': row.resolution,
                'fps': row.fps,
                'codec': row.codec,
            }
        except GoogleAPIError as e:
            logger.error(f"BigQuery error fetching video: {e}")
            return None

    def insert_validation_result(self, validation_data: Dict[str, Any]) -> bool:
        """
        Insert validation result into BigQuery

        Args:
            validation_data: Validation result dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.is_production:
            # Mock mode: Just log
            logger.info(f"[MOCK] Would insert validation: {validation_data.get('validation_id')}")
            return True

        table_id = f"{self.project_id}.{config.VALIDATION_TABLE}"

        try:
            errors = self.client.insert_rows_json(table_id, [validation_data])

            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                return False

            logger.info(f"Inserted validation result: {validation_data.get('validation_id')}")
            return True
        except GoogleAPIError as e:
            logger.error(f"BigQuery error inserting validation: {e}")
            return False

    def get_validation_stats(self, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get validation statistics

        Args:
            event_id: Optional event filter

        Returns:
            Statistics dictionary
        """
        if not self.is_production:
            # Mock mode: Return dummy stats
            return {
                'total_hands': 100,
                'validated_hands': 75,
                'validation_rate': 0.75,
                'avg_sync_score': 87.5,
                'perfect_sync_count': 45,
                'offset_needed_count': 25,
                'manual_needed_count': 5,
                'score_distribution': {
                    '90-100': 45,
                    '80-90': 25,
                    '60-80': 5,
                    '<60': 0
                },
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }

        # Production mode
        where_clause = ""
        if event_id:
            where_clause = "WHERE event_id = @event_id"

        query = f"""
        SELECT
            COUNT(*) as total_validations,
            AVG(sync_score) as avg_sync_score,
            COUNTIF(sync_score >= 90) as perfect_sync_count,
            COUNTIF(sync_score >= 80 AND sync_score < 90) as good_sync_count,
            COUNTIF(sync_score >= 60 AND sync_score < 80) as offset_needed_count,
            COUNTIF(sync_score < 60) as manual_needed_count
        FROM `{self.project_id}.{config.VALIDATION_TABLE}`
        {where_clause}
        """

        job_config = bigquery.QueryJobConfig()
        if event_id:
            job_config.query_parameters = [
                bigquery.ScalarQueryParameter("event_id", "STRING", event_id)
            ]

        try:
            results = list(self.client.query(query, job_config=job_config))
            row = results[0]

            return {
                'total_hands': row.total_validations,
                'validated_hands': row.total_validations,
                'validation_rate': 1.0,  # All queried are validated
                'avg_sync_score': float(row.avg_sync_score) if row.avg_sync_score else 0.0,
                'perfect_sync_count': row.perfect_sync_count,
                'offset_needed_count': row.offset_needed_count,
                'manual_needed_count': row.manual_needed_count,
                'score_distribution': {
                    '90-100': row.perfect_sync_count,
                    '80-90': row.good_sync_count,
                    '60-80': row.offset_needed_count,
                    '<60': row.manual_needed_count
                },
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }
        except GoogleAPIError as e:
            logger.error(f"BigQuery error fetching stats: {e}")
            return {}
