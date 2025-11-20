"""
Firestore Service for archive-mam

Connects to qwen_hand_analysis Firestore database to fetch hand data.
Integrates with Vertex AI Vector Search for indexing.

Uses Google Cloud Firestore Client with explicit credentials.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)


class FirestoreService:
    """
    Firestore service to query hands from qwen_hand_analysis database.

    Schema (from qwen_hand_analysis):
      - videos/{video_id}: Video metadata
      - hands/{hand_id}: Hand data
        Fields:
        - hand_id: Unique hand identifier
        - video_ref_id: Reference to video document
        - media_refs: {master_gcs_uri, time_range{start_seconds, end_seconds, duration_seconds}}
        - game_logic: {stage, pot_final}
        - players: [{display_name, position}, ...]
        - embedding: Optional 768-dimensional vector
        - summary: Optional text summary
    """

    def __init__(self, project_id: str = None, credentials_path: str = None):
        """
        Initialize Firestore client with explicit credentials.

        Args:
            project_id: GCP project ID (defaults to GCP_PROJECT env var)
            credentials_path: Path to service account JSON file (defaults to GOOGLE_APPLICATION_CREDENTIALS env var)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT", "gg-poker-dev")

        # Get credentials path (priority: parameter > env var > settings)
        if not credentials_path:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not credentials_path:
            # Try to get from settings
            from app.config import settings
            if settings.google_application_credentials:
                if not os.path.isabs(settings.google_application_credentials):
                    # Convert relative path to absolute
                    credentials_path = os.path.abspath(
                        os.path.join(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # backend/
                            settings.google_application_credentials
                        )
                    )
                else:
                    credentials_path = settings.google_application_credentials

        print(f"[DEBUG] credentials_path: {credentials_path}")
        print(f"[DEBUG] File exists: {os.path.exists(credentials_path) if credentials_path else False}")

        # Load credentials explicitly from service account file
        if credentials_path and os.path.exists(credentials_path):
            # Load credentials with Firestore scopes
            scopes = [
                'https://www.googleapis.com/auth/datastore',
                'https://www.googleapis.com/auth/cloud-platform'
            ]
            creds = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=scopes
            )
            print(f"[DEBUG] Loaded credentials for: {creds.service_account_email}")
            print(f"[DEBUG] Project ID: {creds.project_id}")
            print(f"[DEBUG] Scopes: {creds.scopes}")

            # Firestore Native mode requires database name (default: "(default)")
            self.db = firestore.Client(
                project=self.project_id,
                credentials=creds,
                database="(default)"  # Firestore Native mode default database
            )
            print(f"[DEBUG] Firestore client initialized with explicit credentials from {credentials_path}")
            print(f"[DEBUG] Database: (default)")
            logger.info(f"Firestore client initialized with explicit credentials for project: {self.project_id}")
        else:
            # Fallback to default credentials
            self.db = firestore.Client(project=self.project_id)
            print(f"[DEBUG] Firestore client initialized with DEFAULT credentials")
            logger.info(f"Firestore client initialized with default credentials for project: {self.project_id}")

        logger.info(f"Firestore client ready for project: {self.project_id}")


    def get_all_hands(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        video_ref_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all hands from Firestore.

        Args:
            limit: Maximum number of hands to fetch (default: 100)
            status: Filter by analysis status (e.g., 'completed', 'failed')
            video_ref_id: Filter by specific video_ref_id

        Returns:
            List of hand dictionaries with all fields
        """
        try:
            query = self.db.collection("hands_phh")  # PHH schema collection

            # Apply filters
            if status:
                query = query.where(filter=FieldFilter("status", "==", status))
            if video_ref_id:
                query = query.where(filter=FieldFilter("video_ref_id", "==", video_ref_id))

            # Limit results (no ordering since timestamp_start doesn't exist)
            query = query.limit(limit)

            # Execute query
            docs = query.stream()

            hands = []
            for doc in docs:
                hand_data = doc.to_dict()
                hand_data["hand_id"] = doc.id
                hands.append(hand_data)

            logger.info(f"Fetched {len(hands)} hands from Firestore")
            return hands

        except Exception as e:
            logger.error(f"Error fetching hands from Firestore: {e}")
            raise


    def get_hand_by_id(self, hand_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single hand by ID.

        Args:
            hand_id: Hand document ID

        Returns:
            Hand dictionary with all fields, or None if not found
        """
        try:
            doc_ref = self.db.collection("hands_phh")  # PHH schema collection.document(hand_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"Hand {hand_id} not found in Firestore")
                return None

            hand_data = doc.to_dict()
            hand_data["hand_id"] = doc.id

            logger.info(f"Fetched hand {hand_id} from Firestore")
            return hand_data

        except Exception as e:
            logger.error(f"Error fetching hand {hand_id}: {e}")
            raise


    def get_hands_without_embeddings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch hands that don't have embeddings yet.

        Args:
            limit: Maximum number of hands to fetch

        Returns:
            List of hands without embeddings
        """
        try:
            # Get all hands and filter in Python (Firestore doesn't support querying for missing fields directly)
            all_hands = self.get_all_hands(limit=1000)

            hands_without_embeddings = [
                hand for hand in all_hands
                if "embedding" not in hand or hand.get("embedding") is None
            ][:limit]

            logger.info(f"Fetched {len(hands_without_embeddings)} hands without embeddings")
            return hands_without_embeddings

        except Exception as e:
            logger.error(f"Error fetching hands without embeddings: {e}")
            raise


    def update_hand_embedding(
        self,
        hand_id: str,
        embedding: List[float],
        summary: Optional[str] = None
    ) -> bool:
        """
        Update hand's embedding and summary in Firestore.

        Args:
            hand_id: Hand document ID
            embedding: 768-dimensional embedding vector
            summary: Optional summary text

        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection("hands_phh")  # PHH schema collection.document(hand_id)

            update_data = {
                "embedding": embedding,
                "embedding_updated_at": firestore.SERVER_TIMESTAMP
            }

            if summary:
                update_data["summary"] = summary

            doc_ref.update(update_data)

            logger.info(f"Updated embedding for hand {hand_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating embedding for hand {hand_id}: {e}")
            return False


    def get_hands_by_video(self, video_ref_id: str) -> List[Dict[str, Any]]:
        """
        Get all hands for a specific video.

        Args:
            video_ref_id: Video document ID (video_ref_id field)

        Returns:
            List of hands belonging to the video
        """
        try:
            query = self.db.collection("hands_phh")  # PHH schema collection
            query = query.where(filter=FieldFilter("video_ref_id", "==", video_ref_id))

            docs = query.stream()

            hands = []
            for doc in docs:
                hand_data = doc.to_dict()
                hand_data["hand_id"] = doc.id
                hands.append(hand_data)

            logger.info(f"Fetched {len(hands)} hands for video {video_ref_id}")
            return hands

        except Exception as e:
            logger.error(f"Error fetching hands for video {video_ref_id}: {e}")
            raise


    def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata from Firestore.

        Args:
            video_id: Video document ID

        Returns:
            Video metadata dictionary, or None if not found
        """
        try:
            doc_ref = self.db.collection("videos").document(video_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"Video {video_id} not found in Firestore")
                return None

            video_data = doc.to_dict()
            video_data["video_id"] = doc.id

            logger.info(f"Fetched video metadata for {video_id}")
            return video_data

        except Exception as e:
            logger.error(f"Error fetching video metadata for {video_id}: {e}")
            raise


    def batch_get_hands(self, hand_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple hands by IDs in batch.

        Args:
            hand_ids: List of hand document IDs

        Returns:
            List of hand dictionaries
        """
        try:
            hands = []

            # Firestore batch get (max 500 documents)
            for i in range(0, len(hand_ids), 500):
                batch_ids = hand_ids[i:i+500]

                for hand_id in batch_ids:
                    hand_data = self.get_hand_by_id(hand_id)
                    if hand_data:
                        hands.append(hand_data)

            logger.info(f"Batch fetched {len(hands)} hands")
            return hands

        except Exception as e:
            logger.error(f"Error in batch get hands: {e}")
            raise


# Singleton instance
_firestore_service: Optional[FirestoreService] = None


def get_firestore_service() -> FirestoreService:
    """
    Get or create Firestore service singleton.

    Returns:
        FirestoreService instance
    """
    global _firestore_service

    if _firestore_service is None:
        _firestore_service = FirestoreService()

    return _firestore_service
