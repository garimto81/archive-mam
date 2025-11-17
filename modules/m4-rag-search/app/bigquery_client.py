"""
BigQuery client with mock/real data switching

Development mode: Load data from JSON files
Production mode: Query real BigQuery tables
"""
import json
import logging
import os
from typing import List, Dict, Any, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class BigQueryClient:
    """BigQuery client with environment-aware data loading"""

    def __init__(self):
        self.config = config
        self.client = None if config.is_development() else self._init_client()
        self._mock_hands = None
        self._mock_embeddings = None

        if config.is_development():
            self._load_mock_data()

    def _init_client(self) -> bigquery.Client:
        """Initialize BigQuery client for production"""
        return bigquery.Client(project=config.GCP_PROJECT)

    def _load_mock_data(self):
        """Load mock data from JSON files"""
        try:
            # Load hand summary data
            hands_path = config.get_mock_data_path('hands')
            logger.info(f"Loading mock hand data from {hands_path}")

            with open(hands_path, 'r', encoding='utf-8') as f:
                self._mock_hands = json.load(f)

            # Load embedding data
            embeddings_path = config.get_mock_data_path('embeddings')
            logger.info(f"Loading mock embedding data from {embeddings_path}")

            with open(embeddings_path, 'r', encoding='utf-8') as f:
                self._mock_embeddings = json.load(f)

            logger.info(
                f"Loaded {len(self._mock_hands)} hands and "
                f"{len(self._mock_embeddings)} embeddings"
            )

        except FileNotFoundError as e:
            logger.error(f"Mock data file not found: {e}")
            self._mock_hands = []
            self._mock_embeddings = []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mock data JSON: {e}")
            self._mock_hands = []
            self._mock_embeddings = []

    def search_hands(
        self,
        query_embedding: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search hands using vector similarity or text matching

        Args:
            query_embedding: Query embedding vector (production)
            query_text: Query text (development fallback)
            top_k: Number of results to return
            filters: Optional filters (players, event_name, year_range, pot_size)

        Returns:
            List of search results with metadata
        """
        if config.is_development():
            return self._search_hands_mock(query_text, top_k, filters)
        else:
            return self._search_hands_real(query_embedding, top_k, filters)

    def _search_hands_mock(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Mock search using simple text matching

        Simulates vector search by:
        1. Simple text matching in summary
        2. Random relevance scores (0.6-0.9)
        3. Return top_k results
        """
        if not self._mock_hands or not self._mock_embeddings:
            logger.warning("Mock data not loaded")
            return []

        # Create embedding lookup
        embeddings_by_hand_id = {
            emb['hand_id']: emb for emb in self._mock_embeddings
        }

        results = []
        query_lower = query_text.lower()

        for hand in self._mock_hands:
            hand_id = hand.get('hand_id')

            # Check if embedding exists
            if hand_id not in embeddings_by_hand_id:
                continue

            # Simple text matching (simulate semantic search)
            # Check tournament_id, players, winner
            match_score = 0.0

            # Check tournament name
            tournament_id = hand.get('tournament_id', '').lower()
            if any(term in tournament_id for term in query_lower.split()):
                match_score += 0.3

            # Check players
            players = hand.get('players', [])
            player_names = [p.get('name', '').lower() for p in players]
            if any(query_lower in name for name in player_names):
                match_score += 0.4

            # Check winner
            winner = hand.get('winner', '').lower()
            if query_lower in winner:
                match_score += 0.3

            # Apply filters
            if filters:
                if not self._apply_filters_mock(hand, filters):
                    continue

            # If any match, add with simulated relevance score
            if match_score > 0:
                results.append({
                    'hand_id': hand_id,
                    'relevance_score': min(match_score, 0.95),
                    'tournament_id': hand.get('tournament_id'),
                    'table_number': hand.get('table_number'),
                    'hand_number': hand.get('hand_number'),
                    'pot_size': hand.get('pot_size'),
                    'winner': hand.get('winner'),
                    'timestamp': hand.get('timestamp'),
                    'players': [p.get('name') for p in players]
                })

        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return results[:top_k]

    def _apply_filters_mock(
        self,
        hand: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """Apply filters to mock hand data"""
        # Filter by players
        if 'players' in filters:
            player_names = [p.get('name') for p in hand.get('players', [])]
            if not any(name in player_names for name in filters['players']):
                return False

        # Filter by event name
        if 'event_name_contains' in filters:
            tournament_id = hand.get('tournament_id', '').lower()
            if filters['event_name_contains'].lower() not in tournament_id:
                return False

        # Filter by pot size
        if 'pot_size_min' in filters:
            if hand.get('pot_size', 0) < filters['pot_size_min']:
                return False

        if 'pot_size_max' in filters:
            if hand.get('pot_size', 0) > filters['pot_size_max']:
                return False

        return True

    def _search_hands_real(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Real vector search using BigQuery

        Uses cosine similarity:
        similarity = SUM(a*b) / (SQRT(SUM(a²)) * SQRT(SUM(b²)))
        """
        # Build filter conditions
        filter_conditions = []
        query_params = [
            bigquery.ArrayQueryParameter('query_embedding', 'FLOAT64', query_embedding)
        ]

        if filters:
            if 'players' in filters and filters['players']:
                # Convert array to STRING for LIKE matching
                filter_conditions.append(
                    "EXISTS (SELECT 1 FROM UNNEST(players) AS p WHERE p IN UNNEST(@player_filter))"
                )
                query_params.append(
                    bigquery.ArrayQueryParameter('player_filter', 'STRING', filters['players'])
                )

            if 'event_name_contains' in filters:
                filter_conditions.append("LOWER(event_name) LIKE @event_filter")
                query_params.append(
                    bigquery.ScalarQueryParameter(
                        'event_filter',
                        'STRING',
                        f"%{filters['event_name_contains'].lower()}%"
                    )
                )

            if 'pot_size_min' in filters:
                filter_conditions.append("pot_size_usd >= @pot_min")
                query_params.append(
                    bigquery.ScalarQueryParameter(
                        'pot_min', 'FLOAT64', filters['pot_size_min']
                    )
                )

            if 'pot_size_max' in filters:
                filter_conditions.append("pot_size_usd <= @pot_max")
                query_params.append(
                    bigquery.ScalarQueryParameter(
                        'pot_max', 'FLOAT64', filters['pot_size_max']
                    )
                )

        where_clause = f"WHERE {' AND '.join(filter_conditions)}" if filter_conditions else ""

        # Vector similarity query
        query = f"""
        WITH similarities AS (
            SELECT
                e.hand_id,
                e.summary_text,
                (
                    SELECT SUM(a * b)
                    FROM UNNEST(e.embedding) AS a WITH OFFSET pos_a
                    JOIN UNNEST(@query_embedding) AS b WITH OFFSET pos_b
                    ON pos_a = pos_b
                ) AS relevance_score,
                h.event_name,
                h.timestamp_start,
                h.timestamp_end,
                h.nas_path,
                h.timecode_offset,
                h.proxy_url,
                h.players,
                h.pot_size_usd
            FROM `{config.GCP_PROJECT}.{config.BQ_EMBEDDING_TABLE}` e
            JOIN `{config.GCP_PROJECT}.{config.BQ_HAND_TABLE}` h
            ON e.hand_id = h.hand_id
            {where_clause}
        )
        SELECT *
        FROM similarities
        WHERE relevance_score IS NOT NULL
        ORDER BY relevance_score DESC
        LIMIT {top_k}
        """

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)

        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"BigQuery search failed: {e}", exc_info=True)
            return []

    def log_search(
        self,
        query_id: str,
        query_text: str,
        user_id: Optional[str],
        results_count: int,
        processing_time_ms: int
    ):
        """Log search query for analytics"""
        if config.is_development():
            logger.info(
                f"[MOCK] Search logged: {query_id} | "
                f"query='{query_text}' | results={results_count} | "
                f"time={processing_time_ms}ms"
            )
            return

        # Real BigQuery insert
        table_ref = f"{config.GCP_PROJECT}.{config.BQ_SEARCH_LOG_TABLE}"

        row = {
            'query_id': query_id,
            'query_text': query_text,
            'user_id': user_id,
            'results_count': results_count,
            'processing_time_ms': processing_time_ms,
            'timestamp': bigquery.ScalarQueryParameter(
                'timestamp', 'TIMESTAMP', None
            )
        }

        try:
            errors = self.client.insert_rows_json(table_ref, [row])
            if errors:
                logger.error(f"Failed to log search: {errors}")
        except Exception as e:
            logger.error(f"Failed to log search: {e}", exc_info=True)

    def save_feedback(
        self,
        query_id: str,
        hand_id: str,
        user_id: Optional[str],
        feedback: str
    ):
        """Save user feedback"""
        if config.is_development():
            logger.info(
                f"[MOCK] Feedback saved: {query_id} | "
                f"hand={hand_id} | feedback={feedback}"
            )
            return

        # Real BigQuery insert
        table_ref = f"{config.GCP_PROJECT}.{config.BQ_FEEDBACK_TABLE}"

        row = {
            'query_id': query_id,
            'hand_id': hand_id,
            'user_id': user_id,
            'feedback': feedback,
            'timestamp': None
        }

        try:
            errors = self.client.insert_rows_json(table_ref, [row])
            if errors:
                logger.error(f"Failed to save feedback: {errors}")
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}", exc_info=True)

    def get_search_stats(self, period: str = '24h') -> Dict[str, Any]:
        """Get search statistics"""
        if config.is_development():
            # Return mock stats
            return {
                'period': period,
                'total_searches': 125,
                'unique_users': 15,
                'avg_processing_time_ms': 280,
                'avg_results_count': 45.3,
                'top_queries': [
                    {'query': 'Tom Dwan', 'count': 12},
                    {'query': 'Phil Ivey', 'count': 8},
                    {'query': 'WSOP 2024', 'count': 6}
                ],
                'zero_result_queries': 3,
                'feedback_rate': 0.23
            }

        # Real stats query (to be implemented in Week 5)
        # Query search_logs and feedback tables
        return {}


# Singleton instance
_bq_client = None


def get_bigquery_client() -> BigQueryClient:
    """Get or create BigQuery client singleton"""
    global _bq_client

    if _bq_client is None:
        _bq_client = BigQueryClient()

    return _bq_client
