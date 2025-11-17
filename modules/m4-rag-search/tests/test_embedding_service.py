"""
Tests for Embedding Service
"""
import pytest
from unittest.mock import patch, MagicMock

from app.embedding_service import EmbeddingService, get_embedding_service
from app.config import get_config


class TestEmbeddingService:
    """Tests for EmbeddingService class"""

    def test_generate_mock_embedding(self):
        """Test mock embedding generation"""
        service = EmbeddingService()

        text = "Tom Dwan wins big pot"
        embedding = service.generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

        # Test deterministic behavior
        embedding2 = service.generate_embedding(text)
        assert embedding == embedding2

    def test_generate_mock_embedding_different_texts(self):
        """Test that different texts produce different embeddings"""
        service = EmbeddingService()

        text1 = "Tom Dwan"
        text2 = "Phil Ivey"

        embedding1 = service.generate_embedding(text1)
        embedding2 = service.generate_embedding(text2)

        assert embedding1 != embedding2

    def test_generate_embeddings_batch(self):
        """Test batch embedding generation"""
        service = EmbeddingService()

        texts = [
            "Tom Dwan wins",
            "Phil Ivey raises",
            "WSOP 2024"
        ]

        embeddings = service.generate_embeddings_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)

    def test_embedding_normalization(self):
        """Test that embeddings are normalized"""
        service = EmbeddingService()

        embedding = service.generate_embedding("test text")

        # Calculate magnitude
        magnitude = sum(x ** 2 for x in embedding) ** 0.5

        # Should be close to 1.0 (unit vector)
        assert abs(magnitude - 1.0) < 0.01

    def test_singleton_pattern(self):
        """Test singleton pattern"""
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        assert service1 is service2


class TestVertexAIIntegration:
    """Tests for Vertex AI integration (mocked)"""

    @patch('app.embedding_service.TextEmbeddingModel')
    @patch('app.embedding_service.vertexai')
    def test_vertex_ai_initialization(self, mock_vertexai, mock_model_class):
        """Test Vertex AI model initialization in production"""
        config = get_config()
        original_env = config.ENV

        try:
            # Set production mode
            config.ENV = 'production'

            mock_model = MagicMock()
            mock_model_class.from_pretrained.return_value = mock_model

            service = EmbeddingService()

            # Verify initialization calls
            mock_vertexai.init.assert_called_once()
            mock_model_class.from_pretrained.assert_called_once()

        finally:
            # Restore environment
            config.ENV = original_env

    @patch('app.embedding_service.TextEmbeddingModel')
    @patch('app.embedding_service.vertexai')
    def test_vertex_ai_embedding_generation(self, mock_vertexai, mock_model_class):
        """Test embedding generation with Vertex AI"""
        config = get_config()
        original_env = config.ENV

        try:
            config.ENV = 'production'

            # Mock model response
            mock_embedding = MagicMock()
            mock_embedding.values = [0.1] * 768

            mock_model = MagicMock()
            mock_model.get_embeddings.return_value = [mock_embedding]
            mock_model_class.from_pretrained.return_value = mock_model

            service = EmbeddingService()
            embedding = service._generate_vertex_ai_embedding("test text")

            assert len(embedding) == 768
            mock_model.get_embeddings.assert_called_once_with(["test text"])

        finally:
            config.ENV = original_env

    @patch('app.embedding_service.TextEmbeddingModel')
    @patch('app.embedding_service.vertexai')
    def test_vertex_ai_batch_embedding(self, mock_vertexai, mock_model_class):
        """Test batch embedding generation with Vertex AI"""
        config = get_config()
        original_env = config.ENV

        try:
            config.ENV = 'production'

            # Mock model response
            mock_embeddings = [MagicMock(values=[0.1] * 768) for _ in range(3)]

            mock_model = MagicMock()
            mock_model.get_embeddings.return_value = mock_embeddings
            mock_model_class.from_pretrained.return_value = mock_model

            service = EmbeddingService()
            texts = ["text1", "text2", "text3"]
            embeddings = service._generate_vertex_ai_embeddings_batch(texts)

            assert len(embeddings) == 3
            assert all(len(emb) == 768 for emb in embeddings)

        finally:
            config.ENV = original_env

    @patch('app.embedding_service.TextEmbeddingModel')
    @patch('app.embedding_service.vertexai')
    def test_vertex_ai_error_fallback(self, mock_vertexai, mock_model_class):
        """Test fallback to mock embedding on Vertex AI error"""
        config = get_config()
        original_env = config.ENV

        try:
            config.ENV = 'production'

            # Mock model to raise error
            mock_model = MagicMock()
            mock_model.get_embeddings.side_effect = Exception("API Error")
            mock_model_class.from_pretrained.return_value = mock_model

            service = EmbeddingService()
            embedding = service._generate_vertex_ai_embedding("test text")

            # Should fallback to mock embedding
            assert len(embedding) == 768

        finally:
            config.ENV = original_env
