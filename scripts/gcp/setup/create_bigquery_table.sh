#!/bin/bash
# BigQuery 테이블 생성 스크립트
# v4.0.0 - Vertex AI Vector Search + BigQuery 아키텍처

set -e  # 에러 발생 시 즉시 종료

# 환경변수 확인
if [ -z "$GCP_PROJECT" ]; then
    echo "Error: GCP_PROJECT 환경변수가 설정되지 않았습니다."
    echo "사용법: export GCP_PROJECT=gg-poker-prod"
    exit 1
fi

DATASET="poker_archive"
TABLE="hands"
SCHEMA_FILE="bigquery_schema.json"

echo "========================================="
echo "BigQuery 테이블 생성"
echo "========================================="
echo "프로젝트: $GCP_PROJECT"
echo "데이터셋: $DATASET"
echo "테이블: $TABLE"
echo "========================================="

# 1. 데이터셋 존재 확인 및 생성
echo ""
echo "[1/3] 데이터셋 확인 중..."
if bq ls -d --project_id="$GCP_PROJECT" | grep -q "$DATASET"; then
    echo "✅ 데이터셋 '$DATASET' 이미 존재합니다."
else
    echo "📝 데이터셋 '$DATASET' 생성 중..."
    bq mk \
        --dataset \
        --location=US \
        --description="포커 핸드 메타데이터 아카이브 (ATI 기반)" \
        "$GCP_PROJECT:$DATASET"
    echo "✅ 데이터셋 생성 완료"
fi

# 2. 테이블 생성
echo ""
echo "[2/3] 테이블 생성 중..."
bq mk --table \
    --project_id="$GCP_PROJECT" \
    --description="ATI 메타데이터 기반 포커 핸드 검색 테이블 (v4.0.0)" \
    --time_partitioning_field=created_date \
    --time_partitioning_type=DAY \
    --clustering_fields=tournament_id,hand_number \
    --require_partition_filter=false \
    "$GCP_PROJECT:$DATASET.$TABLE" \
    "$SCHEMA_FILE"

echo "✅ 테이블 생성 완료"

# 3. 테이블 정보 확인
echo ""
echo "[3/3] 테이블 정보 확인..."
bq show --format=prettyjson "$GCP_PROJECT:$DATASET.$TABLE"

echo ""
echo "========================================="
echo "✅ BigQuery 테이블 생성 완료!"
echo "========================================="
echo ""
echo "테이블 전체 이름: $GCP_PROJECT:$DATASET.$TABLE"
echo "파티셔닝: created_date (일별)"
echo "클러스터링: tournament_id, hand_number"
echo ""
echo "다음 단계:"
echo "  1. Cloud Functions 코드 작성"
echo "  2. GCS에 테스트 데이터 업로드"
echo "  3. 인덱싱 테스트"
echo "========================================="
