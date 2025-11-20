"""
RAG (Retrieval-Augmented Generation) API 엔드포인트
POST /api/rag
"""

from fastapi import APIRouter, HTTPException
from app.models import RAGRequest, RAGResponse, HandResult, ErrorResponse
from app.services.vertex_search import VertexSearchService
from app.services.llm_service import LLMService
from app.config import settings
import structlog
import time

router = APIRouter()
logger = structlog.get_logger()

# 서비스 초기화
vertex_search = VertexSearchService()
llm_service = LLMService()


@router.post("/rag", response_model=RAGResponse, responses={500: {"model": ErrorResponse}})
async def generate_rag_answer(request: RAGRequest) -> RAGResponse:
    """
    RAG 답변 생성 API (Qwen3-8B + Vertex AI Search)

    **기능**:
    1. Vertex AI Vector Search로 관련 핸드 검색 (top_k개)
    2. 검색 결과를 컨텍스트로 Qwen3-8B에 전달
    3. Qwen3-8B Thinking Mode로 자연어 답변 생성

    **Request Body**:
    ```json
    {
      "query": "Phil Ivey의 블러프 전략은?",
      "top_k": 5,
      "use_thinking_mode": true
    }
    ```

    **Response**:
    ```json
    {
      "query": "Phil Ivey의 블러프 전략은?",
      "answer": "Phil Ivey의 블러프 전략은...",
      "context_hands": [...],
      "total_time_ms": 2500,
      "search_time_ms": 100,
      "llm_time_ms": 2400
    }
    ```
    """
    start_time = time.time()

    try:
        logger.info(
            "rag_request",
            query=request.query,
            top_k=request.top_k,
            use_thinking_mode=request.use_thinking_mode,
        )

        # Step 1: Vertex AI 검색
        search_start = time.time()
        search_results = await vertex_search.search(
            query=request.query,
            top_k=request.top_k or settings.rag_context_hands,
            similarity_threshold=settings.search_similarity_threshold,
        )
        search_time_ms = (time.time() - search_start) * 1000

        if not search_results:
            logger.warning("rag_no_search_results", query=request.query)
            return RAGResponse(
                query=request.query,
                answer="죄송합니다. 관련된 핸드를 찾을 수 없습니다. 다른 질문을 시도해주세요.",
                context_hands=[],
                total_time_ms=(time.time() - start_time) * 1000,
                search_time_ms=search_time_ms,
                llm_time_ms=0.0,
            )

        # Step 2: 검색 결과를 HandResult 모델로 변환
        context_hands = [
            HandResult(
                hand_id=result["hand_id"],
                hero_name=result["hero_name"],
                villain_name=result.get("villain_name"),
                description=result["description"],
                pot_bb=result["pot_bb"],
                street=result["street"],
                action=result["action"],
                tournament=result.get("tournament"),
                tags=result.get("tags", []),
                video_url=result.get("video_url"),
                timestamp=result.get("timestamp"),
                distance=result.get("distance"),
            )
            for result in search_results
        ]

        # Step 3: Qwen3-8B로 답변 생성
        llm_start = time.time()
        answer = await llm_service.generate_answer(
            query=request.query,
            hands=context_hands,
            use_thinking_mode=request.use_thinking_mode,
        )
        llm_time_ms = (time.time() - llm_start) * 1000

        total_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "rag_success",
            query=request.query,
            context_hands_count=len(context_hands),
            total_time_ms=total_time_ms,
            search_time_ms=search_time_ms,
            llm_time_ms=llm_time_ms,
        )

        return RAGResponse(
            query=request.query,
            answer=answer,
            context_hands=context_hands,
            total_time_ms=total_time_ms,
            search_time_ms=search_time_ms,
            llm_time_ms=llm_time_ms,
        )

    except Exception as e:
        logger.error("rag_error", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=f"RAG 답변 생성 중 오류 발생: {str(e)}")
