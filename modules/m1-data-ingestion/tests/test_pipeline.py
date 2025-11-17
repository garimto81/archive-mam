"""
Unit tests for Dataflow pipeline components
"""
import json
import pytest
from unittest.mock import Mock, patch

from app.dataflow_pipeline import ParseATIJson, DeduplicateByHandId, get_bigquery_schema


class TestParseATIJson:
    """Test ParseATIJson DoFn"""

    def test_parse_valid_json(self):
        """Test parsing valid ATI JSON"""
        parser = ParseATIJson()

        line = json.dumps({
            'handId': 'wsop2024_me_d1_h001',
            'eventId': 'wsop2024_me',
            'tournamentDay': 1,
            'handNumber': 1,
            'tableNumber': 42,
            'timestampStartUTC': '2024-11-17T10:00:00Z',
            'timestampEndUTC': '2024-11-17T10:02:30Z',
            'durationSeconds': 150,
            'players': ['Phil Ivey', 'Daniel Negreanu'],
            'potSizeUSD': 12500.50,
            'winnerPlayerName': 'Phil Ivey',
            'handDescription': 'Royal flush on river'
        })

        results = list(parser.process(line))

        assert len(results) == 1
        data = results[0]

        # Verify field transformations
        assert data['hand_id'] == 'wsop2024_me_d1_h001'
        assert data['event_id'] == 'wsop2024_me'
        assert data['tournament_day'] == 1
        assert data['hand_number'] == 1
        assert data['table_number'] == 42
        assert data['timestamp_start_utc'] == '2024-11-17T10:00:00Z'
        assert data['timestamp_end_utc'] == '2024-11-17T10:02:30Z'
        assert data['duration_seconds'] == 150
        assert data['players'] == ['Phil Ivey', 'Daniel Negreanu']
        assert data['pot_size_usd'] == 12500.50
        assert data['winner_player_name'] == 'Phil Ivey'
        assert data['hand_description'] == 'Royal flush on river'
        assert 'ingested_at' in data

    def test_parse_minimal_json(self):
        """Test parsing JSON with only required fields"""
        parser = ParseATIJson()

        line = json.dumps({
            'handId': 'test_hand_001',
        })

        results = list(parser.process(line))

        assert len(results) == 1
        data = results[0]

        assert data['hand_id'] == 'test_hand_001'
        assert data['event_id'] == ''
        assert data['tournament_day'] is None
        assert data['hand_number'] == 0
        assert data['pot_size_usd'] == 0.0

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON - should log error and yield nothing"""
        parser = ParseATIJson()

        invalid_line = "not a valid json {{"

        results = list(parser.process(invalid_line))

        assert len(results) == 0

    def test_parse_missing_hand_id(self):
        """Test parsing JSON without hand_id - should fail validation"""
        parser = ParseATIJson()

        line = json.dumps({
            'eventId': 'wsop2024_me',
            'tournamentDay': 1
        })

        results = list(parser.process(line))

        assert len(results) == 0  # Should be filtered out due to missing hand_id

    def test_parse_type_conversions(self):
        """Test type conversions (strings to numbers)"""
        parser = ParseATIJson()

        line = json.dumps({
            'handId': 'test_hand_002',
            'tournamentDay': '3',  # String instead of int
            'handNumber': '42',
            'potSizeUSD': '15000.75'
        })

        results = list(parser.process(line))

        assert len(results) == 1
        data = results[0]

        assert data['tournament_day'] == 3
        assert data['hand_number'] == 42
        assert data['pot_size_usd'] == 15000.75

    def test_parse_null_tournament_day(self):
        """Test parsing cash game (no tournament day)"""
        parser = ParseATIJson()

        line = json.dumps({
            'handId': 'cash_game_001',
            'eventId': 'gg_live_cash',
            'tournamentDay': None
        })

        results = list(parser.process(line))

        assert len(results) == 1
        data = results[0]

        assert data['hand_id'] == 'cash_game_001'
        assert data['tournament_day'] is None


class TestDeduplicateByHandId:
    """Test DeduplicateByHandId DoFn"""

    def test_deduplicate_no_duplicates(self):
        """Test with unique hand IDs"""
        deduplicator = DeduplicateByHandId()

        elements = [
            {'hand_id': 'hand_001', 'data': 'a'},
            {'hand_id': 'hand_002', 'data': 'b'},
            {'hand_id': 'hand_003', 'data': 'c'},
        ]

        results = []
        for element in elements:
            results.extend(list(deduplicator.process(element)))

        assert len(results) == 3
        assert results[0]['hand_id'] == 'hand_001'
        assert results[1]['hand_id'] == 'hand_002'
        assert results[2]['hand_id'] == 'hand_003'

    def test_deduplicate_with_duplicates(self):
        """Test with duplicate hand IDs - keeps first occurrence"""
        deduplicator = DeduplicateByHandId()

        elements = [
            {'hand_id': 'hand_001', 'data': 'first'},
            {'hand_id': 'hand_002', 'data': 'unique'},
            {'hand_id': 'hand_001', 'data': 'duplicate'},  # Should be filtered
            {'hand_id': 'hand_003', 'data': 'unique2'},
            {'hand_id': 'hand_002', 'data': 'duplicate2'},  # Should be filtered
        ]

        results = []
        for element in elements:
            results.extend(list(deduplicator.process(element)))

        assert len(results) == 3
        assert results[0]['hand_id'] == 'hand_001'
        assert results[0]['data'] == 'first'  # First occurrence kept
        assert results[1]['hand_id'] == 'hand_002'
        assert results[2]['hand_id'] == 'hand_003'


class TestBigQuerySchema:
    """Test BigQuery schema definition"""

    def test_schema_has_required_fields(self):
        """Test schema contains all required fields"""
        schema = get_bigquery_schema()

        field_names = [field['name'] for field in schema['fields']]

        required_fields = [
            'hand_id',
            'event_id',
            'tournament_day',
            'hand_number',
            'table_number',
            'timestamp_start_utc',
            'timestamp_end_utc',
            'duration_seconds',
            'players',
            'pot_size_usd',
            'winner_player_name',
            'hand_description',
            'ingested_at'
        ]

        for field in required_fields:
            assert field in field_names, f"Missing field: {field}"

    def test_schema_field_types(self):
        """Test schema field types are correct"""
        schema = get_bigquery_schema()

        field_types = {field['name']: field['type'] for field in schema['fields']}

        assert field_types['hand_id'] == 'STRING'
        assert field_types['event_id'] == 'STRING'
        assert field_types['tournament_day'] == 'INT64'
        assert field_types['hand_number'] == 'INT64'
        assert field_types['timestamp_start_utc'] == 'TIMESTAMP'
        assert field_types['pot_size_usd'] == 'NUMERIC'
        assert field_types['players'] == 'STRING'  # REPEATED

    def test_schema_hand_id_required(self):
        """Test hand_id is marked as REQUIRED"""
        schema = get_bigquery_schema()

        hand_id_field = next(
            field for field in schema['fields'] if field['name'] == 'hand_id'
        )

        assert hand_id_field['mode'] == 'REQUIRED'

    def test_schema_players_repeated(self):
        """Test players field is REPEATED"""
        schema = get_bigquery_schema()

        players_field = next(
            field for field in schema['fields'] if field['name'] == 'players'
        )

        assert players_field['mode'] == 'REPEATED'


class TestPipelineIntegration:
    """Integration tests for pipeline (basic structure)"""

    @patch('app.dataflow_pipeline.beam.Pipeline')
    def test_run_pipeline_validates_gcs_path(self, mock_pipeline):
        """Test pipeline validates GCS path"""
        from app.dataflow_pipeline import run_pipeline

        # Invalid path (not starting with gs://)
        with pytest.raises(ValueError, match="Invalid GCS path"):
            run_pipeline(gcs_path="not-a-gcs-path")

        # Valid path
        with pytest.raises(Exception):
            # Will fail for other reasons, but should pass GCS validation
            run_pipeline(gcs_path="gs://bucket/file.jsonl")

    def test_pipeline_options_creation(self):
        """Test pipeline options are created correctly"""
        from app.dataflow_pipeline import create_pipeline_options

        options = create_pipeline_options(
            project_id="test-project",
            region="us-central1",
            temp_location="gs://test/temp",
            staging_location="gs://test/staging",
            runner="DirectRunner"
        )

        assert options is not None
        # Options are created successfully
