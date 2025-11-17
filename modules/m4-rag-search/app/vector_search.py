"""
Vector Search Logic

Coordinates embedding generation and BigQuery vector search
"""
import logging
import time
from typing import List, Dict, Any, Optional

from .config import get_config
from .embedding_service import get_embedding_service
from .bigquery_client import get_bigquery_client

logger = logging.getLogger(__name__)
config = get_config()


class VectorSearch:
    """Vector search coordinator"""

    def __init__(self):
        self.config = config
        self.embedding_service = get_embedding_service()
        self.bq_client = get_bigquery_client()

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search hands using natural language query

        Args:
            query: Natural language search query
            top_k: Number of results to return
            filters: Optional filters (players, event, year, pot_size)

        Returns:
            Search results with metadata and timing info
        """
        start_time = time.time()

        # Validate query
        if len(query) < config.MIN_QUERY_LENGTH:
            raise ValueError(
                f"Query must be at least {config.MIN_QUERY_LENGTH} characters"
            )

        if top_k > config.MAX_TOP_K:
            top_k = config.MAX_TOP_K

        # Generate query embedding
        embedding_start = time.time()

        if config.is_development():
            # Development: Use text directly, skip embedding
            query_embedding = None
        else:
            # Production: Generate embedding
            query_embedding = self.embedding_service.generate_embedding(query)

        embedding_time = (time.time() - embedding_start) * 1000  # ms

        # Search
        search_start = time.time()
        results = self.bq_client.search_hands(
            query_embedding=query_embedding,
            query_text=query,
            top_k=top_k,
            filters=filters
        )
        search_time = (time.time() - search_start) * 1000  # ms

        total_time = (time.time() - start_time) * 1000  # ms

        logger.info(
            f"Search completed: query='{query}' | results={len(results)} | "
            f"embedding_time={embedding_time:.1f}ms | "
            f"search_time={search_time:.1f}ms | "
            f"total_time={total_time:.1f}ms"
        )

        return {
            'results': results,
            'total_results': len(results),
            'processing_time_ms': int(total_time),
            'debug': {
                'embedding_time_ms': int(embedding_time),
                'search_time_ms': int(search_time)
            } if config.DEBUG else None
        }

    def find_similar(
        self,
        hand_id: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar hands to given hand_id

        Args:
            hand_id: Hand ID to find similar hands for
            top_k: Number of similar hands to return

        Returns:
            List of similar hands
        """
        # In development mode, return mock similar hands
        if config.is_development():
            return self._find_similar_mock(hand_id, top_k)

        # Production: Get hand embedding and search
        # This would query the embedding table and use vector search
        # For now, return empty list
        logger.warning(f"find_similar not implemented for production: {hand_id}")
        return []

    def _find_similar_mock(
        self,
        hand_id: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Find similar hands in mock mode"""
        # Return mock similar hands
        # In real implementation, would get hand embedding and search
        mock_results = []

        for i in range(min(top_k, 5)):
            mock_results.append({
                'hand_id': f"HAND_{i:06d}",
                'relevance_score': 0.85 - (i * 0.05),
                'tournament_id': f"WSOP_2024_{i:03d}",
                'pot_size': 50000 - (i * 5000)
            })

        return mock_results


# Singleton instance
_vector_search = None


def get_vector_search() -> VectorSearch:
    """Get or create vector search singleton"""
    global _vector_search

    if _vector_search is None:
        _vector_search = VectorSearch()

    return _vector_search
