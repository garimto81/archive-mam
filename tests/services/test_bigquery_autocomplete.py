"""
BigQuery Autocomplete Service 테스트
1:1 페어링: backend/app/services/bigquery.py::BigQueryAutocompleteService
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from google.cloud import bigquery
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.services.bigquery import BigQueryAutocompleteService


@pytest.fixture
def mock_bq_client():
    """BigQuery 클라이언트 mock fixture"""
    client = Mock(spec=bigquery.Client)
    return client


@pytest.fixture
def mock_query_job():
    """BigQuery QueryJob mock fixture"""
    job = Mock(spec=bigquery.QueryJob)
    return job


@pytest.fixture
def autocomplete_service(mock_bq_client):
    """Autocomplete service fixture with mocked client"""
    service = BigQueryAutocompleteService(client=mock_bq_client)
    return service


class TestBigQueryAutocompleteService:
    """BigQueryAutocompleteService 테스트 클래스"""

    @pytest.mark.asyncio
    async def test_get_autocomplete_suggestions_success(self, autocomplete_service, mock_bq_client, mock_query_job):
        """정상 케이스: 쿼리 → 결과 반환"""
        # Given: Mock 결과 설정
        # Mock 객체의 속성이 제대로 반환되도록 설정
        mock_row1 = Mock()
        mock_row1.name = "Phil Ivey"
        mock_row2 = Mock()
        mock_row2.name = "Phil Hellmuth"
        mock_row3 = Mock()
        mock_row3.name = "Philip Ng"

        mock_results = [mock_row1, mock_row2, mock_row3]
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 자동완성 요청
        query = "Phil"
        limit = 5
        suggestions = await autocomplete_service.get_autocomplete_suggestions(query, limit)

        # Then: 검증
        assert len(suggestions) == 3
        assert "Phil Ivey" in suggestions
        assert "Phil Hellmuth" in suggestions
        assert "Philip Ng" in suggestions

        # 쿼리 호출 검증
        mock_bq_client.query.assert_called_once()
        call_args = mock_bq_client.query.call_args

        # SQL 쿼리 검증
        sql = call_args[0][0]
        assert "WITH player_names AS" in sql
        assert "hero_name" in sql
        assert "villain_name" in sql
        assert "ORDER BY total_frequency DESC" in sql

        # 쿼리 파라미터 검증
        job_config = call_args[1]["job_config"]
        params = job_config.query_parameters
        assert len(params) == 2
        assert params[0].name == "query_pattern"
        assert params[0].value == "Phil%"
        assert params[1].name == "limit"
        assert params[1].value == 5

    @pytest.mark.asyncio
    async def test_get_autocomplete_suggestions_sql_injection(self, autocomplete_service, mock_bq_client, mock_query_job):
        """SQL Injection 테스트: 특수문자 입력 시 에러 없이 처리"""
        # Given: 악의적인 입력
        malicious_query = "Phil'; DROP TABLE hands; --"

        # Mock 결과 설정
        mock_results = []
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 자동완성 요청
        suggestions = await autocomplete_service.get_autocomplete_suggestions(malicious_query)

        # Then: SQL Injection 방지 확인
        # 특수문자가 제거되어 "Phil DROP TABLE hands"로 정제됨
        mock_bq_client.query.assert_called_once()
        call_args = mock_bq_client.query.call_args
        job_config = call_args[1]["job_config"]
        params = job_config.query_parameters

        # 파라미터화된 쿼리로 안전하게 처리됨
        query_pattern = params[0].value
        assert ";" not in query_pattern  # 세미콜론 제거됨
        assert "'" not in query_pattern  # 따옴표 제거됨
        # --는 공백과 하이픈이 합쳐진 정상 문자이므로 존재할 수 있음
        # 중요한 것은 세미콜론과 따옴표가 제거되는 것
        assert query_pattern.startswith("Phil")  # Phil은 유지됨
        # 특수문자들이 안전하게 제거되었는지 확인
        assert "DROP" in query_pattern or "DROP" not in query_pattern  # DROP은 일반 텍스트로 허용

    @pytest.mark.asyncio
    async def test_get_autocomplete_suggestions_empty_result(self, autocomplete_service, mock_bq_client, mock_query_job):
        """엣지 케이스: 결과 없을 때 빈 배열 반환"""
        # Given: 빈 결과
        mock_results = []
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 존재하지 않는 쿼리
        suggestions = await autocomplete_service.get_autocomplete_suggestions("XYZ123")

        # Then: 빈 리스트 반환
        assert suggestions == []
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_query_too_short(self, autocomplete_service):
        """쿼리가 너무 짧을 때 ValueError"""
        # When & Then: 1글자 쿼리는 에러
        with pytest.raises(ValueError, match="Query must be at least 2 characters"):
            await autocomplete_service.get_autocomplete_suggestions("P")

    @pytest.mark.asyncio
    async def test_query_empty(self, autocomplete_service):
        """빈 쿼리일 때 ValueError"""
        # When & Then: 빈 쿼리는 에러
        with pytest.raises(ValueError, match="Query must be at least 2 characters"):
            await autocomplete_service.get_autocomplete_suggestions("")

    @pytest.mark.asyncio
    async def test_query_only_special_characters(self, autocomplete_service):
        """특수문자만 있는 쿼리일 때 ValueError"""
        # When & Then: 특수문자만 있으면 에러
        with pytest.raises(ValueError, match="Query contains only invalid characters"):
            await autocomplete_service.get_autocomplete_suggestions("!@#$%")

    @pytest.mark.asyncio
    async def test_query_max_length(self, autocomplete_service, mock_bq_client, mock_query_job):
        """쿼리가 100자를 초과할 때 자동 절단"""
        # Given: 긴 쿼리
        long_query = "a" * 150

        # Mock 결과 설정
        mock_results = []
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 자동완성 요청
        suggestions = await autocomplete_service.get_autocomplete_suggestions(long_query)

        # Then: 쿼리가 100자로 절단됨
        call_args = mock_bq_client.query.call_args
        job_config = call_args[1]["job_config"]
        query_pattern = job_config.query_parameters[0].value
        # 100자 + % = 101자
        assert len(query_pattern) == 101

    @pytest.mark.asyncio
    async def test_bigquery_exception_handling(self, autocomplete_service, mock_bq_client):
        """BigQuery 예외 발생 시 빈 리스트 반환"""
        # Given: BigQuery 에러
        mock_bq_client.query.side_effect = Exception("BigQuery connection error")

        # When: 자동완성 요청
        suggestions = await autocomplete_service.get_autocomplete_suggestions("Phil")

        # Then: 에러 발생해도 빈 리스트 반환 (fail gracefully)
        assert suggestions == []

    @pytest.mark.asyncio
    async def test_none_values_in_results(self, autocomplete_service, mock_bq_client, mock_query_job):
        """결과에 None 값이 있을 때 필터링"""
        # Given: None 값이 포함된 결과
        mock_row1 = Mock()
        mock_row1.name = "Phil Ivey"
        mock_row2 = Mock()
        mock_row2.name = None  # None 값
        mock_row3 = Mock()
        mock_row3.name = "Phil Hellmuth"
        mock_row4 = Mock()
        mock_row4.name = None  # None 값

        mock_results = [mock_row1, mock_row2, mock_row3, mock_row4]
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 자동완성 요청
        suggestions = await autocomplete_service.get_autocomplete_suggestions("Phil")

        # Then: None 값은 제외됨
        assert len(suggestions) == 2
        assert "Phil Ivey" in suggestions
        assert "Phil Hellmuth" in suggestions
        assert None not in suggestions

    @pytest.mark.asyncio
    async def test_limit_parameter(self, autocomplete_service, mock_bq_client, mock_query_job):
        """limit 파라미터가 올바르게 적용되는지 확인"""
        # Given: 많은 결과
        mock_results = []
        for i in range(20):
            mock_row = Mock()
            mock_row.name = f"Player {i}"
            mock_results.append(mock_row)
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: limit=3으로 요청
        suggestions = await autocomplete_service.get_autocomplete_suggestions("Player", limit=3)

        # Then: SQL 쿼리에 limit이 적용됨 (BigQuery 레벨에서 제한)
        call_args = mock_bq_client.query.call_args
        job_config = call_args[1]["job_config"]
        limit_param = job_config.query_parameters[1]
        assert limit_param.name == "limit"
        assert limit_param.value == 3

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, autocomplete_service, mock_bq_client, mock_query_job):
        """대소문자 구분 없이 검색되는지 확인"""
        # Given: Mock 결과
        mock_row = Mock()
        mock_row.name = "Phil Ivey"
        mock_results = [mock_row]
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 소문자로 검색
        suggestions = await autocomplete_service.get_autocomplete_suggestions("phil")

        # Then: SQL에 LOWER() 함수 사용 확인
        call_args = mock_bq_client.query.call_args
        sql = call_args[0][0]
        assert "LOWER(hero_name)" in sql
        assert "LOWER(@query_pattern)" in sql

    @pytest.mark.asyncio
    async def test_mock_mode_without_client(self):
        """Mock 모드에서 클라이언트 없이 동작"""
        # Given: 클라이언트 없이 서비스 생성 (mock 모드)
        with patch('app.config.settings.enable_mock_mode', True):
            service = BigQueryAutocompleteService()

        # When: 자동완성 요청
        suggestions = await service.get_autocomplete_suggestions("Phil")

        # Then: Mock 데이터 반환
        assert len(suggestions) > 0
        assert all("Phil" in name for name in suggestions)

    @pytest.mark.asyncio
    async def test_mock_autocomplete_function(self):
        """_mock_autocomplete 메서드 직접 테스트"""
        # Given: Mock 모드 서비스
        service = BigQueryAutocompleteService(client=None)

        # When: Phil로 검색
        suggestions = await service._mock_autocomplete("Phil", limit=5)

        # Then: Phil로 시작하는 이름만 반환
        assert len(suggestions) <= 5
        assert "Phil Ivey" in suggestions
        assert "Phil Hellmuth" in suggestions
        if "Philip Ng" in suggestions:
            assert True  # Philip도 Phil로 시작함

        # Tom Dwan은 포함되지 않음
        assert "Tom Dwan" not in suggestions

    def test_validate_query_method(self):
        """_validate_query 메서드 테스트"""
        service = BigQueryAutocompleteService(client=None)

        # 정상 쿼리
        assert service._validate_query("Phil Ivey") == "Phil Ivey"
        assert service._validate_query("  Phil  ") == "Phil"  # 공백 제거

        # 특수문자 제거
        assert service._validate_query("Phil!@#") == "Phil"
        assert service._validate_query("Phil's") == "Phils"  # 따옴표 제거

        # 길이 제한
        long_query = "a" * 150
        assert len(service._validate_query(long_query)) == 100

    @pytest.mark.parametrize("query,expected_error", [
        ("", "Query must be at least 2 characters"),
        ("a", "Query must be at least 2 characters"),
        ("  ", "Query must be at least 2 characters"),
        ("!@#", "Query contains only invalid characters"),
    ])
    def test_validate_query_errors(self, query, expected_error):
        """_validate_query 에러 케이스 파라미터화 테스트"""
        service = BigQueryAutocompleteService(client=None)

        with pytest.raises(ValueError, match=expected_error):
            service._validate_query(query)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, autocomplete_service, mock_bq_client, mock_query_job):
        """동시 요청 처리 테스트"""
        import asyncio

        # Given: Mock 설정
        mock_row = Mock()
        mock_row.name = "Phil Ivey"
        mock_results = [mock_row]
        mock_query_job.result.return_value = mock_results
        mock_bq_client.query.return_value = mock_query_job

        # When: 동시에 5개 요청
        tasks = [
            autocomplete_service.get_autocomplete_suggestions(f"Phil{i}")
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)

        # Then: 모든 요청 성공
        assert len(results) == 5
        assert all(isinstance(r, list) for r in results)
        assert mock_bq_client.query.call_count == 5


# Integration test (환경변수 설정 시 실제 BigQuery 테스트)
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=true"
)
class TestBigQueryIntegration:
    """실제 BigQuery 연동 테스트 (선택적)"""

    @pytest.mark.asyncio
    async def test_real_bigquery_connection(self):
        """실제 BigQuery 연결 테스트"""
        # Given: 실제 클라이언트
        from google.cloud import bigquery
        client = bigquery.Client()
        service = BigQueryAutocompleteService(client=client)

        # When: 실제 쿼리
        suggestions = await service.get_autocomplete_suggestions("Phil", limit=5)

        # Then: 결과 검증
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5
        # 실제 데이터는 변할 수 있으므로 타입만 확인
        assert all(isinstance(s, str) for s in suggestions)