"""
BigQuery client for video metadata storage
"""
import logging
from typing import List, Dict, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .config import config

logger = logging.getLogger(__name__)


class BigQueryClient:
    """BigQuery client for video_files table"""

    def __init__(self):
        self.client = bigquery.Client(project=config.PROJECT_ID)
        self.table_id = config.bigquery_table_id

    def ensure_table_exists(self) -> None:
        """
        Create video_files table if it doesn't exist
        """
        schema = [
            bigquery.SchemaField("video_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("tournament_day", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("table_number", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("nas_file_path", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("file_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("gcs_proxy_path", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("duration_seconds", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("resolution", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("codec", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("bitrate_kbps", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("fps", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("file_size_bytes", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("proxy_size_bytes", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("scanned_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("indexed_at", "TIMESTAMP", mode="NULLABLE"),
        ]

        try:
            table = self.client.get_table(self.table_id)
            logger.info(f"Table {self.table_id} already exists")
        except NotFound:
            logger.info(f"Creating table {self.table_id}")
            table = bigquery.Table(self.table_id, schema=schema)
            table = self.client.create_table(table)
            logger.info(f"Created table {self.table_id}")

    def insert_video_metadata(self, videos: List[Dict]) -> None:
        """
        Insert video metadata into BigQuery

        Args:
            videos: List of video metadata dictionaries

        Raises:
            RuntimeError: If insert fails
        """
        if not videos:
            logger.warning("No videos to insert")
            return

        logger.info(f"Inserting {len(videos)} videos into BigQuery")

        try:
            errors = self.client.insert_rows_json(self.table_id, videos)

            if errors:
                error_msg = f"BigQuery insert errors: {errors}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info(f"Successfully inserted {len(videos)} videos")

        except Exception as e:
            error_msg = f"BigQuery insert failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def upsert_video_metadata(self, video: Dict) -> None:
        """
        Insert or update video metadata

        Args:
            video: Video metadata dictionary
        """
        video_id = video.get('video_id')
        if not video_id:
            raise ValueError("video_id is required")

        logger.info(f"Upserting video {video_id}")

        # Use MERGE statement for upsert
        merge_query = f"""
        MERGE `{self.table_id}` T
        USING (SELECT @video_id AS video_id) S
        ON T.video_id = S.video_id
        WHEN MATCHED THEN
            UPDATE SET
                event_id = @event_id,
                tournament_day = @tournament_day,
                table_number = @table_number,
                nas_file_path = @nas_file_path,
                file_name = @file_name,
                gcs_proxy_path = @gcs_proxy_path,
                duration_seconds = @duration_seconds,
                resolution = @resolution,
                codec = @codec,
                bitrate_kbps = @bitrate_kbps,
                fps = @fps,
                file_size_bytes = @file_size_bytes,
                proxy_size_bytes = @proxy_size_bytes,
                scanned_at = @scanned_at
        WHEN NOT MATCHED THEN
            INSERT (
                video_id, event_id, tournament_day, table_number,
                nas_file_path, file_name, gcs_proxy_path,
                duration_seconds, resolution, codec, bitrate_kbps, fps,
                file_size_bytes, proxy_size_bytes, created_at, scanned_at, indexed_at
            )
            VALUES (
                @video_id, @event_id, @tournament_day, @table_number,
                @nas_file_path, @file_name, @gcs_proxy_path,
                @duration_seconds, @resolution, @codec, @bitrate_kbps, @fps,
                @file_size_bytes, @proxy_size_bytes, @created_at, @scanned_at, CURRENT_TIMESTAMP()
            )
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("video_id", "STRING", video.get("video_id")),
                bigquery.ScalarQueryParameter("event_id", "STRING", video.get("event_id")),
                bigquery.ScalarQueryParameter("tournament_day", "INT64", video.get("tournament_day")),
                bigquery.ScalarQueryParameter("table_number", "INT64", video.get("table_number")),
                bigquery.ScalarQueryParameter("nas_file_path", "STRING", video.get("nas_file_path")),
                bigquery.ScalarQueryParameter("file_name", "STRING", video.get("file_name")),
                bigquery.ScalarQueryParameter("gcs_proxy_path", "STRING", video.get("gcs_proxy_path")),
                bigquery.ScalarQueryParameter("duration_seconds", "INT64", video.get("duration_seconds")),
                bigquery.ScalarQueryParameter("resolution", "STRING", video.get("resolution")),
                bigquery.ScalarQueryParameter("codec", "STRING", video.get("codec")),
                bigquery.ScalarQueryParameter("bitrate_kbps", "INT64", video.get("bitrate_kbps")),
                bigquery.ScalarQueryParameter("fps", "FLOAT64", video.get("fps")),
                bigquery.ScalarQueryParameter("file_size_bytes", "INT64", video.get("file_size_bytes")),
                bigquery.ScalarQueryParameter("proxy_size_bytes", "INT64", video.get("proxy_size_bytes")),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", video.get("created_at")),
                bigquery.ScalarQueryParameter("scanned_at", "TIMESTAMP", video.get("scanned_at")),
            ]
        )

        try:
            query_job = self.client.query(merge_query, job_config=job_config)
            query_job.result()  # Wait for completion
            logger.info(f"Upserted video {video_id}")
        except Exception as e:
            error_msg = f"Upsert failed for {video_id}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """
        Get video metadata by ID

        Args:
            video_id: Video ID

        Returns:
            Video metadata dict or None if not found
        """
        query = f"""
        SELECT *
        FROM `{self.table_id}`
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
            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Query failed for video_id {video_id}: {e}")
            return None

    def list_videos(
        self,
        event_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List videos with optional filtering

        Args:
            event_id: Filter by event ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of video metadata dictionaries
        """
        where_clause = ""
        params = []

        if event_id:
            where_clause = "WHERE event_id = @event_id"
            params.append(bigquery.ScalarQueryParameter("event_id", "STRING", event_id))

        query = f"""
        SELECT *
        FROM `{self.table_id}`
        {where_clause}
        ORDER BY indexed_at DESC
        LIMIT @limit OFFSET @offset
        """

        params.extend([
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("offset", "INT64", offset)
        ])

        job_config = bigquery.QueryJobConfig(query_parameters=params)

        try:
            results = list(self.client.query(query, job_config=job_config))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"List videos query failed: {e}")
            return []

    def get_stats(self, period: str = "24h") -> Dict:
        """
        Get scanning statistics

        Args:
            period: Time period ('24h', '7d', '30d', 'all')

        Returns:
            Statistics dictionary
        """
        # Map period to SQL interval
        interval_map = {
            '24h': 'INTERVAL 1 DAY',
            '7d': 'INTERVAL 7 DAY',
            '30d': 'INTERVAL 30 DAY',
            'all': 'INTERVAL 1000000 DAY'  # Effectively all time
        }
        interval = interval_map.get(period, 'INTERVAL 1 DAY')

        query = f"""
        SELECT
            COUNT(*) as total_files_scanned,
            SUM(file_size_bytes) as total_storage_bytes,
            COUNT(CASE WHEN gcs_proxy_path IS NOT NULL THEN 1 END) as proxies_generated,
            AVG(duration_seconds) as avg_duration_seconds,
            MAX(scanned_at) as last_scan_at
        FROM `{self.table_id}`
        WHERE scanned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), {interval})
        """

        try:
            results = list(self.client.query(query))
            if results:
                row = dict(results[0])
                return {
                    'period': period,
                    'total_files_scanned': row.get('total_files_scanned', 0),
                    'total_storage_bytes': row.get('total_storage_bytes', 0),
                    'proxies_generated': row.get('proxies_generated', 0),
                    'avg_duration_seconds': round(row.get('avg_duration_seconds', 0), 2),
                    'last_scan_at': row.get('last_scan_at'),
                }
            return {}
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            return {}
