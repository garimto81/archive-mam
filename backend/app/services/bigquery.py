"""
BigQuery 서비스
핸드 상세 정보 조회 및 자동완성
"""

from google.cloud import bigquery
from typing import List, Optional
from app.config import settings
from app.models import HandDetail
import structlog
import json
import os
import re

logger = structlog.get_logger()


class BigQueryService:
    """BigQuery 서비스"""

    def __init__(self):
        """BigQuery 클라이언트 초기화"""
        if settings.enable_mock_mode:
            logger.info("bigquery_mock_mode_enabled")
            self.mock_mode = True
            self.client = None
        else:
            self.mock_mode = False
            self.client = bigquery.Client(project=settings.gcp_project)
            logger.info(
                "bigquery_initialized",
                project=settings.gcp_project,
                dataset=settings.bq_dataset,
            )

    async def get_hand_by_id(self, hand_id: str) -> HandDetail | None:
        """
        hand_id로 핸드 상세 정보 조회

        Args:
            hand_id: 핸드 ID

        Returns:
            HandDetail 또는 None (not found)
        """
        if self.mock_mode:
            return await self._mock_get_hand(hand_id)

        try:
            table_name = settings.get_bq_table_full_name(settings.bq_table_hand_summary)
            query = f"""
            SELECT
                hand_id,
                hero_name,
                villain_name,
                description,
                pot_bb,
                street,
                action,
                hero_cards,
                board,
                tournament,
                year,
                tags,
                created_at,
                updated_at
            FROM `{table_name}`
            WHERE hand_id = @hand_id
            LIMIT 1
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("hand_id", "STRING", hand_id)
                ]
            )

            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            if not results:
                logger.warning("hand_not_found", hand_id=hand_id)
                return None

            row = results[0]
            hand = HandDetail(
                hand_id=row.hand_id,
                hero_name=row.hero_name,
                villain_name=row.villain_name,
                description=row.description,
                pot_bb=row.pot_bb,
                street=row.street,
                action=row.action,
                hero_cards=row.hero_cards,
                board=row.board,
                tournament=row.tournament,
                year=row.year,
                tags=row.tags or [],
                video_file_path=None,  # TODO: JOIN with video_files table
                video_url=None,
                timestamp=None,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

            logger.info("hand_retrieved", hand_id=hand_id)
            return hand

        except Exception as e:
            logger.error("bigquery_error", error=str(e), hand_id=hand_id)
            raise

    async def _mock_get_hand(self, hand_id: str) -> HandDetail | None:
        """Mock 핸드 조회 (테스트용)"""
        logger.info("using_mock_bigquery", hand_id=hand_id)

        try:
            # mock_data/synthetic_ati/ 에서 해당 ID 파일 로드
            sample_file = f"{settings.test_data_path}/{hand_id}.json"
            with open(sample_file, "r", encoding="utf-8") as f:
                hand_data = json.load(f)

            return HandDetail(
                hand_id=hand_id,
                hero_name=hand_data.get("hero", {}).get("name", "Unknown"),
                villain_name=None,
                description=hand_data.get("description", "Mock hand"),
                pot_bb=hand_data.get("pot_size_bb", 100.0),
                street=hand_data.get("street", "River"),
                action=hand_data.get("action", "Call"),
                hero_cards=hand_data.get("hero", {}).get("cards"),
                board=hand_data.get("board"),
                tournament=hand_data.get("tournament"),
                year=hand_data.get("year"),
                tags=hand_data.get("tags", []),
                video_file_path=None,
                video_url=None,
                timestamp=None,
                created_at=None,
                updated_at=None,
            )

        except FileNotFoundError:
            logger.warning("mock_hand_not_found", hand_id=hand_id)
            return None
        except Exception as e:
            logger.error("mock_bigquery_error", error=str(e), hand_id=hand_id)
            # 하드코딩 샘플 반환
            return HandDetail(
                hand_id=hand_id,
                hero_name="Phil Ivey",
                villain_name="Tom Dwan",
                description="Sample hand for testing",
                pot_bb=150.0,
                street="River",
                action="Bluff",
                hero_cards="Ah Kh",
                board="Qh Jh 9s 5d 2c",
                tournament="High Stakes Poker",
                year=2023,
                tags=["bluff", "high-stakes"],
                video_file_path=None,
                video_url=None,
                timestamp=None,
                created_at=None,
                updated_at=None,
            )


class BigQueryAutocompleteService:
    """BigQuery 기반 자동완성 서비스"""

    def __init__(self, client: Optional[bigquery.Client] = None):
        """
        BigQuery 클라이언트 초기화

        Args:
            client: BigQuery 클라이언트 (테스트용 Mock 주입 가능)
        """
        if client:
            self.client = client
        else:
            # 환경변수 확인
            if settings.enable_mock_mode:
                logger.info("bigquery_autocomplete_mock_mode_enabled")
                self.client = None
            else:
                self.client = bigquery.Client(project=settings.gcp_project)
                logger.info(
                    "bigquery_autocomplete_initialized",
                    project=settings.gcp_project,
                    dataset=settings.bq_dataset,
                )

        self.dataset = os.getenv("BQ_DATASET", settings.bq_dataset)
        self.table = os.getenv("BQ_TABLE_HAND_SUMMARY", settings.bq_table_hand_summary)

    def _validate_query(self, query: str) -> str:
        """
        입력 쿼리 검증 및 정제

        Args:
            query: 사용자 입력 쿼리

        Returns:
            정제된 쿼리

        Raises:
            ValueError: 쿼리가 너무 짧거나 잘못된 경우
        """
        # 기본 검증
        if not query or len(query.strip()) < 2:
            raise ValueError("Query must be at least 2 characters long")

        # 특수문자 제거 (영문, 숫자, 공백, 하이픈만 허용)
        cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', '', query.strip())

        if not cleaned:
            raise ValueError("Query contains only invalid characters")

        # 최대 길이 제한
        if len(cleaned) > 100:
            cleaned = cleaned[:100]

        return cleaned

    async def get_autocomplete_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """
        BigQuery에서 prefix 매칭으로 자동완성 제안 반환.

        Args:
            query: 검색 쿼리 (최소 2자)
            limit: 최대 결과 개수 (기본 10)

        Returns:
            자동완성 제안 리스트 (빈도순 정렬)

        Example:
            >>> service = BigQueryAutocompleteService(client)
            >>> await service.get_autocomplete_suggestions("Phil", limit=5)
            ["Phil Ivey", "Phil Hellmuth", "Philip Ng"]

        Raises:
            ValueError: 쿼리가 너무 짧거나 잘못된 경우
        """
        try:
            # 입력 검증
            cleaned_query = self._validate_query(query)
            logger.info(
                "autocomplete_query_received",
                original_query=query,
                cleaned_query=cleaned_query,
                limit=limit
            )

            # Mock 모드 처리
            if self.client is None:
                return await self._mock_autocomplete(cleaned_query, limit)

            # SQL 쿼리 구성
            # LIKE 패턴 생성 (SQL Injection 방지를 위해 파라미터화)
            query_pattern = f"{cleaned_query}%"

            # BigQuery 전체 테이블명
            table_name = f"{settings.gcp_project}.{self.dataset}.{self.table}"

            # SQL 쿼리
            sql = f"""
            WITH player_names AS (
                SELECT hero_name AS name, COUNT(*) AS frequency
                FROM `{table_name}`
                WHERE LOWER(hero_name) LIKE LOWER(@query_pattern)
                GROUP BY hero_name

                UNION ALL

                SELECT villain_name AS name, COUNT(*) AS frequency
                FROM `{table_name}`
                WHERE villain_name IS NOT NULL
                  AND LOWER(villain_name) LIKE LOWER(@query_pattern)
                GROUP BY villain_name
            ),
            aggregated AS (
                SELECT
                    name,
                    SUM(frequency) AS total_frequency
                FROM player_names
                WHERE name IS NOT NULL
                GROUP BY name
            )
            SELECT name
            FROM aggregated
            ORDER BY total_frequency DESC
            LIMIT @limit
            """

            # 쿼리 파라미터 설정 (SQL Injection 방지)
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("query_pattern", "STRING", query_pattern),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )

            # 쿼리 실행
            query_job = self.client.query(sql, job_config=job_config)
            results = query_job.result()

            # 결과 파싱
            suggestions = []
            for row in results:
                if row.name:  # None 체크
                    suggestions.append(row.name)

            logger.info(
                "autocomplete_results",
                query=cleaned_query,
                count=len(suggestions),
                suggestions=suggestions[:3]  # 로그에는 처음 3개만
            )

            return suggestions

        except ValueError as e:
            logger.warning("autocomplete_validation_error", error=str(e), query=query)
            raise
        except Exception as e:
            logger.error("autocomplete_error", error=str(e), query=query)
            # 에러 발생 시 빈 리스트 반환 (fail gracefully)
            return []

    async def _mock_autocomplete(self, query: str, limit: int) -> List[str]:
        """
        Mock 자동완성 (테스트용)

        Args:
            query: 검색 쿼리
            limit: 최대 결과 개수

        Returns:
            Mock 자동완성 제안 리스트
        """
        logger.info("using_mock_autocomplete", query=query, limit=limit)

        # Mock 데이터
        mock_names = [
            "Phil Ivey",
            "Phil Hellmuth",
            "Philip Ng",
            "Tom Dwan",
            "Daniel Negreanu",
            "Doug Polk",
            "Junglemann",
            "Fedor Holz",
            "Vanessa Selbst",
            "Antonio Esfandiari",
            "Jason Koon",
            "Dan Smith",
            "Bryn Kenney",
            "Justin Bonomo",
            "Stephen Chidwick",
            "David Peters",
            "Sam Greenwood",
            "Mikita Badziakouski",
            "Isaac Haxton",
            "Timothy Adams"
        ]

        # 대소문자 구분 없이 prefix 매칭
        query_lower = query.lower()
        suggestions = [
            name for name in mock_names
            if name.lower().startswith(query_lower)
        ]

        # limit 적용 및 반환
        return suggestions[:limit]
