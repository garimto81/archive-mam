"""
Qwen3-8B LLM 서비스
OpenAI API 호환 클라이언트로 Ollama 또는 Hugging Face Endpoint 연동
"""

from openai import AsyncOpenAI
from app.config import settings
from app.models import HandResult
import structlog

logger = structlog.get_logger()


class LLMService:
    """Qwen3-8B LLM 서비스 (Thinking Mode 지원)"""

    def __init__(self):
        """OpenAI 호환 클라이언트 초기화"""
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout,
        )
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        logger.info(
            "llm_service_initialized",
            provider=settings.llm_provider,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        )

    async def generate_answer(
        self, query: str, hands: list[HandResult], use_thinking_mode: bool = True
    ) -> str:
        """
        RAG 답변 생성

        Args:
            query: 사용자 질문
            hands: 검색된 핸드 리스트 (컨텍스트)
            use_thinking_mode: Qwen3 Thinking Mode 사용 여부

        Returns:
            LLM이 생성한 답변 (한국어)
        """
        # 1. 컨텍스트 생성 (검색된 핸드들을 텍스트로 포맷팅)
        context = self._format_hands(hands)

        # 2. 프롬프트 생성 (한국어/영어 템플릿 선택 가능)
        prompt = self._build_prompt(query, context)

        # 3. Qwen3-8B API 호출
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                extra_body={"thinking": use_thinking_mode},  # Qwen3 Thinking Mode
            )

            answer = response.choices[0].message.content

            logger.info(
                "llm_generation_success",
                query=query[:50],
                answer_length=len(answer),
                thinking_mode=use_thinking_mode,
            )

            return answer

        except Exception as e:
            logger.error("llm_generation_error", error=str(e), query=query[:50])
            raise

    def _format_hands(self, hands: list[HandResult]) -> str:
        """핸드 리스트를 LLM 컨텍스트용 텍스트로 변환"""
        if not hands:
            return "검색 결과가 없습니다."

        context_parts = []
        for i, hand in enumerate(hands[:settings.rag_context_hands], 1):
            hand_text = f"""
핸드 {i}:
- ID: {hand.hand_id}
- 설명: {hand.description}
- Hero: {hand.hero_name}
{f"- Villain: {hand.villain_name}" if hand.villain_name else ""}
- Pot: {hand.pot_bb} BB
- Street: {hand.street}
- Action: {hand.action}
{f"- Tournament: {hand.tournament}" if hand.tournament else ""}
{f"- Tags: {', '.join(hand.tags)}" if hand.tags else ""}
---
"""
            context_parts.append(hand_text.strip())

        return "\n\n".join(context_parts)

    def _build_prompt(self, query: str, context: str) -> str:
        """RAG 프롬프트 생성 (한국어 템플릿)"""
        if settings.rag_prompt_template == "korean":
            prompt = f"""당신은 포커 전문가입니다. 사용자의 질문에 검색된 포커 핸드 데이터를 기반으로 답변하세요.

사용자 질문: {query}

검색된 포커 핸드:
{context}

답변 요구사항:
1. 질문과 가장 관련 있는 핸드들을 선별하여 설명
2. 각 핸드의 주요 특징 및 전략적 의미 분석
3. 공통 패턴이 있다면 강조
4. 구체적인 수치와 함께 설명 (Pot Size, BB 등)
5. 간결하고 명확하게 작성 (최대 400단어)

답변:"""
        else:  # english
            prompt = f"""You are a poker expert. Answer the user's question based on the retrieved poker hands.

User Question: {query}

Retrieved Poker Hands:
{context}

Requirements:
1. Select and explain the most relevant hands to the question
2. Analyze key features and strategic implications of each hand
3. Highlight common patterns if any
4. Provide specific numbers (Pot Size, BB, etc.)
5. Be concise and clear (max 400 words)

Answer:"""

        return prompt


# 싱글톤 인스턴스 (선택)
_llm_service_instance = None


def get_llm_service() -> LLMService:
    """LLMService 싱글톤 인스턴스 반환"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
