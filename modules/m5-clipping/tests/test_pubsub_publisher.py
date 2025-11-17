"""
Tests for Pub/Sub publisher.

Tests message publishing for clipping requests and completion messages.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from google.api_core import exceptions as gcp_exceptions

from app.pubsub_publisher import PubSubPublisher, get_publisher


@pytest.fixture
def mock_publisher_client():
    """Create mock Pub/Sub publisher client."""
    with patch('app.pubsub_publisher.pubsub_v1.PublisherClient') as mock:
        client = Mock()
        mock.return_value = client

        # Mock topic_path method
        client.topic_path.return_value = 'projects/test-project/topics/test-topic'

        # Mock publish method
        future = Mock()
        future.result.return_value = 'message-id-123'
        client.publish.return_value = future

        yield client


class TestPubSubPublisher:
    """Tests for PubSubPublisher class."""

    def test_init_development_mode(self, mock_publisher_client):
        """Test initialization in development mode."""
        with patch.dict('os.environ', {'POKER_ENV': 'development'}):
            publisher = PubSubPublisher()

            assert publisher.config.is_development() is True
            assert 'PUBSUB_EMULATOR_HOST' in os.environ

    def test_init_production_mode(self, mock_publisher_client):
        """Test initialization in production mode."""
        with patch.dict('os.environ', {'POKER_ENV': 'production'}, clear=True):
            publisher = PubSubPublisher()

            assert publisher.config.is_development() is False

    def test_publish_clipping_request_success(self, mock_publisher_client):
        """Test successful publishing of clipping request."""
        publisher = PubSubPublisher()

        message_id = publisher.publish_clipping_request(
            request_id='clip-20241117-001',
            hand_id='wsop2024_me_d3_h154',
            nas_video_path='/nas/poker/test.mp4',
            start_seconds=100.0,
            end_seconds=200.0,
            output_quality='high'
        )

        assert message_id == 'message-id-123'

        # Verify publish was called
        mock_publisher_client.publish.assert_called_once()

        # Check message data
        call_args = mock_publisher_client.publish.call_args
        message_bytes = call_args[0][1]
        import json
        message_data = json.loads(message_bytes.decode('utf-8'))

        assert message_data['request_id'] == 'clip-20241117-001'
        assert message_data['hand_id'] == 'wsop2024_me_d3_h154'
        assert message_data['start_seconds'] == 100.0
        assert message_data['end_seconds'] == 200.0

    def test_publish_clipping_request_with_attributes(self, mock_publisher_client):
        """Test that message attributes are set."""
        publisher = PubSubPublisher()

        publisher.publish_clipping_request(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            nas_video_path='/nas/test.mp4',
            start_seconds=0,
            end_seconds=10
        )

        # Check that attributes were passed
        call_args = mock_publisher_client.publish.call_args
        kwargs = call_args[1]

        assert 'request_id' in kwargs
        assert kwargs['request_id'] == 'clip-20241117-001'
        assert kwargs['hand_id'] == 'test_hand'

    def test_publish_clipping_request_topic_not_found(self, mock_publisher_client):
        """Test handling of topic not found error."""
        # Mock topic not found error
        future = Mock()
        future.result.side_effect = gcp_exceptions.NotFound("Topic not found")
        mock_publisher_client.publish.return_value = future

        publisher = PubSubPublisher()

        with pytest.raises(Exception) as exc_info:
            publisher.publish_clipping_request(
                request_id='clip-20241117-001',
                hand_id='test_hand',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

        assert 'Topic not found' in str(exc_info.value)

    def test_publish_clipping_request_timeout(self, mock_publisher_client):
        """Test handling of publish timeout."""
        import concurrent.futures

        future = Mock()
        future.result.side_effect = concurrent.futures.TimeoutError()
        mock_publisher_client.publish.return_value = future

        publisher = PubSubPublisher()

        with pytest.raises(Exception):
            publisher.publish_clipping_request(
                request_id='clip-20241117-001',
                hand_id='test_hand',
                nas_video_path='/nas/test.mp4',
                start_seconds=0,
                end_seconds=10
            )

    def test_publish_completion_message_success(self, mock_publisher_client):
        """Test successful publishing of completion message."""
        publisher = PubSubPublisher()

        message_id = publisher.publish_completion_message(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            status='completed',
            output_gcs_path='gs://bucket/test.mp4'
        )

        assert message_id == 'message-id-123'

        # Verify publish was called
        assert mock_publisher_client.publish.call_count >= 1

        # Check message data
        call_args = mock_publisher_client.publish.call_args
        message_bytes = call_args[0][1]
        import json
        message_data = json.loads(message_bytes.decode('utf-8'))

        assert message_data['request_id'] == 'clip-20241117-001'
        assert message_data['status'] == 'completed'
        assert message_data['output_gcs_path'] == 'gs://bucket/test.mp4'

    def test_publish_completion_message_failed(self, mock_publisher_client):
        """Test publishing completion message for failed clip."""
        publisher = PubSubPublisher()

        message_id = publisher.publish_completion_message(
            request_id='clip-20241117-001',
            hand_id='test_hand',
            status='failed',
            error_message='FFmpeg error: invalid codec'
        )

        assert message_id == 'message-id-123'

        # Check message data
        call_args = mock_publisher_client.publish.call_args
        message_bytes = call_args[0][1]
        import json
        message_data = json.loads(message_bytes.decode('utf-8'))

        assert message_data['status'] == 'failed'
        assert 'error_message' in message_data
        assert message_data['error_message'] == 'FFmpeg error: invalid codec'

    def test_close(self, mock_publisher_client):
        """Test closing the publisher."""
        publisher = PubSubPublisher()
        publisher.close()

        mock_publisher_client.stop.assert_called_once()


class TestGetPublisher:
    """Tests for get_publisher singleton."""

    def test_get_publisher_singleton(self, mock_publisher_client):
        """Test that get_publisher returns singleton."""
        # Clear singleton
        import app.pubsub_publisher
        app.pubsub_publisher._publisher = None

        publisher1 = get_publisher()
        publisher2 = get_publisher()

        assert publisher1 is publisher2


import os
