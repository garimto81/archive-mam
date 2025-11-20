#!/bin/bash
# 통합 테스트 스크립트
# v4.0.0 - GCS → Cloud Functions → BigQuery 전체 플로우 검증

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경변수
GCP_PROJECT="${GCP_PROJECT:-gg-poker-prod}"
REGION="us-central1"
BUCKET_NAME="ati-metadata-prod"
DATASET="poker_archive"
TABLE="hands"
FUNCTION_NAME="index-ati-metadata"

# 테스트 설정
TEST_COUNT="${TEST_COUNT:-10}"  # 테스트할 파일 수 (기본: 10개)
CLEANUP="${CLEANUP:-false}"     # 테스트 후 리소스 정리 (기본: 유지)

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}통합 테스트: GCS → BigQuery 플로우${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "프로젝트: ${GREEN}$GCP_PROJECT${NC}"
echo -e "리전: ${GREEN}$REGION${NC}"
echo -e "테스트 파일 수: ${GREEN}$TEST_COUNT${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Step 0: 사전 준비 확인
echo -e "${YELLOW}[Step 0/8]${NC} 사전 준비 확인..."

if [ -z "$GCP_PROJECT" ]; then
    echo -e "${RED}❌ GCP_PROJECT 환경변수가 설정되지 않았습니다.${NC}"
    echo "사용법: export GCP_PROJECT=gg-poker-prod"
    exit 1
fi

# gcloud 인증 확인
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${RED}❌ GCP 인증이 필요합니다.${NC}"
    echo "실행: gcloud auth login"
    exit 1
fi

echo -e "${GREEN}✅ 인증 확인 완료${NC}"

# 프로젝트 설정
gcloud config set project "$GCP_PROJECT" --quiet
echo -e "${GREEN}✅ 프로젝트 설정: $GCP_PROJECT${NC}"

# Step 1: API 활성화
echo ""
echo -e "${YELLOW}[Step 1/8]${NC} 필요한 API 활성화..."

APIS=(
    "storage.googleapis.com"
    "bigquery.googleapis.com"
    "cloudfunctions.googleapis.com"
    "pubsub.googleapis.com"
)

for api in "${APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo -e "${GREEN}✅${NC} $api 이미 활성화됨"
    else
        echo -e "${YELLOW}📝${NC} $api 활성화 중..."
        gcloud services enable "$api" --quiet
        echo -e "${GREEN}✅${NC} $api 활성화 완료"
    fi
done

# Step 2: GCS 버킷 생성
echo ""
echo -e "${YELLOW}[Step 2/8]${NC} GCS 버킷 생성/확인..."

if gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
    echo -e "${GREEN}✅ 버킷 'gs://$BUCKET_NAME' 이미 존재${NC}"
else
    echo -e "${YELLOW}📝 버킷 생성 중...${NC}"
    gsutil mb -p "$GCP_PROJECT" -c STANDARD -l "$REGION" "gs://$BUCKET_NAME"
    echo -e "${GREEN}✅ 버킷 생성 완료${NC}"
fi

# Step 3: BigQuery 테이블 생성
echo ""
echo -e "${YELLOW}[Step 3/8]${NC} BigQuery 테이블 생성/확인..."

# 데이터셋 확인
if bq ls -d --project_id="$GCP_PROJECT" | grep -q "$DATASET"; then
    echo -e "${GREEN}✅ 데이터셋 '$DATASET' 이미 존재${NC}"
else
    echo -e "${YELLOW}📝 데이터셋 생성 중...${NC}"
    bq mk --dataset --location=US --description="포커 핸드 메타데이터" "$GCP_PROJECT:$DATASET"
    echo -e "${GREEN}✅ 데이터셋 생성 완료${NC}"
fi

# 테이블 확인
if bq ls --project_id="$GCP_PROJECT" "$DATASET" | grep -q "$TABLE"; then
    echo -e "${YELLOW}⚠️  테이블 '$TABLE' 이미 존재 - 기존 데이터 유지${NC}"

    # 기존 행 수 확인
    EXISTING_COUNT=$(bq query --use_legacy_sql=false --format=csv \
        "SELECT COUNT(*) FROM \`$GCP_PROJECT.$DATASET.$TABLE\`" | tail -n 1)
    echo -e "${BLUE}ℹ️  기존 데이터: $EXISTING_COUNT 행${NC}"
else
    echo -e "${YELLOW}📝 테이블 생성 중...${NC}"
    bq mk --table \
        --project_id="$GCP_PROJECT" \
        --time_partitioning_field=created_date \
        --time_partitioning_type=DAY \
        --clustering_fields=tournament_id,hand_number \
        "$GCP_PROJECT:$DATASET.$TABLE" \
        bigquery_schema.json
    echo -e "${GREEN}✅ 테이블 생성 완료${NC}"
fi

# Step 4: Cloud Functions 배포
echo ""
echo -e "${YELLOW}[Step 4/8]${NC} Cloud Functions 배포..."
echo -e "${BLUE}ℹ️  배포에 2-3분 소요됩니다...${NC}"

cd cloud_functions/index_metadata

gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime=python311 \
    --region="$REGION" \
    --source=. \
    --entry-point=process_ati_metadata \
    --trigger-bucket="$BUCKET_NAME" \
    --memory=512MB \
    --timeout=540s \
    --set-env-vars="GCP_PROJECT=$GCP_PROJECT" \
    --max-instances=10 \
    --quiet

echo -e "${GREEN}✅ Cloud Functions 배포 완료${NC}"

cd ../..

# Step 5: 테스트 데이터 준비
echo ""
echo -e "${YELLOW}[Step 5/8]${NC} 테스트 데이터 업로드 ($TEST_COUNT 개 파일)..."

# 기존 테스트 데이터 정리 (선택)
echo -e "${BLUE}ℹ️  기존 테스트 데이터 정리 중...${NC}"
gsutil -m rm -f "gs://$BUCKET_NAME/test/*.json" 2>/dev/null || true

# 새 테스트 데이터 업로드
echo -e "${YELLOW}📝 $TEST_COUNT 개 파일 업로드 중...${NC}"

count=0
for file in mock_data/synthetic_ati/*.json; do
    if [ $count -ge $TEST_COUNT ]; then
        break
    fi

    # all_hands_combined.json 제외
    if [[ $(basename "$file") == "all_hands_combined.json" ]]; then
        continue
    fi

    gsutil cp "$file" "gs://$BUCKET_NAME/test/" &
    ((count++))
done

# 백그라운드 작업 완료 대기
wait

echo -e "${GREEN}✅ $TEST_COUNT 개 파일 업로드 완료${NC}"

# Step 6: Cloud Functions 실행 대기 (Pub/Sub 트리거)
echo ""
echo -e "${YELLOW}[Step 6/8]${NC} Cloud Functions 실행 대기..."
echo -e "${BLUE}ℹ️  Pub/Sub 트리거 처리 중... (10초 대기)${NC}"

sleep 10

# Step 7: 결과 검증
echo ""
echo -e "${YELLOW}[Step 7/8]${NC} 결과 검증..."

# 7-1. Cloud Functions 로그 확인
echo ""
echo -e "${BLUE}[7-1] Cloud Functions 로그 (최근 20개):${NC}"
gcloud functions logs read "$FUNCTION_NAME" \
    --region="$REGION" \
    --gen2 \
    --limit=20 \
    --format="table(time,severity,textPayload)" 2>/dev/null || echo "로그 조회 실패 (함수 아직 실행 안 됨)"

# 7-2. BigQuery 행 수 확인
echo ""
echo -e "${BLUE}[7-2] BigQuery 행 수 확인:${NC}"

FINAL_COUNT=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`$GCP_PROJECT.$DATASET.$TABLE\`" | tail -n 1)

EXPECTED_MIN=$((EXISTING_COUNT + TEST_COUNT))

echo -e "기존 행: ${BLUE}$EXISTING_COUNT${NC}"
echo -e "추가 예상: ${BLUE}$TEST_COUNT${NC}"
echo -e "현재 행: ${BLUE}$FINAL_COUNT${NC}"

if [ "$FINAL_COUNT" -ge "$EXPECTED_MIN" ]; then
    echo -e "${GREEN}✅ 데이터 삽입 성공 (최소 $TEST_COUNT 개 추가됨)${NC}"
else
    echo -e "${RED}❌ 데이터 삽입 부분 실패 (예상: $EXPECTED_MIN, 실제: $FINAL_COUNT)${NC}"
    echo -e "${YELLOW}⚠️  Cloud Functions 로그를 확인하세요${NC}"
fi

# 7-3. 최근 삽입된 데이터 샘플
echo ""
echo -e "${BLUE}[7-3] 최근 삽입된 데이터 (5개):${NC}"

bq query --use_legacy_sql=false --format=pretty \
    "SELECT hand_id, hero_name, pot_bb, created_at
     FROM \`$GCP_PROJECT.$DATASET.$TABLE\`
     ORDER BY created_at DESC
     LIMIT 5"

# 7-4. 에러 로그 확인
echo ""
echo -e "${BLUE}[7-4] 에러 로그 확인:${NC}"

ERROR_COUNT=$(gcloud functions logs read "$FUNCTION_NAME" \
    --region="$REGION" \
    --gen2 \
    --filter="severity>=ERROR" \
    --limit=10 \
    --format="value(textPayload)" 2>/dev/null | wc -l)

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ 에러 없음${NC}"
else
    echo -e "${RED}⚠️  $ERROR_COUNT 개 에러 발견${NC}"
    echo -e "${YELLOW}에러 로그:${NC}"
    gcloud functions logs read "$FUNCTION_NAME" \
        --region="$REGION" \
        --gen2 \
        --filter="severity>=ERROR" \
        --limit=5 \
        --format="table(time,textPayload)"
fi

# Step 8: 정리 (선택)
echo ""
echo -e "${YELLOW}[Step 8/8]${NC} 리소스 정리..."

if [ "$CLEANUP" = "true" ]; then
    echo -e "${RED}⚠️  CLEANUP=true - 리소스 정리 중...${NC}"

    # 테스트 데이터 삭제
    echo -e "${YELLOW}📝 GCS 테스트 데이터 삭제 중...${NC}"
    gsutil -m rm -f "gs://$BUCKET_NAME/test/*.json" 2>/dev/null || true

    # Cloud Functions 삭제 (선택)
    read -p "Cloud Functions도 삭제할까요? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud functions delete "$FUNCTION_NAME" --region="$REGION" --gen2 --quiet
        echo -e "${GREEN}✅ Cloud Functions 삭제 완료${NC}"
    fi

    # BigQuery 테이블 삭제 (선택)
    read -p "BigQuery 테이블도 삭제할까요? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bq rm -f -t "$GCP_PROJECT:$DATASET.$TABLE"
        echo -e "${GREEN}✅ BigQuery 테이블 삭제 완료${NC}"
    fi
else
    echo -e "${GREEN}✅ 리소스 유지 (CLEANUP=false)${NC}"
    echo -e "${BLUE}ℹ️  정리하려면: CLEANUP=true bash test_integration.sh${NC}"
fi

# 최종 요약
echo ""
echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}✅ 통합 테스트 완료!${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""
echo -e "📊 결과 요약:"
echo -e "  - GCS 버킷: ${GREEN}gs://$BUCKET_NAME${NC}"
echo -e "  - BigQuery 테이블: ${GREEN}$GCP_PROJECT:$DATASET.$TABLE${NC}"
echo -e "  - Cloud Functions: ${GREEN}$FUNCTION_NAME${NC}"
echo -e "  - 테스트 파일: ${GREEN}$TEST_COUNT 개${NC}"
echo -e "  - BigQuery 행: ${GREEN}$FINAL_COUNT 개${NC}"
echo -e "  - 에러: ${GREEN}$ERROR_COUNT 개${NC}"
echo ""
echo -e "🔍 추가 확인:"
echo -e "  - 로그: ${BLUE}gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2 --limit=50${NC}"
echo -e "  - 데이터: ${BLUE}bq query --use_legacy_sql=false 'SELECT * FROM \`$GCP_PROJECT.$DATASET.$TABLE\` LIMIT 10'${NC}"
echo ""
echo -e "${BLUE}=======================================${NC}"
