"""
Autocomplete Suggestion Service

Provides search query suggestions based on:
- Popular searches
- Player names
- Event names
- User search history
"""
import logging
from typing import List, Dict, Any

from .config import get_config
from .bigquery_client import get_bigquery_client

logger = logging.getLogger(__name__)
config = get_config()


class AutocompleteService:
    """Autocomplete suggestion service"""

    def __init__(self):
        self.config = config
        self.bq_client = get_bigquery_client()

        # Mock data for development
        self._mock_players = [
            "Tom Dwan", "Phil Ivey", "Daniel Negreanu", "Phil Hellmuth",
            "Doyle Brunson", "Erik Seidel", "Antonio Esfandiari",
            "Tony G", "Patrik Antonius", "Gus Hansen"
        ]

        self._mock_events = [
            "WSOP 2024 Main Event", "WSOP 2023 Main Event", "WSOP 2022 Main Event",
            "WPT Championship", "EPT Monte Carlo", "Poker After Dark",
            "High Stakes Poker"
        ]

        self._mock_popular = [
            "Tom Dwan bluff", "Phil Ivey big pot", "WSOP 2024",
            "river all-in", "pocket aces", "bad beat",
            "million dollar pot", "hero call"
        ]

    def get_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions

        Args:
            query: Partial search query
            limit: Maximum number of suggestions

        Returns:
            List of suggestions with type and count
        """
        if len(query) < config.AUTOCOMPLETE_MIN_QUERY_LENGTH:
            return []

        if config.is_development():
            return self._get_suggestions_mock(query, limit)
        else:
            return self._get_suggestions_real(query, limit)

    def _get_suggestions_mock(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get mock autocomplete suggestions"""
        query_lower = query.lower()
        suggestions = []

        # Player name matches
        for player in self._mock_players:
            if query_lower in player.lower():
                suggestions.append({
                    'text': player,
                    'type': 'player',
                    'count': 150  # Mock result count
                })

        # Event name matches
        for event in self._mock_events:
            if query_lower in event.lower():
                suggestions.append({
                    'text': event,
                    'type': 'event',
                    'count': 80
                })

        # Popular search matches
        for popular in self._mock_popular:
            if query_lower in popular.lower():
                suggestions.append({
                    'text': popular,
                    'type': 'popular',
                    'count': 45
                })

        # Sort by relevance (exact prefix match first, then by count)
        suggestions.sort(
            key=lambda x: (
                not x['text'].lower().startswith(query_lower),
                -x['count']
            )
        )

        return suggestions[:limit]

    def _get_suggestions_real(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get real autocomplete suggestions from BigQuery

        Queries:
        1. Player names from hand_summary
        2. Event names from hand_summary
        3. Popular searches from search_logs
        """
        # To be implemented in production
        # Would query BigQuery for:
        # - DISTINCT players WHERE player LIKE '%query%'
        # - DISTINCT event_name WHERE event_name LIKE '%query%'
        # - Top queries from search_logs WHERE query LIKE '%query%'

        logger.warning("Real autocomplete not implemented yet")
        return self._get_suggestions_mock(query, limit)


# Singleton instance
_autocomplete_service = None


def get_autocomplete_service() -> AutocompleteService:
    """Get or create autocomplete service singleton"""
    global _autocomplete_service

    if _autocomplete_service is None:
        _autocomplete_service = AutocompleteService()

    return _autocomplete_service
