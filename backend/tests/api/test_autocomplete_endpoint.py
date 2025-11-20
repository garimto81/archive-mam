"""
테스트: Autocomplete API 엔드포인트
1:1 페어링: backend/app/api/autocomplete.py

Coverage:
- 정상 케이스: 쿼리 → 결과 반환
- 에러 케이스: 입력 검증, Rate limiting
- 성능 테스트: 응답 시간
- Two-tier 전략: BigQuery → Vertex AI fallback
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import time

# Import the app
from app.main import app
from app.api import autocomplete

client = TestClient(app)


# ====================
# 정상 케이스 테스트
# ====================

def test_autocomplete_success():
    """정상 케이스: 쿼리 → 결과 반환"""
    # Mock the services
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # Setup mock BigQuery service
        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Phil Ivey", "Phil Hellmuth", "Philip Ng"]
        )
        mock_bq.return_value = mock_bq_service

        # Setup mock Vertex service (not called in this case)
        mock_vertex_service = MagicMock()
        mock_vertex.return_value = mock_vertex_service

        # Make request
        response = client.get("/api/autocomplete?q=Phil&limit=5")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "suggestions" in data
        assert "query" in data
        assert "source" in data
        assert "response_time_ms" in data
        assert "total" in data

        # Verify data
        assert data["query"] == "Phil"
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) <= 5
        assert data["source"] == "bigquery_cache"
        assert data["total"] == len(data["suggestions"])


def test_autocomplete_with_special_characters():
    """정상 케이스: 하이픈과 공백 포함된 쿼리"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Tom Dwan", "Tom-K Smith"]
        )
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=Tom-K&limit=3")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Tom-K"
        assert len(data["suggestions"]) <= 3


# ====================
# 입력 검증 테스트
# ====================

def test_autocomplete_query_too_short():
    """에러 케이스: 쿼리 2자 미만"""
    response = client.get("/api/autocomplete?q=P")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # FastAPI's validation error format
    assert any("at least 2 characters" in str(err) for err in data["detail"])


def test_autocomplete_query_too_long():
    """에러 케이스: 쿼리 100자 초과"""
    long_query = "a" * 101
    response = client.get("/api/autocomplete?q=" + long_query)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_autocomplete_invalid_characters():
    """에러 케이스: 특수문자 포함"""
    response = client.get("/api/autocomplete?q=Phil<script>")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_autocomplete_sql_injection_attempt():
    """에러 케이스: SQL 인젝션 시도"""
    response = client.get("/api/autocomplete?q=Phil'; DROP TABLE--")

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_autocomplete_limit_validation():
    """에러 케이스: limit 범위 벗어남"""
    # Limit too high
    response = client.get("/api/autocomplete?q=Phil&limit=20")
    assert response.status_code == 422

    # Limit too low
    response = client.get("/api/autocomplete?q=Phil&limit=0")
    assert response.status_code == 422


# ====================
# Rate Limiting 테스트
# ====================

def test_autocomplete_rate_limiting():
    """Rate limiting: 100 req/min 초과 시 429"""
    # Clear rate limit storage
    autocomplete.rate_limit_storage.clear()

    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Test Result"]
        )
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex.return_value = mock_vertex_service

        # Simulate requests from same IP
        test_ip = "192.168.1.1"

        # Mock client IP
        with patch('app.api.autocomplete.get_client_ip', return_value=test_ip):
            # Fill up rate limit
            now = datetime.now()
            autocomplete.rate_limit_storage[test_ip] = [
                now - timedelta(seconds=i) for i in range(100)
            ]

            # 101st request should be rejected
            response = client.get("/api/autocomplete?q=Phil")

            assert response.status_code == 429
            data = response.json()
            assert data["detail"]["error"] == "Rate limit exceeded"
            assert "100 requests per minute" in data["detail"]["message"]

    # Clean up
    autocomplete.rate_limit_storage.clear()


def test_autocomplete_rate_limit_window_reset():
    """Rate limiting: 1분 후 윈도우 리셋"""
    autocomplete.rate_limit_storage.clear()

    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Test Result"]
        )
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex.return_value = mock_vertex_service

        test_ip = "192.168.1.2"

        with patch('app.api.autocomplete.get_client_ip', return_value=test_ip):
            # Add old requests (>1 minute ago)
            old_time = datetime.now() - timedelta(minutes=2)
            autocomplete.rate_limit_storage[test_ip] = [old_time for _ in range(100)]

            # Should allow new request (old ones expired)
            response = client.get("/api/autocomplete?q=Phil")

            assert response.status_code == 200

    autocomplete.rate_limit_storage.clear()


# ====================
# Two-Tier 검색 전략 테스트
# ====================

def test_autocomplete_bigquery_cache_only():
    """Tier 1: BigQuery 캐시만 사용 (결과 충분)"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # BigQuery returns enough results
        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Phil Ivey", "Phil Hellmuth", "Philip Ng", "Phil Galfond"]
        )
        mock_bq.return_value = mock_bq_service

        # Vertex should not be called
        mock_vertex_service = MagicMock()
        mock_vertex_service.semantic_autocomplete = AsyncMock()
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=Phil&limit=3")

        assert response.status_code == 200
        data = response.json()

        # Verify only BigQuery was used
        assert data["source"] == "bigquery_cache"
        assert len(data["suggestions"]) == 3

        # Vertex should not have been called
        mock_vertex_service.semantic_autocomplete.assert_not_called()


def test_autocomplete_hybrid_fallback():
    """Tier 2: BigQuery 부족 시 Vertex AI 호출"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # BigQuery returns insufficient results
        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Junglemann"]  # Only 1 result
        )
        mock_bq.return_value = mock_bq_service

        # Vertex provides additional results
        mock_vertex_service = MagicMock()
        mock_vertex_service.semantic_autocomplete = AsyncMock(
            return_value=["Daniel Dvoress", "Mikki Mase"]
        )
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=Junglman&limit=3")

        assert response.status_code == 200
        data = response.json()

        # Verify hybrid source
        assert data["source"] == "hybrid"
        assert len(data["suggestions"]) == 3
        assert "Junglemann" in data["suggestions"]

        # Vertex should have been called
        mock_vertex_service.semantic_autocomplete.assert_called_once()


def test_autocomplete_duplicate_removal():
    """하이브리드 검색 시 중복 제거"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # Both services return overlapping results
        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=["Phil Ivey", "Tom Dwan"]
        )
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex_service.semantic_autocomplete = AsyncMock(
            return_value=["Tom Dwan", "Daniel Negreanu"]  # "Tom Dwan" is duplicate
        )
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=Tom&limit=5")

        assert response.status_code == 200
        data = response.json()

        # Verify duplicates are removed
        suggestions = data["suggestions"]
        assert len(suggestions) == len(set(suggestions))  # No duplicates
        assert suggestions.count("Tom Dwan") == 1


# ====================
# 성능 테스트
# ====================

def test_autocomplete_response_time_bigquery():
    """성능 테스트: BigQuery 캐시 응답 시간 <100ms"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # Simulate fast BigQuery response
        mock_bq_service = MagicMock()

        async def fast_bigquery(*args, **kwargs):
            # Simulate 8ms query time
            await asyncio.sleep(0.008)
            return ["Phil Ivey", "Phil Hellmuth"]

        import asyncio
        mock_bq_service.get_autocomplete_suggestions = fast_bigquery
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex.return_value = mock_vertex_service

        start = time.time()
        response = client.get("/api/autocomplete?q=Phil")
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        data = response.json()

        # Check reported response time
        assert data["response_time_ms"] < 100
        assert data["source"] == "bigquery_cache"

        # Check actual response time (with some overhead tolerance)
        assert duration < 200  # Allow for test overhead


def test_autocomplete_response_time_hybrid():
    """성능 테스트: 하이브리드 검색도 <100ms 목표"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # Simulate slower responses
        mock_bq_service = MagicMock()

        async def slow_bigquery(*args, **kwargs):
            await asyncio.sleep(0.010)  # 10ms
            return ["Result1"]

        mock_bq_service.get_autocomplete_suggestions = slow_bigquery
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()

        async def slow_vertex(*args, **kwargs):
            await asyncio.sleep(0.050)  # 50ms
            return ["Result2", "Result3"]

        import asyncio
        mock_vertex_service.semantic_autocomplete = slow_vertex
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=test&limit=3")

        assert response.status_code == 200
        data = response.json()

        # Should still try to be under 100ms
        assert data["response_time_ms"] < 150  # Some tolerance for hybrid
        assert data["source"] == "hybrid"


# ====================
# 에러 처리 테스트
# ====================

def test_autocomplete_bigquery_error_graceful():
    """BigQuery 에러 시 graceful degradation"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # BigQuery throws error
        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            side_effect=Exception("BigQuery connection failed")
        )
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=Phil")

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


def test_autocomplete_empty_results():
    """결과가 없을 때 빈 리스트 반환"""
    with patch('app.api.autocomplete.get_bigquery_service') as mock_bq, \
         patch('app.api.autocomplete.get_vertex_service') as mock_vertex:

        # Both services return empty
        mock_bq_service = MagicMock()
        mock_bq_service.get_autocomplete_suggestions = AsyncMock(
            return_value=[]
        )
        mock_bq.return_value = mock_bq_service

        mock_vertex_service = MagicMock()
        mock_vertex_service.semantic_autocomplete = AsyncMock(
            return_value=[]
        )
        mock_vertex.return_value = mock_vertex_service

        response = client.get("/api/autocomplete?q=xyz123")

        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []
        assert data["total"] == 0
        assert data["source"] == "hybrid"  # Both were tried


# ====================
# Health Check 테스트
# ====================

def test_autocomplete_health_check():
    """헬스체크 엔드포인트"""
    response = client.get("/api/autocomplete/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "services" in data
    assert "timestamp" in data


# ====================
# Integration 테스트 (Mock 모드)
# ====================

@pytest.mark.integration
def test_autocomplete_mock_mode():
    """Mock 모드에서 전체 플로우 테스트"""
    # Set mock mode
    import os
    original = os.environ.get("ENABLE_MOCK_MODE")
    os.environ["ENABLE_MOCK_MODE"] = "true"

    try:
        # Reinitialize services in mock mode
        autocomplete.bigquery_service = None
        autocomplete.vertex_search = None

        response = client.get("/api/autocomplete?q=Phil")

        assert response.status_code == 200
        data = response.json()

        # Mock data should return preset names
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    finally:
        # Restore original setting
        if original:
            os.environ["ENABLE_MOCK_MODE"] = original
        else:
            os.environ.pop("ENABLE_MOCK_MODE", None)

        # Reset services
        autocomplete.bigquery_service = None
        autocomplete.vertex_search = None


# ====================
# Levenshtein Distance 테스트
# ====================

def test_levenshtein_distance():
    """편집 거리 계산 테스트"""
    from app.api.autocomplete import levenshtein_distance

    # Exact match
    assert levenshtein_distance("Phil Ivey", "Phil Ivey") == 0

    # 1 character difference
    assert levenshtein_distance("Phil Ivy", "Phil Ivey") == 1

    # 2 character difference
    assert levenshtein_distance("Junglman", "Junglemann") == 2

    # Different words
    assert levenshtein_distance("abc", "xyz") == 3

    # Empty string
    assert levenshtein_distance("test", "") == 4
    assert levenshtein_distance("", "test") == 4


def test_is_typo():
    """오타 판단 테스트"""
    from app.api.autocomplete import is_typo

    # Typo detected (distance = 1)
    assert is_typo("Phil Ivy", "Phil Ivey") == True
    assert is_typo("bluf", "bluff") == True

    # Typo detected (distance = 2)
    assert is_typo("Junglman", "Junglemann", max_distance=2) == True

    # Not a typo (distance too large)
    assert is_typo("abc", "xyz") == False

    # Exact match is not a typo
    assert is_typo("Phil Ivey", "Phil Ivey") == False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])