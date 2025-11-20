"""
BigQuery 서비스
v4.0.0
"""

from google.cloud import bigquery
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.config import settings
from app.models.schemas import HandMetadata


class BigQueryService:
    """BigQuery 조회 서비스"""

    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT)
        self.table_id = f"{settings.GCP_PROJECT}.{settings.BIGQUERY_DATASET}.{settings.BIGQUERY_TABLE}"

    def get_hand_by_id(self, hand_id: str) -> Optional[HandMetadata]:
        """핸드 ID로 메타데이터 조회

        Args:
            hand_id: 핸드 ID

        Returns:
            HandMetadata 또는 None
        """
        query = f"""
            SELECT *
            FROM `{self.table_id}`
            WHERE hand_id = @hand_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hand_id", "STRING", hand_id)
            ]
        )

        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            if not results:
                return None

            row = results[0]
            return self._row_to_hand_metadata(row)

        except Exception as e:
            print(f"BigQuery error: {e}")
            raise

    def get_hands_by_ids(self, hand_ids: List[str]) -> List[HandMetadata]:
        """여러 핸드 ID로 메타데이터 조회

        Args:
            hand_ids: 핸드 ID 리스트

        Returns:
            HandMetadata 리스트
        """
        if not hand_ids:
            return []

        # IN 쿼리 사용
        placeholders = ", ".join([f"'{hid}'" for hid in hand_ids])
        query = f"""
            SELECT *
            FROM `{self.table_id}`
            WHERE hand_id IN ({placeholders})
        """

        try:
            query_job = self.client.query(query)
            results = query_job.result()

            hands = []
            for row in results:
                hands.append(self._row_to_hand_metadata(row))

            # hand_ids 순서대로 정렬
            hand_dict = {h.hand_id: h for h in hands}
            return [hand_dict[hid] for hid in hand_ids if hid in hand_dict]

        except Exception as e:
            print(f"BigQuery error: {e}")
            raise

    def search_hands(
        self,
        min_pot_bb: Optional[float] = None,
        tournament_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[HandMetadata]:
        """필터 조건으로 핸드 검색

        Args:
            min_pot_bb: 최소 팟 사이즈
            tournament_id: 토너먼트 ID
            tags: 태그 필터
            limit: 결과 수 제한

        Returns:
            HandMetadata 리스트
        """
        where_clauses = []
        query_params = []

        if min_pot_bb is not None:
            where_clauses.append("pot_bb >= @min_pot_bb")
            query_params.append(
                bigquery.ScalarQueryParameter("min_pot_bb", "FLOAT64", min_pot_bb)
            )

        if tournament_id:
            where_clauses.append("tournament_id = @tournament_id")
            query_params.append(
                bigquery.ScalarQueryParameter("tournament_id", "STRING", tournament_id)
            )

        if tags:
            # ARRAY_LENGTH를 사용한 태그 필터
            for i, tag in enumerate(tags):
                where_clauses.append(f"@tag{i} IN UNNEST(tags)")
                query_params.append(
                    bigquery.ScalarQueryParameter(f"tag{i}", "STRING", tag)
                )

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
            SELECT *
            FROM `{self.table_id}`
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT @limit
        """

        query_params.append(
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        )

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)

        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()

            return [self._row_to_hand_metadata(row) for row in results]

        except Exception as e:
            print(f"BigQuery error: {e}")
            raise

    def _row_to_hand_metadata(self, row) -> HandMetadata:
        """BigQuery Row를 HandMetadata로 변환"""
        return HandMetadata(
            hand_id=row.hand_id,
            tournament_id=row.tournament_id,
            hand_number=row.hand_number,
            timestamp=row.timestamp,
            duration_seconds=row.duration_seconds,
            hero_name=row.hero_name,
            villain_name=row.villain_name,
            hero_position=row.hero_position,
            villain_position=row.villain_position,
            hero_stack_bb=row.hero_stack_bb,
            villain_stack_bb=row.villain_stack_bb,
            street=row.street,
            pot_bb=row.pot_bb,
            action_sequence=list(row.action_sequence) if row.action_sequence else None,
            hero_action=row.hero_action,
            result=row.result,
            tags=list(row.tags) if row.tags else None,
            hand_type=row.hand_type,
            description=row.description,
            video_url=row.video_url,
            video_start_time=row.video_start_time,
            video_end_time=row.video_end_time,
            thumbnail_url=row.thumbnail_url,
            created_at=row.created_at,
            gcs_source_path=row.gcs_source_path
        )
