"""
Vertex AI Semantic Autocomplete 테스트
1:1 Test Pairing for backend/app/services/vertex_search.py (semantic_autocomplete 메서드)
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.services.vertex_search import VertexSearchService
from app.config import settings


@pytest.fixture
def mock_vertex_service():
    """Vertex AI 서비스 mock fixture"""
    with patch.object(settings, 'enable_mock_mode', True):
        service = VertexSearchService()
        return service


@pytest.fixture
def sample_hands():
    """샘플 핸드 데이터 (Vertex AI 검색 결과)"""
    return [
        {
            "hand_id": "hand_001",
            "hero_name": "Junglemann",
            "villain_name": "Phil Ivey",
            "description": "Junglemann makes a thin river call",
            "pot_bb": 150.0,
            "street": "River",
            "action": "Call",
            "tournament": "WSOP Main Event",
            "tags": ["hero-call", "high-stakes"],
            "distance": 0.92
        },
        {
            "hand_id": "hand_002",
            "hero_name": "Daniel Dvoress",
            "villain_name": "Tom Dwan",
            "description": "Dvoress bluffs the river",
            "pot_bb": 120.0,
            "street": "River",
            "action": "Bluff",
            "tournament": "Triton Series",
            "tags": ["bluff", "river"],
            "distance": 0.85
        },
        {
            "hand_id": "hand_003",
            "hero_name": "Mikki Mase",
            "villain_name": "Garrett Adelstein",
            "description": "Mase makes a hero call",
            "pot_bb": 200.0,
            "street": "River",
            "action": "Call",
            "tournament": "Hustler Casino Live",
            "tags": ["hero-call", "controversial"],
            "distance": 0.78
        },
        {
            "hand_id": "hand_004",
            "hero_name": "Phil Hellmuth",
            "villain_name": "Daniel Negreanu",
            "description": "Hellmuth folds to pressure",
            "pot_bb": 80.0,
            "street": "Turn",
            "action": "Fold",
            "tournament": "High Stakes Duel",
            "tags": ["fold", "pressure"],
            "distance": 0.65  # Below threshold
        }
    ]


# ====================
# 정상 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_success(mock_vertex_service, sample_hands):
    """정상 케이스: 쿼리 → 임베딩 → Vector Search → 키워드 추출"""
    # Given: Mock embedding 및 vector search 결과
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(return_value=sample_hands)

    # When: semantic_autocomplete 호출
    result = await mock_vertex_service.semantic_autocomplete(
        query="Junglman",
        limit=5,
        similarity_threshold=0.7
    )

    # Then: 키워드 추출 성공 (유사도 >= 0.7인 핸드에서만)
    assert isinstance(result, list)
    assert len(result) == 5  # limit=5이므로 정확히 5개
    # Junglemann, Phil Ivey, hero-call, high-stakes, Daniel Dvoress, Tom Dwan, bluff, river, Mikki Mase, Garrett Adelstein, hero-call, controversial
    # hand_004는 distance=0.65로 threshold 미만이므로 제외
    # limit=5이므로 처음 5개만 반환
    assert "Junglemann" in result  # 첫 번째 핸드 (0.92)
    assert "Daniel Dvoress" in result  # 두 번째 핸드 (0.85)
    # Phil Hellmuth는 distance < 0.7이므로 포함되지 않아야 함
    assert "Phil Hellmuth" not in result


@pytest.mark.asyncio
async def test_semantic_autocomplete_typo_correction(mock_vertex_service, sample_hands):
    """오타 수정: "Junglman" → "Junglemann" 제안"""
    # Given
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(return_value=sample_hands[:1])

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="Junglman",  # 오타
        limit=3,
        similarity_threshold=0.7
    )

    # Then: "Junglemann" 제안
    assert "Junglemann" in result


@pytest.mark.asyncio
async def test_semantic_autocomplete_deduplication(mock_vertex_service):
    """중복 제거: 동일 선수명이 여러 핸드에 등장해도 한 번만 반환"""
    # Given: 동일 선수명이 여러 핸드에 등장
    duplicate_hands = [
        {
            "hand_id": "hand_001",
            "hero_name": "Phil Ivey",
            "villain_name": "Tom Dwan",
            "tags": ["bluff"],
            "distance": 0.95
        },
        {
            "hand_id": "hand_002",
            "hero_name": "Phil Ivey",  # 중복
            "villain_name": "Daniel Negreanu",
            "tags": ["call"],
            "distance": 0.90
        },
        {
            "hand_id": "hand_003",
            "hero_name": "Tom Dwan",  # villain에서 중복
            "villain_name": "Phil Ivey",  # 중복
            "tags": ["bluff"],  # 중복
            "distance": 0.85
        }
    ]

    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(return_value=duplicate_hands)

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="Phil",
        limit=10,
        similarity_threshold=0.7
    )

    # Then: "Phil Ivey"는 한 번만 등장 (순서 유지)
    assert result.count("Phil Ivey") == 1
    assert result.count("Tom Dwan") == 1
    assert result.count("bluff") == 1


# ====================
# 임베딩 생성 테스트
# ====================

@pytest.mark.asyncio
async def test_generate_embedding_success(mock_vertex_service):
    """임베딩 생성 성공: 768차원 벡터 반환"""
    # Given: Mock embedding (현재는 TODO로 구현 안 됨)
    text = "Junglemann makes a hero call"

    # When
    embedding = await mock_vertex_service._generate_embedding(text)

    # Then: 768차원 벡터 반환
    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)


# ====================
# Vector Search 테스트
# ====================

@pytest.mark.asyncio
async def test_vector_search_mock(mock_vertex_service):
    """Vector Search Mock 테스트"""
    # Given
    query_embedding = [0.1] * 768

    # When: Mock 모드에서는 빈 리스트 반환 (TODO 구현 전)
    result = await mock_vertex_service._vector_search(query_embedding, top_k=5)

    # Then
    assert isinstance(result, list)
    # 현재는 TODO로 빈 리스트 반환


# ====================
# 키워드 추출 테스트
# ====================

def test_extract_keywords_from_hands(mock_vertex_service, sample_hands):
    """키워드 추출: hero_name, villain_name, tags에서 추출"""
    # When
    keywords = mock_vertex_service._extract_keywords(
        hands=sample_hands,
        threshold=0.7
    )

    # Then
    assert isinstance(keywords, list)
    # hand_001: Junglemann, Phil Ivey, hero-call, high-stakes
    # hand_002: Daniel Dvoress, Tom Dwan, bluff, river
    # hand_003: Mikki Mase, Garrett Adelstein, hero-call, controversial
    # hand_004: distance=0.65 < 0.7 → 제외
    assert "Junglemann" in keywords
    assert "Phil Ivey" in keywords
    assert "hero-call" in keywords
    assert "Daniel Dvoress" in keywords
    assert "Tom Dwan" in keywords
    assert "Mikki Mase" in keywords
    # hand_004는 threshold 미만이므로 포함 안 됨
    assert "Phil Hellmuth" not in keywords


def test_extract_keywords_threshold_filtering(mock_vertex_service, sample_hands):
    """키워드 추출: 유사도 임계값 필터링"""
    # When: threshold=0.8로 높게 설정
    keywords = mock_vertex_service._extract_keywords(
        hands=sample_hands,
        threshold=0.8
    )

    # Then: distance >= 0.8인 핸드만 포함
    # hand_001 (0.92), hand_002 (0.85) → 포함
    # hand_003 (0.78), hand_004 (0.65) → 제외
    assert "Junglemann" in keywords
    assert "Daniel Dvoress" in keywords
    assert "Mikki Mase" not in keywords  # 0.78 < 0.8
    assert "Phil Hellmuth" not in keywords  # 0.65 < 0.8


def test_extract_keywords_empty_hands(mock_vertex_service):
    """키워드 추출: 빈 핸드 리스트"""
    # When
    keywords = mock_vertex_service._extract_keywords(
        hands=[],
        threshold=0.7
    )

    # Then
    assert keywords == []


def test_extract_keywords_no_tags(mock_vertex_service):
    """키워드 추출: 태그 없는 핸드"""
    # Given: 태그 없는 핸드
    hands_no_tags = [
        {
            "hand_id": "hand_001",
            "hero_name": "Phil Ivey",
            "villain_name": None,
            "tags": [],
            "distance": 0.9
        }
    ]

    # When
    keywords = mock_vertex_service._extract_keywords(
        hands=hands_no_tags,
        threshold=0.7
    )

    # Then: 선수명만 추출
    assert keywords == ["Phil Ivey"]


# ====================
# 타임아웃 테스트
# ====================

@pytest.mark.asyncio
async def test_vector_search_timeout(mock_vertex_service):
    """타임아웃 테스트: 5초 초과 시 에러 처리"""
    # Given: 타임아웃 시뮬레이션
    async def slow_embedding(text):
        await asyncio.sleep(6)  # 5초 초과
        return [0.1] * 768

    mock_vertex_service._generate_embedding = slow_embedding
    mock_vertex_service._vector_search = AsyncMock(return_value=[])

    # When: timeout 적용
    import asyncio
    try:
        result = await asyncio.wait_for(
            mock_vertex_service.semantic_autocomplete("test"),
            timeout=5.0
        )
        assert False, "Should have timed out"
    except asyncio.TimeoutError:
        # Then: TimeoutError 발생
        assert True


# ====================
# 에러 핸들링 테스트
# ====================

@pytest.mark.asyncio
async def test_graceful_degradation(mock_vertex_service):
    """에러 핸들링: Vertex AI API 장애 시 빈 배열 반환"""
    # Given: API 장애 시뮬레이션
    mock_vertex_service._generate_embedding = AsyncMock(
        side_effect=Exception("Vertex AI API error")
    )

    # When: semantic_autocomplete 호출
    result = await mock_vertex_service.semantic_autocomplete(
        query="test",
        limit=5
    )

    # Then: 빈 배열 반환 (graceful degradation)
    assert result == []


@pytest.mark.asyncio
async def test_vector_search_api_error(mock_vertex_service):
    """Vector Search API 에러 핸들링"""
    # Given
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(
        side_effect=Exception("Vector Search API error")
    )

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="test",
        limit=5
    )

    # Then: 빈 배열 반환
    assert result == []


# ====================
# 엣지 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_empty_query(mock_vertex_service):
    """빈 쿼리 처리"""
    # Given
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(return_value=[])

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="",
        limit=5
    )

    # Then: 빈 배열 반환 또는 에러
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_semantic_autocomplete_limit_zero(mock_vertex_service, sample_hands):
    """limit=0 처리"""
    # Given
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(return_value=sample_hands)

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="test",
        limit=0
    )

    # Then: 빈 배열 반환
    assert result == []


@pytest.mark.asyncio
async def test_semantic_autocomplete_large_limit(mock_vertex_service, sample_hands):
    """큰 limit 값 처리"""
    # Given
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_vertex_service._vector_search = AsyncMock(return_value=sample_hands)

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="test",
        limit=100
    )

    # Then: 실제 추출된 키워드 개수만큼만 반환
    assert len(result) <= 100
    assert isinstance(result, list)


# ====================
# 통합 테스트
# ====================

@pytest.mark.asyncio
async def test_semantic_autocomplete_integration(mock_vertex_service):
    """전체 흐름 통합 테스트"""
    # Given: 실제 Mock 데이터 사용 (settings.test_data_path)
    mock_vertex_service._generate_embedding = AsyncMock(return_value=[0.1] * 768)

    # Mock vector search 결과
    integration_hands = [
        {
            "hand_id": "hand_001",
            "hero_name": "Junglemann",
            "villain_name": "Phil Ivey",
            "tags": ["hero-call", "river"],
            "distance": 0.92
        },
        {
            "hand_id": "hand_002",
            "hero_name": "Daniel Dvoress",
            "villain_name": "Garrett Adelstein",
            "tags": ["bluff", "high-stakes"],
            "distance": 0.88
        }
    ]
    mock_vertex_service._vector_search = AsyncMock(return_value=integration_hands)

    # When
    result = await mock_vertex_service.semantic_autocomplete(
        query="Junglman",  # 오타
        limit=5,
        similarity_threshold=0.7
    )

    # Then
    assert len(result) > 0
    assert "Junglemann" in result
    # 유사도 순으로 정렬되어야 함 (distance 높은 순)
    assert result[0] == "Junglemann"  # hand_001이 0.92로 가장 높음
