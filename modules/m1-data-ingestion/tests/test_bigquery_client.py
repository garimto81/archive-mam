"""
Unit tests for BigQuery client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.bigquery_client import BigQueryClient


@pytest.fixture
def mock_bigquery_client():
    """Mock google.cloud.bigquery.Client"""
    with patch('app.bigquery_client.bigquery.Client') as mock_client:
        yield mock_client


class TestBigQueryClient:
    """Test BigQueryClient class"""

    def test_init_with_defaults(self, mock_bigquery_client):
        """Test initialization with default config"""
        client = BigQueryClient()

        assert client.project_id == 'gg-poker'
        assert client.dataset == 'prod'
        assert client.table == 'hand_summary'
        assert client.table_ref == 'gg-poker.prod.hand_summary'

    def test_init_with_custom_values(self, mock_bigquery_client):
        """Test initialization with custom values"""
        client = BigQueryClient(
            project_id='test-project',
            dataset='test_dataset',
            table='test_table'
        )

        assert client.project_id == 'test-project'
        assert client.dataset == 'test_dataset'
        assert client.table == 'test_table'
        assert client.table_ref == 'test-project.test_dataset.test_table'


class TestGetStats:
    """Test get_stats method"""

    @patch('app.bigquery_client.bigquery.Client')
    def test_get_stats_24h(self, mock_client_class):
        """Test getting stats for 24h period"""
        # Mock query result
        mock_row = Mock()
        mock_row.total_hands = 15000
        mock_row.total_events = 5
        mock_row.last_ingestion_timestamp = datetime(2024, 11, 17, 12, 0, 0)
        mock_row.first_ingestion_timestamp = datetime(2024, 11, 16, 12, 0, 0)
        mock_row.hands_with_winner = 14800
        mock_row.avg_pot_size = 5000.50
        mock_row.total_pot_value = 75007500.0

        mock_client = Mock()
        mock_query_job = Mock()
        mock_query_job.result.return_value = [mock_row]
        mock_client.query.return_value = mock_query_job

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        stats = client.get_stats(period='24h')

        assert stats['period'] == '24h'
        assert stats['total_hands'] == 15000
        assert stats['total_events'] == 5
        assert stats['hands_with_winner'] == 14800
        assert stats['avg_pot_size_usd'] == 5000.50
        assert stats['total_pot_value_usd'] == 75007500.0

    @patch('app.bigquery_client.bigquery.Client')
    def test_get_stats_all_time(self, mock_client_class):
        """Test getting stats for all time"""
        mock_row = Mock()
        mock_row.total_hands = 1000000
        mock_row.total_events = 100
        mock_row.last_ingestion_timestamp = datetime(2024, 11, 17, 12, 0, 0)
        mock_row.first_ingestion_timestamp = datetime(2024, 1, 1, 0, 0, 0)
        mock_row.hands_with_winner = 990000
        mock_row.avg_pot_size = 7500.0
        mock_row.total_pot_value = 7500000000.0

        mock_client = Mock()
        mock_query_job = Mock()
        mock_query_job.result.return_value = [mock_row]
        mock_client.query.return_value = mock_query_job

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        stats = client.get_stats(period='all')

        assert stats['period'] == 'all'
        assert stats['total_hands'] == 1000000
        assert stats['total_events'] == 100

    @patch('app.bigquery_client.bigquery.Client')
    def test_get_stats_empty_table(self, mock_client_class):
        """Test getting stats from empty table"""
        mock_client = Mock()
        mock_query_job = Mock()
        mock_query_job.result.return_value = []
        mock_client.query.return_value = mock_query_job

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        stats = client.get_stats()

        assert stats['total_hands'] == 0
        assert stats['total_events'] == 0
        assert stats['last_ingestion_timestamp'] is None


class TestCheckHandExists:
    """Test check_hand_exists method"""

    @patch('app.bigquery_client.bigquery.Client')
    def test_check_hand_exists_true(self, mock_client_class):
        """Test checking for existing hand"""
        mock_row = Mock()
        mock_row.cnt = 1

        mock_client = Mock()
        mock_query_job = Mock()
        mock_query_job.result.return_value = [mock_row]
        mock_client.query.return_value = mock_query_job

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        exists = client.check_hand_exists('wsop2024_me_d1_h001')

        assert exists is True

    @patch('app.bigquery_client.bigquery.Client')
    def test_check_hand_exists_false(self, mock_client_class):
        """Test checking for non-existent hand"""
        mock_row = Mock()
        mock_row.cnt = 0

        mock_client = Mock()
        mock_query_job = Mock()
        mock_query_job.result.return_value = [mock_row]
        mock_client.query.return_value = mock_query_job

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        exists = client.check_hand_exists('nonexistent_hand')

        assert exists is False


class TestValidateConnection:
    """Test validate_connection method"""

    @patch('app.bigquery_client.bigquery.Client')
    def test_validate_connection_success(self, mock_client_class):
        """Test successful connection validation"""
        mock_client = Mock()
        mock_client.get_table.return_value = Mock()

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        is_valid = client.validate_connection()

        assert is_valid is True

    @patch('app.bigquery_client.bigquery.Client')
    def test_validate_connection_table_not_found(self, mock_client_class):
        """Test validation when table doesn't exist yet"""
        from google.api_core import exceptions

        mock_client = Mock()
        mock_client.get_table.side_effect = exceptions.NotFound('Table not found')

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        is_valid = client.validate_connection()

        # Should return True (table will be created)
        assert is_valid is True

    @patch('app.bigquery_client.bigquery.Client')
    def test_validate_connection_failure(self, mock_client_class):
        """Test validation failure"""
        mock_client = Mock()
        mock_client.get_table.side_effect = Exception('Connection failed')

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        is_valid = client.validate_connection()

        assert is_valid is False


class TestGetTableInfo:
    """Test get_table_info method"""

    @patch('app.bigquery_client.bigquery.Client')
    def test_get_table_info_success(self, mock_client_class):
        """Test getting table info"""
        mock_table = Mock()
        mock_table.table_id = 'hand_summary'
        mock_table.dataset_id = 'prod'
        mock_table.project = 'gg-poker'
        mock_table.created = datetime(2024, 11, 1, 0, 0, 0)
        mock_table.modified = datetime(2024, 11, 17, 12, 0, 0)
        mock_table.num_rows = 15000
        mock_table.num_bytes = 1500000
        mock_table.schema = [Mock(), Mock(), Mock()]  # 3 fields

        mock_client = Mock()
        mock_client.get_table.return_value = mock_table

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        info = client.get_table_info()

        assert info['table_id'] == 'hand_summary'
        assert info['dataset_id'] == 'prod'
        assert info['project_id'] == 'gg-poker'
        assert info['num_rows'] == 15000
        assert info['schema_fields'] == 3

    @patch('app.bigquery_client.bigquery.Client')
    def test_get_table_info_not_found(self, mock_client_class):
        """Test getting info for non-existent table"""
        from google.api_core import exceptions

        mock_client = Mock()
        mock_client.get_table.side_effect = exceptions.NotFound('Table not found')

        mock_client_class.return_value = mock_client

        client = BigQueryClient()
        info = client.get_table_info()

        assert info is None
