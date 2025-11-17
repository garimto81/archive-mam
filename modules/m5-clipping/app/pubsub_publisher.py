"""
Pub/Sub message publishing for M5 Clipping Service.

Handles publishing clipping requests to Pub/Sub topic.
Supports both development (emulator) and production modes.
"""

import json
import logging
import os
from typing import Dict, Any
from google.cloud import pubsub_v1
from google.api_core import exceptions as gcp_exceptions

from app.config import get_config

logger = logging.getLogger(__name__)


class PubSubPublisher:
    """Pub/Sub message publisher for clipping requests."""

    def __init__(self):
        self.config = get_config()
        self._setup_emulator()
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(
            self.config.GCP_PROJECT_ID,
            self.config.CLIPPING_REQUESTS_TOPIC
        )

        logger.info(
            f"PubSubPublisher initialized: topic={self.topic_path}, "
            f"env={self.config.ENV}, emulator={self.config.get_pubsub_emulator_host()}"
        )

    def _setup_emulator(self):
        """Set up Pub/Sub emulator if in development mode."""
        emulator_host = self.config.get_pubsub_emulator_host()
        if emulator_host:
            os.environ['PUBSUB_EMULATOR_HOST'] = emulator_host
            logger.info(f"Using Pub/Sub emulator: {emulator_host}")

    def publish_clipping_request(
        self,
        request_id: str,
        hand_id: str,
        nas_video_path: str,
        start_seconds: float,
        end_seconds: float,
        output_quality: str = 'high'
    ) -> str:
        """
        Publish a clipping request to Pub/Sub.

        Args:
            request_id: Unique request identifier
            hand_id: Hand identifier
            nas_video_path: Path to video file on NAS
            start_seconds: Start time in seconds
            end_seconds: End time in seconds
            output_quality: Output quality (high/medium)

        Returns:
            Message ID from Pub/Sub

        Raises:
            Exception: If publishing fails
        """
        message_data = {
            'request_id': request_id,
            'hand_id': hand_id,
            'nas_video_path': nas_video_path,
            'start_seconds': start_seconds,
            'end_seconds': end_seconds,
            'output_quality': output_quality
        }

        try:
            # Encode message data
            message_bytes = json.dumps(message_data).encode('utf-8')

            # Publish message
            future = self.publisher.publish(
                self.topic_path,
                message_bytes,
                request_id=request_id,  # Add as attribute for filtering
                hand_id=hand_id
            )

            # Wait for publish to complete (with timeout)
            message_id = future.result(timeout=10.0)

            logger.info(
                f"Published clipping request: request_id={request_id}, "
                f"message_id={message_id}, hand_id={hand_id}"
            )

            return message_id

        except gcp_exceptions.NotFound:
            logger.error(f"Topic not found: {self.topic_path}")
            raise Exception(f"Pub/Sub topic not found: {self.config.CLIPPING_REQUESTS_TOPIC}")

        except gcp_exceptions.GoogleAPICallError as e:
            logger.error(f"Pub/Sub publish failed: {e}")
            raise Exception(f"Failed to publish message to Pub/Sub: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error publishing to Pub/Sub: {e}")
            raise

    def publish_completion_message(
        self,
        request_id: str,
        hand_id: str,
        status: str,
        output_gcs_path: str = None,
        error_message: str = None
    ) -> str:
        """
        Publish a clipping completion message.

        Args:
            request_id: Request identifier
            hand_id: Hand identifier
            status: Completion status (completed/failed)
            output_gcs_path: GCS path to clipped video (if successful)
            error_message: Error message (if failed)

        Returns:
            Message ID from Pub/Sub
        """
        completion_topic = self.publisher.topic_path(
            self.config.GCP_PROJECT_ID,
            self.config.CLIPPING_COMPLETE_TOPIC
        )

        message_data = {
            'request_id': request_id,
            'hand_id': hand_id,
            'status': status,
        }

        if output_gcs_path:
            message_data['output_gcs_path'] = output_gcs_path

        if error_message:
            message_data['error_message'] = error_message

        try:
            message_bytes = json.dumps(message_data).encode('utf-8')

            future = self.publisher.publish(
                completion_topic,
                message_bytes,
                request_id=request_id,
                status=status
            )

            message_id = future.result(timeout=10.0)

            logger.info(
                f"Published completion message: request_id={request_id}, "
                f"status={status}, message_id={message_id}"
            )

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish completion message: {e}")
            raise

    def close(self):
        """Close the publisher client."""
        try:
            self.publisher.stop()
            logger.info("PubSubPublisher closed")
        except Exception as e:
            logger.warning(f"Error closing publisher: {e}")


# Global publisher instance
_publisher = None


def get_publisher() -> PubSubPublisher:
    """Get the global publisher instance (singleton)."""
    global _publisher
    if _publisher is None:
        _publisher = PubSubPublisher()
    return _publisher
