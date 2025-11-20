"""
Autocomplete API 엔드포인트
GET /api/autocomplete?q={query}&limit={limit}

Architecture:
- Tier 1: BigQuery prefix matching (fast, <10ms)
- Tier 2: Vertex AI semantic search (fallback, <100ms)
- Rate limiting: 100 requests/min per IP
- Typo correction: Levenshtein distance ≤2
"""

from fastapi import APIRouter, Query, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.models import ErrorResponse
from app.config import settings
import structlog
import time
import re
from typing import List, Optional, Literal, Dict
from collections import defaultdict
from datetime import datetime, timedelta

# Import actual services
from app.services.bigquery import BigQueryAutocompleteService
from app.services.vertex_search import VertexSearchService

router = APIRouter()
logger = structlog.get_logger()

# Initialize services (singleton instances)
bigquery_service: Optional[BigQueryAutocompleteService] = None
vertex_search: Optional[VertexSearchService] = None

# Rate limiting storage (in-memory, replace with Redis in production)
rate_limit_storage: Dict[str, List[datetime]] = defaultdict(list)
RATE_LIMIT_PER_MINUTE = 100
RATE_LIMIT_WINDOW = timedelta(minutes=1)


# ====================
# Pydantic Models
# ====================

from pydantic import BaseModel, Field, field_validator


class AutocompleteRequest(BaseModel):
    """자동완성 요청 모델"""

    query: str = Field(
        ...,
        description="검색 쿼리",
        min_length=2,
        max_length=100,
        examples=["Phil Ivy", "river", "Junglman"]
    )
    limit: int = Field(
        5,
        description="최대 추천 개수",
        ge=1,
        le=10
    )

    @field_validator('query')
    @classmethod
    def validate_query_pattern(cls, v: str) -> str:
        """
        쿼리 입력 검증
        - 허용 문자: 영문, 숫자, 공백, 하이픈
        - SQL Injection, XSS 방지
        """
        # 허용 문자 패턴
        pattern = re.compile(r'^[a-zA-Z0-9\s\-]+$')

        if not pattern.match(v):
            raise ValueError(
                "Query contains invalid characters. "
                "Only alphanumeric, spaces, and hyphens are allowed."
            )

        # 추가 검증: SQL 키워드 차단
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION']
        upper_query = v.upper()
        for keyword in sql_keywords:
            if keyword in upper_query:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        return v


class AutocompleteResponse(BaseModel):
    """자동완성 응답 모델"""

    suggestions: List[str] = Field(
        ...,
        description="추천 결과 목록",
        max_length=10,
        examples=[["Phil Ivey", "Phil Hellmuth", "Philip Ng"]]
    )
    query: str = Field(
        ...,
        description="원본 쿼리",
        examples=["Phil Ivy"]
    )
    source: Literal["bigquery_cache", "vertex_ai", "hybrid"] = Field(
        ...,
        description="데이터 소스 (bigquery_cache: 빠른 캐시, vertex_semantic: 의미론적 검색)"
    )
    response_time_ms: float = Field(
        ...,
        description="응답 시간 (밀리초)",
        examples=[45.2]
    )
    total: int = Field(
        ...,
        description="총 추천 개수",
        examples=[3]
    )


# ====================
# Rate Limiting Helper
# ====================

async def check_rate_limit(client_ip: str) -> int:
    """
    Rate limiting 체크 (100 requests/minute per IP)

    Args:
        client_ip: 클라이언트 IP 주소

    Returns:
        remaining: 남은 요청 수

    Raises:
        HTTPException: Rate limit 초과 시 429 에러
    """
    now = datetime.now()

    # 현재 IP의 요청 기록 가져오기
    requests = rate_limit_storage[client_ip]

    # 1분 이전 요청들 제거
    requests[:] = [req_time for req_time in requests
                   if now - req_time < RATE_LIMIT_WINDOW]

    # Rate limit 체크
    if len(requests) >= RATE_LIMIT_PER_MINUTE:
        logger.warning(
            "rate_limit_exceeded",
            client_ip=client_ip,
            requests_count=len(requests)
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {RATE_LIMIT_PER_MINUTE} requests per minute",
                "query": None
            }
        )

    # 현재 요청 기록
    requests.append(now)
    remaining = RATE_LIMIT_PER_MINUTE - len(requests)

    return remaining


def get_client_ip(request: Request) -> str:
    """
    클라이언트 IP 추출
    - X-Forwarded-For 헤더 우선
    - 프록시 환경 대응
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ====================
# Service Dependency Injection
# ====================

def get_bigquery_service() -> BigQueryAutocompleteService:
    """BigQuery 서비스 싱글톤 인스턴스 반환"""
    global bigquery_service
    if bigquery_service is None:
        bigquery_service = BigQueryAutocompleteService()
    return bigquery_service


def get_vertex_service() -> VertexSearchService:
    """Vertex Search 서비스 싱글톤 인스턴스 반환"""
    global vertex_search
    if vertex_search is None:
        vertex_search = VertexSearchService()
    return vertex_search


# ====================
# Typo Correction Helper
# ====================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Levenshtein distance 계산 (편집 거리)

    Args:
        s1: 첫 번째 문자열
        s2: 두 번째 문자열

    Returns:
        편집 거리 (0 = 동일, 1 = 1글자 차이, ...)

    Examples:
        >>> levenshtein_distance("Phil Ivy", "Phil Ivey")
        1
        >>> levenshtein_distance("Junglman", "Junglemann")
        2

    TODO: Phase 1 구현
    - python-Levenshtein 라이브러리 사용 권장
    - 또는 아래 알고리즘 구현
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 삽입, 삭제, 교체 비용
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def is_typo(query: str, suggestion: str, max_distance: int = 2) -> bool:
    """
    오타 여부 판단

    Args:
        query: 사용자 입력
        suggestion: 추천 단어
        max_distance: 최대 허용 편집 거리

    Returns:
        True if typo detected (distance <= max_distance)

    Examples:
        >>> is_typo("Phil Ivy", "Phil Ivey")
        True  # distance = 1
        >>> is_typo("bluf", "bluff")
        True  # distance = 1
        >>> is_typo("abc", "xyz")
        False  # distance = 3
    """
    distance = levenshtein_distance(query.lower(), suggestion.lower())
    return distance <= max_distance and distance > 0


# ====================
# API Endpoint
# ====================

@router.get(
    "/autocomplete",
    response_model=AutocompleteResponse,
    responses={
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get autocomplete suggestions",
    description="""
    Smart autocomplete with AI-powered typo correction.

    **Features**:
    - Typo correction (Levenshtein distance ≤2)
    - Fast BigQuery cache (<10ms)
    - Semantic fallback with Vertex AI (<100ms)
    - Rate limiting: 100 requests/min per IP

    **Examples**:
    - `Phil Ivy` → `["Phil Ivey", "Phil Hellmuth", ...]`
    - `Junglman` → `["Junglemann"]` (typo correction)
    - `river` → `["river call", "river bluff", ...]`
    """,
    tags=["Autocomplete"]
)
async def autocomplete_suggestions(
    request: Request,
    q: str = Query(
        ...,
        description="검색 쿼리 (최소 2자, 최대 100자)",
        min_length=2,
        max_length=100,
        example="Phil Ivy"
    ),
    limit: int = Query(
        5,
        description="최대 추천 개수",
        ge=1,
        le=10
    ),
    bq_service: BigQueryAutocompleteService = Depends(get_bigquery_service),
    vertex_service: VertexSearchService = Depends(get_vertex_service)
) -> AutocompleteResponse:
    """
    자동완성 API 메인 엔드포인트

    Flow:
    1. Input validation (Pydantic)
    2. Rate limit check (TODO)
    3. BigQuery prefix search (Tier 1 - fast)
    4. If <3 results, fallback to Vertex AI (Tier 2 - semantic)
    5. Return suggestions with metadata

    Args:
        request: FastAPI Request (for IP extraction)
        q: Search query
        limit: Max suggestions

    Returns:
        AutocompleteResponse with suggestions

    Raises:
        HTTPException:
            - 422: Validation error (query too short/long, invalid chars)
            - 429: Rate limit exceeded
            - 500: Internal server error
    """
    start_time = time.time()
    client_ip = get_client_ip(request)

    try:
        # 1. Input validation (already done by Pydantic)
        autocomplete_req = AutocompleteRequest(query=q, limit=limit)

        logger.info(
            "autocomplete_request",
            query=autocomplete_req.query,
            limit=autocomplete_req.limit,
            client_ip=client_ip
        )

        # 2. Rate limit check
        remaining = await check_rate_limit(client_ip)

        # 3. BigQuery prefix search (Tier 1)
        suggestions = await bq_service.get_autocomplete_suggestions(
            query=autocomplete_req.query,
            limit=autocomplete_req.limit
        )

        source = "bigquery_cache"

        # 4. Fallback to Vertex AI if insufficient results
        if len(suggestions) < 3:
            logger.info(
                "bigquery_insufficient_results",
                query=autocomplete_req.query,
                count=len(suggestions),
                fallback="vertex_semantic"
            )

            # Use Vertex AI service for semantic search
            vertex_suggestions = await vertex_service.semantic_autocomplete(
                query=autocomplete_req.query,
                limit=autocomplete_req.limit,
                similarity_threshold=settings.search_similarity_threshold
            )

            # Merge results (BigQuery + Vertex AI)
            suggestions.extend(vertex_suggestions)

            # Remove duplicates, preserve order
            seen = set()
            unique_suggestions = []
            for s in suggestions:
                if s not in seen:
                    seen.add(s)
                    unique_suggestions.append(s)

            suggestions = unique_suggestions[:autocomplete_req.limit]
            source = "hybrid"  # Both BigQuery and Vertex AI were used

        # 5. Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "autocomplete_success",
            query=autocomplete_req.query,
            total=len(suggestions),
            source=source,
            response_time_ms=response_time_ms
        )

        # 6. Return response
        return AutocompleteResponse(
            suggestions=suggestions,
            query=autocomplete_req.query,
            source=source,
            response_time_ms=response_time_ms,
            total=len(suggestions)
        )

    except ValueError as e:
        # Pydantic validation errors
        logger.error(
            "autocomplete_validation_error",
            query=q,
            error=str(e)
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": {
                    "query": q,
                    "min_length": 2,
                    "max_length": 100
                }
            }
        )

    except Exception as e:
        # Unexpected errors
        logger.error(
            "autocomplete_error",
            query=q,
            error=str(e),
            client_ip=client_ip
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "Failed to fetch autocomplete suggestions",
                "details": {
                    "error_id": f"autocomplete_{int(time.time())}",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            }
        )


# ====================
# Health Check (Optional)
# ====================

@router.get(
    "/autocomplete/health",
    tags=["Autocomplete"],
    summary="Autocomplete service health check"
)
async def autocomplete_health():
    """
    자동완성 서비스 헬스 체크

    Checks:
    - BigQuery connection
    - Vertex AI connection
    - Rate limiter state
    """
    # TODO: Phase 1 - Implement health checks
    return {
        "status": "healthy",
        "services": {
            "bigquery": "not_implemented",
            "vertex_ai": "not_implemented",
            "rate_limiter": "not_implemented"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
