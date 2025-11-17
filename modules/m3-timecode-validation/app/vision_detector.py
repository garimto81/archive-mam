"""
Google Cloud Vision API Integration for Poker Scene Detection
"""
import logging
import io
from typing import Dict, Any, List, Tuple
from google.cloud import vision
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

from . import config

logger = logging.getLogger(__name__)


class VisionDetector:
    """
    Vision API client for poker scene detection
    """

    def __init__(self):
        self.vision_client = vision.ImageAnnotatorClient()
        self.storage_client = storage.Client(project=config.PROJECT_ID)
        self.enabled = config.VISION_API_ENABLED
        logger.info(f"VisionDetector initialized (enabled: {self.enabled})")

    def detect_poker_scene(
        self,
        frame_gcs_path: str
    ) -> Tuple[float, List[str]]:
        """
        Detect poker scene in a video frame using Vision API

        Args:
            frame_gcs_path: GCS path to extracted frame (gs://bucket/path/frame.jpg)

        Returns:
            Tuple of (confidence: 0.0-1.0, detected_objects: list)
        """
        if not self.enabled:
            logger.warning("Vision API disabled, returning mock confidence")
            return 0.85, ['poker_table', 'playing_cards', 'person']

        try:
            # Create image object from GCS path
            image = vision.Image()
            image.source.image_uri = frame_gcs_path

            # Perform label detection
            response = self.vision_client.label_detection(image=image)

            if response.error.message:
                logger.error(f"Vision API error: {response.error.message}")
                return 0.0, []

            labels = response.label_annotations

            # Poker-related keywords
            poker_keywords = [
                'poker', 'card', 'cards', 'playing card',
                'casino', 'game', 'table', 'chip', 'chips',
                'gambling', 'dealer', 'tournament'
            ]

            # Person detection keywords
            person_keywords = ['person', 'people', 'player', 'human']

            detected_objects = []
            max_poker_confidence = 0.0
            max_person_confidence = 0.0

            for label in labels:
                label_lower = label.description.lower()
                confidence = label.score

                # Check poker-related labels
                if any(keyword in label_lower for keyword in poker_keywords):
                    detected_objects.append(label.description)
                    max_poker_confidence = max(max_poker_confidence, confidence)
                    logger.debug(f"Poker label detected: {label.description} ({confidence:.2f})")

                # Check person-related labels
                if any(keyword in label_lower for keyword in person_keywords):
                    if 'person' not in detected_objects:
                        detected_objects.append('person')
                    max_person_confidence = max(max_person_confidence, confidence)

            # Combine confidences (poker scene should have both poker elements and people)
            if max_poker_confidence > 0 and max_person_confidence > 0:
                # Average of poker and person confidence
                overall_confidence = (max_poker_confidence + max_person_confidence) / 2.0
            elif max_poker_confidence > 0:
                # Only poker elements detected
                overall_confidence = max_poker_confidence * 0.8  # Reduce confidence
            else:
                # No poker elements
                overall_confidence = 0.0

            logger.info(
                f"Vision detection: confidence={overall_confidence:.2f}, "
                f"objects={detected_objects}"
            )

            return overall_confidence, detected_objects

        except GoogleAPIError as e:
            logger.error(f"Vision API error: {e}")
            return 0.0, []
        except Exception as e:
            logger.error(f"Unexpected error in vision detection: {e}")
            return 0.0, []

    def detect_player_count(
        self,
        frame_gcs_path: str
    ) -> int:
        """
        Detect number of players in frame using Face Detection

        Args:
            frame_gcs_path: GCS path to extracted frame

        Returns:
            Estimated player count (0 if detection fails)
        """
        if not self.enabled:
            logger.warning("Vision API disabled, returning mock player count")
            return 6

        try:
            image = vision.Image()
            image.source.image_uri = frame_gcs_path

            # Face detection to count players
            response = self.vision_client.face_detection(image=image)

            if response.error.message:
                logger.error(f"Vision API face detection error: {response.error.message}")
                return 0

            faces = response.face_annotations
            player_count = len(faces)

            logger.info(f"Detected {player_count} faces/players")

            return player_count

        except GoogleAPIError as e:
            logger.error(f"Vision API face detection error: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in player count detection: {e}")
            return 0

    def upload_frame_to_gcs(
        self,
        local_frame_path: str,
        destination_blob_name: str
    ) -> str:
        """
        Upload extracted frame to GCS for Vision API processing

        Args:
            local_frame_path: Local path to frame image
            destination_blob_name: GCS blob name (e.g., 'validation-frames/frame_001.jpg')

        Returns:
            GCS URI (gs://bucket/blob)
        """
        try:
            bucket = self.storage_client.bucket(config.GCS_BUCKET_VALIDATION)
            blob = bucket.blob(destination_blob_name)

            blob.upload_from_filename(local_frame_path)

            gcs_uri = f"gs://{config.GCS_BUCKET_VALIDATION}/{destination_blob_name}"
            logger.info(f"Frame uploaded to GCS: {gcs_uri}")

            return gcs_uri

        except Exception as e:
            logger.error(f"Failed to upload frame to GCS: {e}")
            raise


class MockVisionDetector:
    """
    Mock Vision Detector for testing without API calls
    """

    def __init__(self):
        logger.info("MockVisionDetector initialized")

    def detect_poker_scene(
        self,
        frame_gcs_path: str
    ) -> Tuple[float, List[str]]:
        """Mock poker scene detection"""
        # Deterministic mock based on path
        if 'valid' in frame_gcs_path.lower():
            return 0.92, ['poker_table', 'playing_cards', 'poker_chips', 'person']
        elif 'partial' in frame_gcs_path.lower():
            return 0.65, ['table', 'person']
        else:
            return 0.85, ['poker_table', 'playing_cards', 'person']

    def detect_player_count(
        self,
        frame_gcs_path: str
    ) -> int:
        """Mock player count detection"""
        # Return random count between 6-9
        return 7

    def upload_frame_to_gcs(
        self,
        local_frame_path: str,
        destination_blob_name: str
    ) -> str:
        """Mock GCS upload"""
        mock_uri = f"gs://{config.GCS_BUCKET_VALIDATION}/{destination_blob_name}"
        logger.info(f"[MOCK] Frame uploaded to GCS: {mock_uri}")
        return mock_uri
