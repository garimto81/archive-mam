"""
Vertex AI Embedding Service

Development mode: Generate mock embeddings
Production mode: Use Vertex AI TextEmbedding-004
"""
import logging
import random
from typing import List, Dict, Any

from .config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class EmbeddingService:
    """Embedding generation service with mock/real switching"""

    def __init__(self):
        self.config = config
        self.model = None

        if config.is_production():
            self._init_vertex_ai()

    def _init_vertex_ai(self):
        """Initialize Vertex AI embedding model"""
        try:
            from vertexai.language_models import TextEmbeddingModel
            import vertexai

            # Initialize Vertex AI
            vertexai.init(
                project=config.GCP_PROJECT,
                location=config.VERTEX_AI_LOCATION
            )

            # Load embedding model
            self.model = TextEmbeddingModel.from_pretrained(config.EMBEDDING_MODEL)
            logger.info(f"Loaded Vertex AI model: {config.EMBEDDING_MODEL}")

        except ImportError:
            logger.error("vertexai package not installed. Install with: pip install google-cloud-aiplatform")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}", exc_info=True)
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Args:
            text: Input text

        Returns:
            768-dimensional embedding vector
        """
        if config.is_development():
            return self._generate_mock_embedding(text)
        else:
            return self._generate_vertex_ai_embedding(text)

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for batch of texts

        Args:
            texts: List of input texts

        Returns:
            List of 768-dimensional embedding vectors
        """
        if config.is_development():
            return [self._generate_mock_embedding(text) for text in texts]
        else:
            return self._generate_vertex_ai_embeddings_batch(texts)

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate mock embedding for development

        Uses deterministic random seed based on text hash
        to ensure same text always gets same embedding
        """
        # Use text hash as seed for reproducibility
        seed = hash(text) % (2**32)
        random.seed(seed)

        # Generate 768-dim vector with mean=0, std=0.3
        embedding = [random.gauss(0, 0.3) for _ in range(config.EMBEDDING_DIMENSION)]

        # Normalize to unit vector (cosine similarity works better)
        magnitude = sum(x ** 2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def _generate_vertex_ai_embedding(self, text: str) -> List[float]:
        """Generate real embedding using Vertex AI"""
        try:
            embeddings = self.model.get_embeddings([text])
            return embeddings[0].values

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}", exc_info=True)
            # Fallback to mock embedding
            logger.warning("Falling back to mock embedding")
            return self._generate_mock_embedding(text)

    def _generate_vertex_ai_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 5
    ) -> List[List[float]]:
        """
        Generate embeddings in batches using Vertex AI

        Vertex AI has limit of 5 texts per API call,
        so we batch the requests.
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                embeddings = self.model.get_embeddings(batch)
                all_embeddings.extend([emb.values for emb in embeddings])

            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}", exc_info=True)
                # Fallback to mock
                all_embeddings.extend([
                    self._generate_mock_embedding(text) for text in batch
                ])

        return all_embeddings


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton"""
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
