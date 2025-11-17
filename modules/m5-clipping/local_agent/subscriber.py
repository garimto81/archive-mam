"""
Pub/Sub subscriber daemon for M5 Clipping Service.

Subscribes to clipping requests, processes videos with FFmpeg,
uploads to GCS, and publishes completion messages.

This is a long-running daemon process managed by systemd in production.
"""

import json
import logging
import os
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from google.cloud import pubsub_v1, storage
from google.api_core import exceptions as gcp_exceptions

from local_agent.config import AgentConfig
from local_agent.ffmpeg_clipper import FFmpegClipper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/clipping-agent.log') if not AgentConfig.is_development() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


class ClippingAgent:
    """Local agent that processes clipping requests."""

    def __init__(self):
        self.config = AgentConfig
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.MAX_CONCURRENT_CLIPS)

        # Setup emulator if development
        self.config.setup_emulator()

        # Initialize clients
        self.subscriber = pubsub_v1.SubscriberClient()
        self.publisher = pubsub_v1.PublisherClient()
        self.storage_client = storage.Client(project=self.config.GCP_PROJECT_ID) if not self.config.is_development() else None

        # Initialize FFmpeg clipper
        self.clipper = FFmpegClipper(is_development=self.config.is_development())

        # Subscription path
        self.subscription_path = self.subscriber.subscription_path(
            self.config.GCP_PROJECT_ID,
            self.config.CLIPPING_REQUESTS_SUBSCRIPTION
        )

        # Completion topic path
        self.completion_topic_path = self.publisher.topic_path(
            self.config.GCP_PROJECT_ID,
            self.config.CLIPPING_COMPLETE_TOPIC
        )

        # Statistics
        self.stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'started_at': datetime.utcnow().isoformat()
        }

        logger.info(
            f"ClippingAgent initialized: agent_id={self.config.AGENT_ID}, "
            f"role={self.config.AGENT_ROLE}, env={self.config.ENV}"
        )

    def start(self):
        """Start the agent and begin processing messages."""
        self.running = True

        logger.info(f"Starting to subscribe: {self.subscription_path}")

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start streaming pull
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self._message_callback
        )

        logger.info("Agent is running. Press Ctrl+C to stop.")

        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop(streaming_pull_future)

    def stop(self, streaming_pull_future=None):
        """Stop the agent gracefully."""
        logger.info("Stopping agent...")
        self.running = False

        if streaming_pull_future:
            streaming_pull_future.cancel()

        # Wait for ongoing tasks to complete
        self.executor.shutdown(wait=True, timeout=60)

        logger.info(
            f"Agent stopped. Stats: processed={self.stats['processed']}, "
            f"succeeded={self.stats['succeeded']}, failed={self.stats['failed']}"
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.running = False

    def _message_callback(self, message: pubsub_v1.subscriber.message.Message):
        """
        Callback for processing Pub/Sub messages.

        Args:
            message: Pub/Sub message containing clipping request
        """
        try:
            # Parse message data
            data = json.loads(message.data.decode('utf-8'))

            request_id = data.get('request_id')
            hand_id = data.get('hand_id')

            logger.info(f"Received clipping request: {request_id}")

            # Submit to thread pool for processing
            future = self.executor.submit(self._process_clipping_request, data)

            # Add callback to acknowledge message after processing
            future.add_done_callback(lambda f: self._handle_completion(f, message))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            message.nack()  # Negative acknowledgment - will be redelivered

        except Exception as e:
            logger.error(f"Error in message callback: {e}")
            message.nack()

    def _handle_completion(self, future, message):
        """Handle completion of clipping task."""
        try:
            # Get result (this will raise exception if task failed)
            result = future.result()

            # Acknowledge message
            message.ack()

            logger.info(f"Clipping task completed: {result.get('request_id')}")

        except Exception as e:
            logger.error(f"Clipping task failed: {e}")
            message.nack()

    def _process_clipping_request(self, data: dict) -> dict:
        """
        Process a clipping request.

        Args:
            data: Clipping request data from Pub/Sub

        Returns:
            Processing result dictionary
        """
        request_id = data['request_id']
        hand_id = data['hand_id']
        nas_video_path = data['nas_video_path']
        start_seconds = data['start_seconds']
        end_seconds = data['end_seconds']
        output_quality = data.get('output_quality', 'high')

        self.stats['processed'] += 1

        logger.info(f"Processing clip: {request_id}")

        try:
            # Generate output path
            temp_dir = self.config.get_temp_clips_dir()
            output_filename = f"{hand_id}.mp4"
            output_path = os.path.join(temp_dir, output_filename)

            # Clip video with FFmpeg
            logger.info(f"Starting FFmpeg clipping: {request_id}")
            start_time = time.time()

            clipped_path, metadata = self.clipper.clip_video(
                input_path=nas_video_path,
                output_path=output_path,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                quality=output_quality
            )

            processing_time = int(time.time() - start_time)

            logger.info(
                f"FFmpeg clipping completed: {request_id}, "
                f"time={processing_time}s, size={metadata['file_size_bytes']}"
            )

            # Upload to GCS
            gcs_path = self._upload_to_gcs(clipped_path, hand_id)

            # Clean up temp file
            try:
                os.remove(clipped_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")

            # Publish completion message
            self._publish_completion(
                request_id=request_id,
                hand_id=hand_id,
                status='completed',
                output_gcs_path=gcs_path,
                file_size_bytes=metadata['file_size_bytes'],
                duration_seconds=metadata.get('duration_seconds'),
                processing_time_seconds=processing_time
            )

            self.stats['succeeded'] += 1

            return {
                'request_id': request_id,
                'status': 'completed',
                'gcs_path': gcs_path
            }

        except Exception as e:
            logger.error(f"Clipping failed for {request_id}: {e}", exc_info=True)

            # Publish failure message
            self._publish_completion(
                request_id=request_id,
                hand_id=hand_id,
                status='failed',
                error_message=str(e)
            )

            self.stats['failed'] += 1

            raise

    def _upload_to_gcs(self, local_path: str, hand_id: str) -> str:
        """
        Upload clipped video to GCS.

        Args:
            local_path: Path to local video file
            hand_id: Hand identifier (used as blob name)

        Returns:
            GCS path (gs://bucket/filename)
        """
        blob_name = f"{hand_id}.mp4"

        if self.config.is_development():
            # Mock: Just return fake GCS path
            mock_gcs_path = f"gs://{self.config.GCS_BUCKET}/{blob_name}"
            logger.info(f"[MOCK] Upload to GCS: {mock_gcs_path}")
            return mock_gcs_path

        try:
            bucket = self.storage_client.bucket(self.config.GCS_BUCKET)
            blob = bucket.blob(blob_name)

            # Upload with metadata
            blob.upload_from_filename(
                local_path,
                content_type='video/mp4',
                timeout=300
            )

            # Set cache control
            blob.cache_control = 'public, max-age=86400'
            blob.patch()

            gcs_path = f"gs://{self.config.GCS_BUCKET}/{blob_name}"

            logger.info(f"Uploaded to GCS: {gcs_path}, size={blob.size}")

            return gcs_path

        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            raise

    def _publish_completion(
        self,
        request_id: str,
        hand_id: str,
        status: str,
        output_gcs_path: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        processing_time_seconds: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Publish completion message to Pub/Sub.

        Args:
            request_id: Request identifier
            hand_id: Hand identifier
            status: Completion status (completed/failed)
            output_gcs_path: GCS path to clip (if successful)
            file_size_bytes: File size in bytes
            duration_seconds: Video duration in seconds
            processing_time_seconds: Processing time in seconds
            error_message: Error message (if failed)
        """
        message_data = {
            'request_id': request_id,
            'hand_id': hand_id,
            'status': status,
            'completed_at': datetime.utcnow().isoformat() + 'Z',
            'agent_id': self.config.AGENT_ID
        }

        if output_gcs_path:
            message_data['output_gcs_path'] = output_gcs_path

        if file_size_bytes:
            message_data['file_size_bytes'] = file_size_bytes

        if duration_seconds:
            message_data['duration_seconds'] = duration_seconds

        if processing_time_seconds:
            message_data['processing_time_seconds'] = processing_time_seconds

        if error_message:
            message_data['error_message'] = error_message

        try:
            message_bytes = json.dumps(message_data).encode('utf-8')

            future = self.publisher.publish(
                self.completion_topic_path,
                message_bytes,
                request_id=request_id,
                status=status
            )

            message_id = future.result(timeout=10.0)

            logger.info(f"Published completion message: {request_id}, message_id={message_id}")

        except Exception as e:
            logger.error(f"Failed to publish completion message: {e}")
            # Don't raise - completion message is not critical for the main workflow


def main():
    """Main entry point for the agent."""
    logger.info("Starting M5 Clipping Agent...")

    agent = ClippingAgent()

    try:
        agent.start()
    except Exception as e:
        logger.error(f"Agent crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
