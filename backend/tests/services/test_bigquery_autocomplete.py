"""
단위 테스트: BigQueryAutocompleteService
1:1 페어링: backend/app/services/bigquery.py (BigQueryAutocompleteService)

Coverage:
- 정상 케이스: 쿼리 → 결과 반환 (선수명 prefix 매칭)
- 빈도순 정렬 확인
- 최대 10개 결과 제한
- 엣지 케이스: 빈 쿼리, 결과 없음, None 값, 대소문자 구분 없음
- 에러 케이스: BigQuery 연결 실패, SQL Injection 방지

Target Coverage: 90%+
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from google.cloud import bigquery
from typing import List

from app.services.bigquery import BigQueryAutocompleteService
from app.config import settings


# ====================
# Fixtures
# ====================

@pytest.fixture
def mock_bq_client():
    """BigQuery 클라이언트 mock fixture"""
    client = Mock(spec=bigquery.Client)
    return client


@pytest.fixture
def service(mock_bq_client):
    """BigQueryAutocompleteService fixture with mock client"""
    return BigQueryAutocompleteService(client=mock_bq_client)


@pytest.fixture
def service_none_client():
    """BigQueryAutocompleteService fixture with None client (mock mode)"""
    with patch('app.services.bigquery.settings') as mock_settings:
        mock_settings.enable_mock_mode = True
        mock_settings.gcp_project = "test-project"
        mock_settings.bq_dataset = "test_dataset"
        mock_settings.bq_table_hand_summary = "hand_summary"
        return BigQueryAutocompleteService(client=None)


class MockRow:
    """Mock BigQuery Row object"""
    def __init__(self, name: str):
        self.name = name


def create_mock_query_result(names: List[str]):
    """BigQuery QueryResult mock 생성 헬퍼"""
    mock_result = MagicMock()
    mock_result.__iter__ = Mock(return_value=iter([MockRow(name) for name in names]))
    return mock_result


# ====================
# 정상 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_success(service, mock_bq_client):
    """정상 케이스: 쿼리 → 결과 반환"""
    # Arrange
    query = "Phil"
    expected_results = ["Phil Ivey", "Phil Hellmuth", "Philip Ng"]

    # Mock BigQuery query result
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query, limit=10)

    # Assert
    assert results == expected_results
    assert len(results) == 3
    mock_bq_client.query.assert_called_once()

    # Verify SQL query parameters
    call_args = mock_bq_client.query.call_args
    job_config = call_args[1]['job_config']
    assert len(job_config.query_parameters) == 2
    assert job_config.query_parameters[0].value == "Phil%"  # query_pattern
    assert job_config.query_parameters[1].value == 10  # limit


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_frequency_order(service, mock_bq_client):
    """빈도순 정렬: 많이 등장한 이름 우선 (BigQuery ORDER BY 검증)"""
    # Arrange
    query = "Tom"
    # BigQuery는 이미 빈도순으로 정렬된 결과를 반환
    expected_results = ["Tom Dwan", "Tom Marchese", "Tom-K Smith"]

    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query, limit=10)

    # Assert
    assert results == expected_results
    assert results[0] == "Tom Dwan"  # Most frequent first

    # Verify SQL contains ORDER BY total_frequency DESC
    call_args = mock_bq_client.query.call_args
    sql_query = call_args[0][0]
    assert "ORDER BY total_frequency DESC" in sql_query


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_limit(service, mock_bq_client):
    """결과 제한: 최대 10개"""
    # Arrange
    query = "Dan"
    limit = 3
    # Mock: 많은 결과가 있지만 limit=3만 반환
    expected_results = ["Daniel Negreanu", "Dan Smith", "Danny Tang"]

    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query, limit=limit)

    # Assert
    assert len(results) == 3
    assert results == expected_results

    # Verify LIMIT parameter
    call_args = mock_bq_client.query.call_args
    job_config = call_args[1]['job_config']
    assert job_config.query_parameters[1].value == limit


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_case_insensitive(service, mock_bq_client):
    """대소문자 구분 없음: "phil" == "Phil" == "PHIL" """
    # Arrange
    queries = ["phil", "Phil", "PHIL", "pHiL"]
    expected_results = ["Phil Ivey", "Phil Hellmuth"]

    for query in queries:
        # Mock
        mock_query_job = Mock()
        mock_query_job.result.return_value = create_mock_query_result(expected_results)
        mock_bq_client.query.return_value = mock_query_job

        # Act
        results = await service.get_autocomplete_suggestions(query, limit=10)

        # Assert
        assert results == expected_results, f"Failed for query: {query}"

        # Verify SQL uses LOWER() for case-insensitive matching
        call_args = mock_bq_client.query.call_args
        sql_query = call_args[0][0]
        assert "LOWER(hero_name) LIKE LOWER(@query_pattern)" in sql_query
        assert "LOWER(villain_name) LIKE LOWER(@query_pattern)" in sql_query


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_none_filtering(service, mock_bq_client):
    """None 값 필터링: NULL 이름은 결과에서 제외"""
    # Arrange
    query = "Test"
    # Mock: None 값이 섞여 있는 결과
    mock_rows = [MockRow("Test Player"), MockRow(None), MockRow("Test User")]

    mock_query_job = Mock()
    mock_result = MagicMock()
    mock_result.__iter__ = Mock(return_value=iter(mock_rows))
    mock_query_job.result.return_value = mock_result
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query, limit=10)

    # Assert
    assert None not in results
    assert results == ["Test Player", "Test User"]
    assert len(results) == 2


# ====================
# 엣지 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_empty_query(service):
    """엣지 케이스: 빈 쿼리 → ValueError"""
    # Arrange
    empty_queries = ["", " ", "  "]

    for query in empty_queries:
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.get_autocomplete_suggestions(query)

        assert "at least 2 characters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_single_char(service):
    """엣지 케이스: 1자 쿼리 → ValueError"""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await service.get_autocomplete_suggestions("P")

    assert "at least 2 characters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_no_results(service, mock_bq_client):
    """엣지 케이스: 결과 없음 → 빈 배열 반환"""
    # Arrange
    query = "xyz123notfound"

    # Mock: 빈 결과
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result([])
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert
    assert results == []
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_special_chars_cleaned(service, mock_bq_client):
    """엣지 케이스: 특수문자 제거 (영문, 숫자, 공백, 하이픈만 허용)"""
    # Arrange
    query = "Phil@#$%Ivey"
    expected_results = ["Phil Ivey"]

    # Mock
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert
    assert results == expected_results

    # Verify cleaned query (특수문자 제거됨)
    call_args = mock_bq_client.query.call_args
    job_config = call_args[1]['job_config']
    query_pattern = job_config.query_parameters[0].value
    assert query_pattern == "PhilIvey%"  # 특수문자 제거됨


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_query_too_long(service, mock_bq_client):
    """엣지 케이스: 쿼리 100자 초과 → 잘림"""
    # Arrange
    long_query = "a" * 150  # 150자
    expected_results = ["Test Player"]

    # Mock
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(long_query)

    # Assert
    assert results == expected_results

    # Verify query was truncated to 100 chars
    call_args = mock_bq_client.query.call_args
    job_config = call_args[1]['job_config']
    query_pattern = job_config.query_parameters[0].value
    cleaned_query = query_pattern.rstrip('%')
    assert len(cleaned_query) <= 100


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_only_special_chars(service):
    """엣지 케이스: 특수문자만 입력 → ValueError"""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await service.get_autocomplete_suggestions("!@#$%^&*()")

    assert "only invalid characters" in str(exc_info.value)


# ====================
# 에러 케이스 테스트
# ====================

@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_db_error_graceful(service, mock_bq_client):
    """에러 핸들링: DB 연결 실패 → 빈 배열 반환 (graceful degradation)"""
    # Arrange
    query = "Phil"

    # Mock: BigQuery connection error
    mock_bq_client.query.side_effect = Exception("Connection to BigQuery failed")

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert - graceful degradation (빈 배열 반환)
    assert results == []
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_query_timeout(service, mock_bq_client):
    """에러 핸들링: 쿼리 타임아웃 → 빈 배열 반환"""
    # Arrange
    query = "Test"

    # Mock: Timeout error
    mock_bq_client.query.side_effect = TimeoutError("Query execution timeout")

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_get_autocomplete_suggestions_sql_injection_prevented(service, mock_bq_client):
    """SQL Injection 방지: 파라미터화된 쿼리 사용"""
    # Arrange
    malicious_queries = [
        "Phil'; DROP TABLE hands; --",
        "Phil' OR '1'='1",
        "Phil'; DELETE FROM hands WHERE '1'='1",
        "Phil' UNION SELECT * FROM users--"
    ]

    expected_results = ["Phil Ivey"]

    for malicious_query in malicious_queries:
        # Mock
        mock_query_job = Mock()
        mock_query_job.result.return_value = create_mock_query_result(expected_results)
        mock_bq_client.query.return_value = mock_query_job

        # Act - should not raise error
        results = await service.get_autocomplete_suggestions(malicious_query)

        # Assert - 특수문자가 제거되어 안전하게 처리됨
        assert isinstance(results, list)

        # Verify parameterized query was used
        call_args = mock_bq_client.query.call_args
        job_config = call_args[1]['job_config']

        # 파라미터화된 쿼리 사용 확인
        assert job_config is not None
        assert hasattr(job_config, 'query_parameters')
        assert len(job_config.query_parameters) == 2

        # SQL 문자열에 직접 값이 삽입되지 않았는지 확인
        sql_query = call_args[0][0]
        assert "@query_pattern" in sql_query  # 플레이스홀더 사용
        assert "DROP TABLE" not in sql_query
        assert "DELETE FROM" not in sql_query


# ====================
# Mock 모드 테스트
# ====================

@pytest.mark.asyncio
async def test_mock_autocomplete_success(service_none_client):
    """Mock 모드: 정상 동작 (client=None)"""
    # Act
    results = await service_none_client.get_autocomplete_suggestions("Phil", limit=5)

    # Assert - Mock 데이터 반환
    assert isinstance(results, list)
    assert len(results) <= 5
    # Mock data includes "Phil Ivey", "Phil Hellmuth", "Philip Ng"
    assert any("Phil" in name for name in results)


@pytest.mark.asyncio
async def test_mock_autocomplete_empty_results(service_none_client):
    """Mock 모드: 결과 없음"""
    # Act - Mock 데이터에 없는 이름
    results = await service_none_client.get_autocomplete_suggestions("xyz123", limit=5)

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_mock_autocomplete_case_insensitive(service_none_client):
    """Mock 모드: 대소문자 구분 없음"""
    # Arrange
    queries = ["phil", "PHIL", "Phil"]

    for query in queries:
        # Act
        results = await service_none_client.get_autocomplete_suggestions(query, limit=5)

        # Assert - 모두 동일한 결과
        assert isinstance(results, list)
        assert len(results) > 0


@pytest.mark.asyncio
async def test_mock_autocomplete_limit_respected(service_none_client):
    """Mock 모드: limit 적용 확인"""
    # Act - Use 2+ character queries
    results_limit_3 = await service_none_client.get_autocomplete_suggestions("Da", limit=3)
    results_limit_10 = await service_none_client.get_autocomplete_suggestions("Da", limit=10)

    # Assert
    assert len(results_limit_3) <= 3
    assert len(results_limit_10) <= 10
    assert len(results_limit_3) <= len(results_limit_10)


# ====================
# _validate_query 메서드 테스트
# ====================

def test_validate_query_success(service):
    """정상 케이스: 유효한 쿼리"""
    # Arrange
    valid_queries = [
        "Phil",
        "Phil Ivey",
        "Tom-Dwan",
        "Daniel123",
        "AB"  # 2자 (최소)
    ]

    for query in valid_queries:
        # Act
        cleaned = service._validate_query(query)

        # Assert
        assert isinstance(cleaned, str)
        assert len(cleaned) >= 2


def test_validate_query_empty_raises_error(service):
    """에러: 빈 쿼리"""
    with pytest.raises(ValueError) as exc_info:
        service._validate_query("")

    assert "at least 2 characters" in str(exc_info.value)


def test_validate_query_too_short(service):
    """에러: 1자 쿼리"""
    with pytest.raises(ValueError):
        service._validate_query("P")


def test_validate_query_only_special_chars(service):
    """에러: 특수문자만"""
    with pytest.raises(ValueError) as exc_info:
        service._validate_query("!@#$")

    assert "only invalid characters" in str(exc_info.value)


def test_validate_query_removes_special_chars(service):
    """특수문자 제거"""
    # Arrange
    query = "Phil@#$%Ivey<script>alert('xss')</script>"

    # Act
    cleaned = service._validate_query(query)

    # Assert
    assert cleaned == "PhilIveyscriptalertxssscript"
    assert "@" not in cleaned
    assert "<" not in cleaned
    assert ">" not in cleaned


def test_validate_query_preserves_valid_chars(service):
    """유효 문자 보존 (영문, 숫자, 공백, 하이픈)"""
    # Arrange
    query = "Tom-Dwan 123"

    # Act
    cleaned = service._validate_query(query)

    # Assert
    assert cleaned == "Tom-Dwan 123"


def test_validate_query_truncates_long_query(service):
    """100자 초과 → 잘림"""
    # Arrange
    long_query = "a" * 150

    # Act
    cleaned = service._validate_query(long_query)

    # Assert
    assert len(cleaned) == 100


def test_validate_query_strips_whitespace(service):
    """공백 제거 (앞뒤)"""
    # Arrange
    query = "  Phil Ivey  "

    # Act
    cleaned = service._validate_query(query)

    # Assert
    assert cleaned == "Phil Ivey"
    assert not cleaned.startswith(" ")
    assert not cleaned.endswith(" ")


# ====================
# 통합 시나리오 테스트
# ====================

@pytest.mark.asyncio
async def test_real_world_scenario_prefix_matching(service, mock_bq_client):
    """실제 시나리오: "Jun" → "Junglemann", "Jun Hwan Lee" 등"""
    # Arrange
    query = "Jun"
    # All results should start with "Jun"
    expected_results = [
        "Junglemann",
        "Jun Hwan Lee",
        "Jungle Boy"
    ]

    # Mock
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert
    assert results == expected_results
    # Verify all results start with "Jun" (case-insensitive)
    for name in results:
        # Either the full name starts with "Jun" or the first word does
        assert name.lower().startswith(query.lower()) or \
               name.split()[0].lower().startswith(query.lower())


@pytest.mark.asyncio
async def test_real_world_scenario_hyphenated_names(service, mock_bq_client):
    """실제 시나리오: 하이픈 포함 이름 (Tom-Dwan 스타일)"""
    # Arrange
    query = "Tom-"
    expected_results = ["Tom-Dwan", "Tom-K Smith"]

    # Mock
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert
    assert results == expected_results


@pytest.mark.asyncio
async def test_real_world_scenario_typo_resilience(service, mock_bq_client):
    """실제 시나리오: 오타 입력 처리 (특수문자 정제)"""
    # Arrange - 사용자가 오타로 특수문자 입력
    query = "Ph!l Iv3y"
    # 정제 후: "Phl Iv3y" (숫자는 보존, 특수문자 제거)
    expected_results = []  # 매칭 없을 수 있음

    # Mock
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(expected_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert - 에러 없이 처리됨
    assert isinstance(results, list)


# ====================
# Performance & Edge Cases
# ====================

@pytest.mark.asyncio
async def test_autocomplete_with_unicode_chars(service):
    """엣지 케이스: 유니코드 문자 (한글 등) → 제거됨"""
    # Arrange
    query = "Phil한글Ivey"

    # Act - ValueError 또는 정제됨
    try:
        with patch.object(service, 'client') as mock_client:
            mock_query_job = Mock()
            mock_query_job.result.return_value = create_mock_query_result(["Phil Ivey"])
            mock_client.query.return_value = mock_query_job

            results = await service.get_autocomplete_suggestions(query)

            # Assert - 한글 제거됨
            assert isinstance(results, list)
    except ValueError:
        # 모두 제거되어 유효하지 않은 경우
        pass


@pytest.mark.asyncio
async def test_autocomplete_duplicate_names_in_result(service, mock_bq_client):
    """엣지 케이스: BigQuery 결과에 중복 이름 (GROUP BY로 방지되어야 함)"""
    # Arrange
    query = "Phil"
    # BigQuery는 GROUP BY로 중복 제거해야 하지만, 만약 중복이 있다면?
    raw_results = ["Phil Ivey", "Phil Ivey", "Phil Hellmuth"]

    # Mock
    mock_query_job = Mock()
    mock_query_job.result.return_value = create_mock_query_result(raw_results)
    mock_bq_client.query.return_value = mock_query_job

    # Act
    results = await service.get_autocomplete_suggestions(query)

    # Assert - 중복 포함 (BigQuery의 GROUP BY 책임)
    # 여기서는 BigQuery 결과를 그대로 반환하는지 확인
    assert results == raw_results


# ====================
# Constructor 테스트
# ====================

def test_constructor_with_client():
    """생성자: 클라이언트 주입"""
    mock_client = Mock(spec=bigquery.Client)
    service = BigQueryAutocompleteService(client=mock_client)

    assert service.client == mock_client


def test_constructor_without_client_mock_mode():
    """생성자: client=None, mock_mode=True"""
    with patch('app.services.bigquery.settings') as mock_settings:
        mock_settings.enable_mock_mode = True

        service = BigQueryAutocompleteService(client=None)

        assert service.client is None


@patch('app.services.bigquery.bigquery.Client')
def test_constructor_without_client_real_mode(mock_client_class):
    """생성자: client=None, mock_mode=False → 실제 클라이언트 생성"""
    with patch('app.services.bigquery.settings') as mock_settings:
        mock_settings.enable_mock_mode = False
        mock_settings.gcp_project = "test-project"
        mock_settings.bq_dataset = "test_dataset"
        mock_settings.bq_table_hand_summary = "hand_summary"

        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        service = BigQueryAutocompleteService(client=None)

        assert service.client == mock_client_instance
        mock_client_class.assert_called_once_with(project="test-project")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--cov=app.services.bigquery", "--cov-report=term-missing"])
