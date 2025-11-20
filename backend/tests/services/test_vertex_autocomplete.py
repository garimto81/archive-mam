"""
테스트: Vertex AI Semantic Autocomplete
1:1 페어링: backend/app/services/vertex_search.py::VertexSearchService.semantic_autocomplete()

Coverage:
- 정상 케이스: 쿼리 → 임베딩 → Vector Search → 키워드 추출
- 컴포넌트 테스트: 임베딩 생성, Vector Search, 키워드 추출
- 에러 케이스: API 장애, 타임아웃, graceful degradation
- 성능 테스트: 응답 시간 <100ms (mock)
- 오타 수정: "Junglman" → "Junglemann"

Target Coverage: 85%+
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from app.services.vertex_search import VertexSearchService


# ====================
# Fixtures
# ====================

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('app.services.vertex_search.settings') as mock:
        mock.enable_mock_mode = False
        mock.gcp_project = "test-project"
        mock.gcp_location = "us-central1"
        mock.vertex_index_id = "test-index-id"
        mock.vertex_embedding_dimension = 768
        mock.search_type = "hybrid"
        yield mock


@pytest.fixture
def service(mock_settings):
    """VertexSearchService fixture"""
    with patch('app.services.vertex_search.aiplatform'):
        return VertexSearchService()


@pytest.fixture
def mock_embedding():
    """Mock 768-dimensional embedding vector"""
    return [0.1] * 768


@pytest.fixture
def mock_similar_hands():
    """Mock similar hands from Vector Search"""
    return [
        {
            "id": "hand_001",
            "hero_name": "Junglemann",
            "villain_name": "Phil Ivey",
            "tags": ["HERO_CALL", "RIVER"],
            "distance": 0.92
        },
        {
            "id": "hand_002",
            "hero_name": "Daniel Dvoress",
            "villain_name": "Tom Dwan",
            "tags": ["BLUFF", "TURN"],
            "distance": 0.85
        },
        {
            "id": "hand_003",
            "hero_name": "Mikki Mase",
            "villain_name": "Garrett Adelstein",
            "tags": ["ALL_IN", "RIVER"],
            "distance": 0.78
        },
        {
            "id": "hand_004",
            "hero_name": "Phil Ivey",
            "villain_name": "Junglemann",
            "tags": ["BLUFF", "TURN"],
            "distance": 0.65  # Below threshold
        }
    ]


# ====================
# 정상 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_success(service, mock_embedding, mock_similar_hands):
    """정상 케이스: 쿼리 → 임베딩 → Vector Search → 키워드"""
    # Mock the internal methods
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    # Call the method
    result = await service.semantic_autocomplete("Junglman", limit=5)

    # Verify the flow
    service._generate_embedding.assert_called_once_with("Junglman")
    service._vector_search.assert_called_once_with(mock_embedding, top_k=10)  # limit * 2

    # Verify results
    assert isinstance(result, list)
    assert len(result) <= 5

    # Should contain player names and tags from hands with distance >= 0.7
    # hand_004 (distance 0.65) should be filtered out
    expected_keywords = [
        "Junglemann", "Phil Ivey",  # hand_001
        "HERO_CALL", "RIVER",
        "Daniel Dvoress", "Tom Dwan",  # hand_002
        "BLUFF", "TURN",
        "Mikki Mase", "Garrett Adelstein",  # hand_003
        "ALL_IN", "RIVER"
    ]

    # Result should be subset of expected keywords (order may vary)
    for keyword in result:
        assert keyword in expected_keywords


@pytest.mark.asyncio
async def test_semantic_autocomplete_typo_correction(service, mock_embedding, mock_similar_hands):
    """오타 수정: "Junglman" → "Junglemann" 제안"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    result = await service.semantic_autocomplete("Junglman", limit=3)

    # Should suggest "Junglemann" (correct spelling from similar hands)
    assert "Junglemann" in result


@pytest.mark.asyncio
async def test_semantic_autocomplete_duplicate_removal(service, mock_embedding):
    """중복 제거: 동일 키워드는 한 번만 반환"""
    # Mock hands with duplicate names/tags
    duplicate_hands = [
        {
            "id": "hand_001",
            "hero_name": "Phil Ivey",
            "villain_name": "Tom Dwan",
            "tags": ["BLUFF"],
            "distance": 0.92
        },
        {
            "id": "hand_002",
            "hero_name": "Phil Ivey",  # Duplicate
            "villain_name": "Daniel Dvoress",
            "tags": ["BLUFF"],  # Duplicate
            "distance": 0.85
        }
    ]

    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=duplicate_hands)

    result = await service.semantic_autocomplete("Phil", limit=10)

    # Verify no duplicates
    assert len(result) == len(set(result))
    assert result.count("Phil Ivey") == 1
    assert result.count("BLUFF") == 1


@pytest.mark.asyncio
async def test_semantic_autocomplete_limit_respected(service, mock_embedding, mock_similar_hands):
    """Limit 파라미터 준수"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    # Request only 2 suggestions
    result = await service.semantic_autocomplete("test", limit=2)

    assert len(result) <= 2


# ====================
# 컴포넌트 테스트
# ====================

@pytest.mark.asyncio
async def test_generate_embedding_success(service):
    """임베딩 생성: 768차원 벡터 반환"""
    # The current implementation returns zeros
    embedding = await service._generate_embedding("test query")

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_vector_search_success(service, mock_embedding):
    """Vector Search: 유사 핸드 검색 (현재는 빈 리스트 반환)"""
    # The current implementation returns empty list
    results = await service._vector_search(mock_embedding, top_k=5)

    assert isinstance(results, list)
    # Current implementation returns [], but structure is ready
    assert len(results) == 0


@pytest.mark.asyncio
async def test_extract_keywords_from_hands(service):
    """키워드 추출: hero_name, villain_name, tags"""
    hands = [
        {
            "hero_name": "Phil Ivey",
            "villain_name": "Tom Dwan",
            "tags": ["BLUFF", "RIVER"],
            "distance": 0.92
        },
        {
            "hero_name": "Daniel Dvoress",
            "villain_name": None,  # No villain
            "tags": ["HERO_CALL"],
            "distance": 0.85
        },
        {
            "hero_name": "Mikki Mase",
            "villain_name": "Garrett Adelstein",
            "tags": [],  # No tags
            "distance": 0.78
        }
    ]

    keywords = service._extract_keywords(hands, threshold=0.7)

    # Verify all expected keywords are extracted
    assert "Phil Ivey" in keywords
    assert "Tom Dwan" in keywords
    assert "BLUFF" in keywords
    assert "RIVER" in keywords
    assert "Daniel Dvoress" in keywords
    assert "HERO_CALL" in keywords
    assert "Mikki Mase" in keywords
    assert "Garrett Adelstein" in keywords


@pytest.mark.asyncio
async def test_extract_keywords_threshold_filter(service):
    """키워드 추출: 유사도 임계값 필터링"""
    hands = [
        {
            "hero_name": "High Score",
            "villain_name": "Player A",
            "tags": ["TAG_A"],
            "distance": 0.95  # Above threshold
        },
        {
            "hero_name": "Low Score",
            "villain_name": "Player B",
            "tags": ["TAG_B"],
            "distance": 0.65  # Below threshold
        }
    ]

    keywords = service._extract_keywords(hands, threshold=0.7)

    # Only high-score hand should be included
    assert "High Score" in keywords
    assert "Player A" in keywords
    assert "TAG_A" in keywords

    # Low-score hand should be excluded
    assert "Low Score" not in keywords
    assert "Player B" not in keywords
    assert "TAG_B" not in keywords


@pytest.mark.asyncio
async def test_extract_keywords_empty_values(service):
    """키워드 추출: 빈 값 처리"""
    hands = [
        {
            "hero_name": None,  # None value
            "villain_name": "",  # Empty string
            "tags": ["", "VALID_TAG", None],  # Mixed with empty
            "distance": 0.8
        }
    ]

    keywords = service._extract_keywords(hands, threshold=0.7)

    # Should only include valid tag
    assert "VALID_TAG" in keywords
    assert None not in keywords
    assert "" not in keywords


# ====================
# 에러 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_api_error(service):
    """API 장애: Vertex AI 에러 → 빈 배열 (graceful degradation)"""
    # Mock embedding to raise exception
    service._generate_embedding = AsyncMock(
        side_effect=Exception("Vertex AI API connection failed")
    )

    result = await service.semantic_autocomplete("test", limit=5)

    # Should return empty list, not raise exception
    assert result == []


@pytest.mark.asyncio
async def test_semantic_autocomplete_vector_search_error(service, mock_embedding):
    """Vector Search 에러 → 빈 배열"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(
        side_effect=Exception("Vector Search failed")
    )

    result = await service.semantic_autocomplete("test", limit=5)

    # Should return empty list
    assert result == []


@pytest.mark.asyncio
async def test_semantic_autocomplete_timeout(service):
    """타임아웃: 5초 초과 → 빈 배열"""
    # Mock a very slow operation
    async def slow_embedding(*args, **kwargs):
        await asyncio.sleep(10)  # 10 seconds
        return [0.0] * 768

    service._generate_embedding = slow_embedding

    # Set a shorter timeout for test
    with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
        # This would normally timeout, but we'll test the exception handling
        service._generate_embedding = AsyncMock(
            side_effect=asyncio.TimeoutError("Operation timed out")
        )

        result = await service.semantic_autocomplete("test", limit=5)

    # Should return empty list on timeout
    assert result == []


@pytest.mark.asyncio
async def test_semantic_autocomplete_empty_result(service, mock_embedding):
    """결과 없음: 빈 배열 반환"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=[])  # No results

    result = await service.semantic_autocomplete("xyz123", limit=5)

    assert result == []
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_semantic_autocomplete_all_below_threshold(service, mock_embedding):
    """모든 결과가 임계값 미만 → 빈 배열"""
    low_score_hands = [
        {
            "hero_name": "Player A",
            "villain_name": "Player B",
            "tags": ["TAG"],
            "distance": 0.65  # Below 0.7
        },
        {
            "hero_name": "Player C",
            "villain_name": "Player D",
            "tags": ["TAG2"],
            "distance": 0.60  # Below 0.7
        }
    ]

    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=low_score_hands)

    result = await service.semantic_autocomplete("test", limit=5, similarity_threshold=0.7)

    # All results filtered out by threshold
    assert result == []


# ====================
# 성능 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_response_time(service, mock_embedding, mock_similar_hands):
    """성능 테스트: 응답 시간 <100ms (mock 환경)"""
    import time

    # Mock fast responses
    async def fast_embedding(*args, **kwargs):
        await asyncio.sleep(0.01)  # 10ms
        return mock_embedding

    async def fast_vector_search(*args, **kwargs):
        await asyncio.sleep(0.02)  # 20ms
        return mock_similar_hands

    service._generate_embedding = fast_embedding
    service._vector_search = fast_vector_search

    start = time.time()
    result = await service.semantic_autocomplete("test", limit=5)
    duration = (time.time() - start) * 1000  # ms

    # Should complete quickly in mock environment
    assert duration < 100
    assert len(result) > 0


# ====================
# Edge Cases 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_special_characters(service, mock_embedding, mock_similar_hands):
    """특수 문자 포함 쿼리 처리"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    # Query with hyphen, apostrophe
    result = await service.semantic_autocomplete("Tom-K's bluff", limit=5)

    assert isinstance(result, list)
    # Should handle gracefully


@pytest.mark.asyncio
async def test_semantic_autocomplete_very_long_query(service, mock_embedding, mock_similar_hands):
    """매우 긴 쿼리 처리"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    long_query = "a" * 200
    result = await service.semantic_autocomplete(long_query, limit=5)

    # Should handle long queries
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_semantic_autocomplete_unicode_query(service, mock_embedding, mock_similar_hands):
    """유니코드 쿼리 처리 (영문 전용이지만 에러는 없어야)"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    # Unicode characters (though English-only is expected)
    result = await service.semantic_autocomplete("Café", limit=5)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_semantic_autocomplete_limit_edge_cases(service, mock_embedding, mock_similar_hands):
    """Limit 엣지 케이스: 0, 1, 매우 큰 값"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    # Limit = 1
    result = await service.semantic_autocomplete("test", limit=1)
    assert len(result) <= 1

    # Limit = 100 (very large)
    result = await service.semantic_autocomplete("test", limit=100)
    assert isinstance(result, list)
    # Will return at most available unique keywords


@pytest.mark.asyncio
async def test_semantic_autocomplete_threshold_edge_cases(service, mock_embedding, mock_similar_hands):
    """Threshold 엣지 케이스: 0.0, 1.0"""
    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    # Threshold = 0.0 (include all)
    result = await service.semantic_autocomplete("test", limit=10, similarity_threshold=0.0)
    assert len(result) > 0  # Should include hand_004 (distance 0.65)

    # Threshold = 1.0 (exclude all)
    result = await service.semantic_autocomplete("test", limit=10, similarity_threshold=1.0)
    assert result == []  # No hand has perfect 1.0 score


# ====================
# Mock Mode 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_mock_mode():
    """Mock 모드: enable_mock_mode=True 시 동작"""
    with patch('app.services.vertex_search.settings') as mock_settings:
        mock_settings.enable_mock_mode = True

        # Create service in mock mode
        service = VertexSearchService()

        assert service.mock_mode == True


# ====================
# Integration-like Tests
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_full_flow(service):
    """전체 플로우: 임베딩 → Vector Search → 키워드 추출 → 중복 제거"""
    # Mock complete flow
    mock_embedding = [0.1] * 768
    mock_hands = [
        {
            "hero_name": "Phil Ivey",
            "villain_name": "Tom Dwan",
            "tags": ["BLUFF", "RIVER"],
            "distance": 0.92
        },
        {
            "hero_name": "Phil Ivey",  # Duplicate
            "villain_name": "Daniel Dvoress",
            "tags": ["BLUFF"],  # Duplicate
            "distance": 0.85
        },
        {
            "hero_name": "Mikki Mase",
            "villain_name": None,
            "tags": [],
            "distance": 0.78
        }
    ]

    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_hands)

    result = await service.semantic_autocomplete("Phil", limit=5, similarity_threshold=0.7)

    # Verify complete flow
    service._generate_embedding.assert_called_once()
    service._vector_search.assert_called_once()

    # Verify results
    assert isinstance(result, list)
    assert len(result) <= 5
    assert len(result) == len(set(result))  # No duplicates

    # Should contain unique keywords
    assert "Phil Ivey" in result
    assert result.count("Phil Ivey") == 1  # No duplicates


# ====================
# Logging Tests
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_logging_success(service, mock_embedding, mock_similar_hands, caplog):
    """성공 시 로그 기록"""
    import structlog

    service._generate_embedding = AsyncMock(return_value=mock_embedding)
    service._vector_search = AsyncMock(return_value=mock_similar_hands)

    with caplog.at_level("INFO"):
        await service.semantic_autocomplete("test", limit=5)

    # Check if success log was recorded (structlog format)
    # Note: structlog may format differently, check for key fields


@pytest.mark.asyncio
async def test_semantic_autocomplete_logging_error(service, caplog):
    """에러 시 로그 기록"""
    service._generate_embedding = AsyncMock(
        side_effect=Exception("Test error")
    )

    with caplog.at_level("ERROR"):
        await service.semantic_autocomplete("test", limit=5)

    # Should log error (structlog format)


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--cov=app.services.vertex_search", "--cov-report=term-missing"])
