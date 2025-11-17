"""
BigQuery Client for M1 Data Ingestion Service
Handles statistics queries and data validation
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from google.cloud import bigquery
from google.api_core import exceptions

from .config import Config


logger = logging.getLogger(__name__)


class BigQueryClient:
    """BigQuery client for hand_summary table operations"""

    def __init__(self, project_id: str = None, dataset: str = None, table: str = None):
        """
        Initialize BigQuery client

        Args:
            project_id: GCP project ID
            dataset: BigQuery dataset name
            table: BigQuery table name
        """
        self.config = Config()
        self.project_id = project_id or self.config.PROJECT_ID
        self.dataset = dataset or self.config.DATASET
        self.table = table or self.config.TABLE

        self.client = bigquery.Client(project=self.project_id)
        self.table_ref = f"{self.project_id}.{self.dataset}.{self.table}"

        logger.info(f"BigQuery client initialized: {self.table_ref}")

    def get_stats(self, period: str = "24h", event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ingestion statistics from hand_summary table

        Args:
            period: Time period (24h, 7d, 30d, all)
            event_id: Filter by specific event_id (optional)

        Returns:
            Statistics dictionary with total_hands, total_events, etc.
        """
        try:
            # Build WHERE clause based on period
            where_clause = self._build_where_clause(period, event_id)

            query = f"""
            SELECT
                COUNT(*) as total_hands,
                COUNT(DISTINCT event_id) as total_events,
                MAX(ingested_at) as last_ingestion_timestamp,
                MIN(ingested_at) as first_ingestion_timestamp,
                COUNTIF(winner_player_name IS NOT NULL) as hands_with_winner,
                AVG(pot_size_usd) as avg_pot_size,
                SUM(pot_size_usd) as total_pot_value
            FROM `{self.table_ref}`
            {where_clause}
            """

            logger.debug(f"Executing stats query: {query}")

            query_job = self.client.query(query)
            results = list(query_job.result())

            if not results:
                return self._empty_stats()

            row = results[0]

            stats = {
                'period': period,
                'total_hands': row.total_hands or 0,
                'total_events': row.total_events or 0,
                'last_ingestion_timestamp': row.last_ingestion_timestamp.isoformat() if row.last_ingestion_timestamp else None,
                'first_ingestion_timestamp': row.first_ingestion_timestamp.isoformat() if row.first_ingestion_timestamp else None,
                'hands_with_winner': row.hands_with_winner or 0,
                'avg_pot_size_usd': float(row.avg_pot_size) if row.avg_pot_size else 0.0,
                'total_pot_value_usd': float(row.total_pot_value) if row.total_pot_value else 0.0,
            }

            # Add top events if not filtered by event_id
            if not event_id:
                stats['top_events'] = self._get_top_events(period, limit=10)

            logger.info(f"Stats retrieved: {stats['total_hands']} hands, {stats['total_events']} events")

            return stats

        except exceptions.GoogleAPIError as e:
            logger.error(f"BigQuery API error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get statistics: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting stats: {e}", exc_info=True)
            raise

    def _build_where_clause(self, period: str, event_id: Optional[str] = None) -> str:
        """Build WHERE clause based on period and filters"""
        conditions = []

        # Time-based filter
        if period == "24h":
            conditions.append("ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)")
        elif period == "7d":
            conditions.append("ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)")
        elif period == "30d":
            conditions.append("ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)")
        # "all" has no time filter

        # Event filter
        if event_id:
            conditions.append(f"event_id = '{event_id}'")

        if conditions:
            return "WHERE " + " AND ".join(conditions)
        return ""

    def _get_top_events(self, period: str, limit: int = 10) -> list:
        """Get top events by hand count"""
        try:
            where_clause = self._build_where_clause(period)

            query = f"""
            SELECT
                event_id,
                COUNT(*) as rows_processed
            FROM `{self.table_ref}`
            {where_clause}
            GROUP BY event_id
            ORDER BY rows_processed DESC
            LIMIT {limit}
            """

            query_job = self.client.query(query)
            results = query_job.result()

            return [
                {
                    'event_id': row.event_id,
                    'rows_processed': row.rows_processed
                }
                for row in results
            ]

        except Exception as e:
            logger.warning(f"Failed to get top events: {e}")
            return []

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics"""
        return {
            'period': '24h',
            'total_hands': 0,
            'total_events': 0,
            'last_ingestion_timestamp': None,
            'first_ingestion_timestamp': None,
            'hands_with_winner': 0,
            'avg_pot_size_usd': 0.0,
            'total_pot_value_usd': 0.0,
            'top_events': []
        }

    def check_hand_exists(self, hand_id: str) -> bool:
        """
        Check if a hand_id already exists in the table

        Args:
            hand_id: Hand ID to check

        Returns:
            True if hand exists, False otherwise
        """
        try:
            query = """
            SELECT COUNT(*) as cnt
            FROM `{table}`
            WHERE hand_id = @hand_id
            LIMIT 1
            """.format(table=self.table_ref)

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("hand_id", "STRING", hand_id)
                ]
            )

            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            exists = results[0].cnt > 0
            logger.debug(f"Hand {hand_id} exists: {exists}")

            return exists

        except Exception as e:
            logger.error(f"Error checking hand existence: {e}", exc_info=True)
            return False

    def get_table_info(self) -> Dict[str, Any]:
        """
        Get table metadata and information

        Returns:
            Table information dict
        """
        try:
            table = self.client.get_table(self.table_ref)

            return {
                'table_id': table.table_id,
                'dataset_id': table.dataset_id,
                'project_id': table.project,
                'created': table.created.isoformat() if table.created else None,
                'modified': table.modified.isoformat() if table.modified else None,
                'num_rows': table.num_rows,
                'num_bytes': table.num_bytes,
                'schema_fields': len(table.schema),
            }

        except exceptions.NotFound:
            logger.warning(f"Table not found: {self.table_ref}")
            return None
        except Exception as e:
            logger.error(f"Error getting table info: {e}", exc_info=True)
            return None

    def validate_connection(self) -> bool:
        """
        Validate BigQuery connection

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to get table info
            self.client.get_table(self.table_ref)
            logger.info("BigQuery connection validated successfully")
            return True
        except exceptions.NotFound:
            logger.warning(f"Table not found (will be created on first write): {self.table_ref}")
            return True  # Table will be created by Dataflow
        except Exception as e:
            logger.error(f"BigQuery connection validation failed: {e}", exc_info=True)
            return False


# Global client instance (singleton pattern)
_client_instance: Optional[BigQueryClient] = None


def get_bigquery_client() -> BigQueryClient:
    """Get or create BigQuery client singleton"""
    global _client_instance

    if _client_instance is None:
        _client_instance = BigQueryClient()

    return _client_instance
