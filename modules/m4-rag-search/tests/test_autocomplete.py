"""
Tests for Autocomplete Service
"""
import pytest

from app.autocomplete import AutocompleteService, get_autocomplete_service


class TestAutocompleteService:
    """Tests for AutocompleteService class"""

    def test_get_suggestions_basic(self):
        """Test basic autocomplete suggestions"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("Tom", limit=10)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all('text' in s for s in suggestions)
        assert all('type' in s for s in suggestions)
        assert all('count' in s for s in suggestions)

    def test_get_suggestions_player_match(self):
        """Test player name matching"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("Tom D", limit=10)

        # Should include Tom Dwan
        player_suggestions = [s for s in suggestions if s['type'] == 'player']
        assert any('Tom Dwan' in s['text'] for s in player_suggestions)

    def test_get_suggestions_event_match(self):
        """Test event name matching"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("WSOP", limit=10)

        # Should include WSOP events
        event_suggestions = [s for s in suggestions if s['type'] == 'event']
        assert len(event_suggestions) > 0

    def test_get_suggestions_popular_match(self):
        """Test popular search matching"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("bluff", limit=10)

        # Should include popular searches with "bluff"
        assert len(suggestions) > 0

    def test_get_suggestions_short_query(self):
        """Test autocomplete with too short query"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("a", limit=10)

        # Should return empty list for query < 2 chars
        assert suggestions == []

    def test_get_suggestions_limit(self):
        """Test suggestion limit"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("Tom", limit=3)

        assert len(suggestions) <= 3

    def test_get_suggestions_prefix_priority(self):
        """Test that prefix matches come first"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("Tom", limit=10)

        # First result should start with "Tom"
        if suggestions:
            assert suggestions[0]['text'].lower().startswith('tom')

    def test_get_suggestions_case_insensitive(self):
        """Test case-insensitive matching"""
        service = AutocompleteService()

        suggestions_lower = service.get_suggestions("tom", limit=10)
        suggestions_upper = service.get_suggestions("TOM", limit=10)

        # Should return same results regardless of case
        assert len(suggestions_lower) == len(suggestions_upper)

    def test_suggestion_types(self):
        """Test that suggestions have valid types"""
        service = AutocompleteService()

        suggestions = service.get_suggestions("Tom", limit=10)

        valid_types = ['player', 'event', 'popular', 'recent']

        for suggestion in suggestions:
            assert suggestion['type'] in valid_types

    def test_singleton_pattern(self):
        """Test singleton pattern"""
        service1 = get_autocomplete_service()
        service2 = get_autocomplete_service()

        assert service1 is service2


class TestAutocompleteMockData:
    """Tests for mock autocomplete data"""

    def test_mock_players_exist(self):
        """Test that mock player data exists"""
        service = AutocompleteService()

        assert len(service._mock_players) > 0
        assert 'Tom Dwan' in service._mock_players
        assert 'Phil Ivey' in service._mock_players

    def test_mock_events_exist(self):
        """Test that mock event data exists"""
        service = AutocompleteService()

        assert len(service._mock_events) > 0
        assert any('WSOP' in event for event in service._mock_events)

    def test_mock_popular_exist(self):
        """Test that mock popular searches exist"""
        service = AutocompleteService()

        assert len(service._mock_popular) > 0
        assert any('bluff' in search.lower() for search in service._mock_popular)
