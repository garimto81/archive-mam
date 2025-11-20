#!/bin/bash
# Cloud Run 배포 스크립트
# v4.0.0 - Vertex AI Vector Search + BigQuery

set -e

# 프로젝트 설정
export GCP_PROJECT="gg-poker-prod"
export REGION="us-central1"
export SERVICE_NAME="archive-mam-api"

# 환경변수 로드
if [ ! -f .env ]; then
    echo "[ERROR] .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    exit 1
fi

# .env 파일의 모든 변수를 export (자식 프로세스에 전달)
set -a
source .env
set +a

echo "========================================="
echo "Cloud Run 배포"
echo "========================================="
echo "프로젝트: $GCP_PROJECT"
echo "리전: $REGION"
echo "서비스: $SERVICE_NAME"
echo ""

# 1. Google Cloud 인증 확인
echo "[1/5] Google Cloud 인증 확인..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "[ERROR] Google Cloud 인증이 필요합니다."
    echo "실행: gcloud auth login"
    exit 1
fi
echo "[OK] 인증 완료"

# 2. 프로젝트 설정
echo ""
echo "[2/5] 프로젝트 설정..."
gcloud config set project $GCP_PROJECT
echo "[OK] 프로젝트 설정: $GCP_PROJECT"

# 3. Cloud Run API 활성화
echo ""
echo "[3/5] Cloud Run API 활성화..."
gcloud services enable run.googleapis.com --project=$GCP_PROJECT
echo "[OK] API 활성화 완료"

# 4. Cloud Run 배포
echo ""
echo "[4/5] Cloud Run 배포 중..."
echo "소스 코드에서 직접 빌드 및 배포..."

# Git Bash는 /api를 C:/Program Files/Git/api로 변환하므로 //api 사용
# Cloud Run에서 자동으로 /api로 정규화됨
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --set-env-vars="GCP_PROJECT=$GCP_PROJECT,GCP_REGION=$GCP_REGION,BIGQUERY_DATASET=$BIGQUERY_DATASET,BIGQUERY_TABLE=$BIGQUERY_TABLE,GCS_METADATA_BUCKET=$GCS_METADATA_BUCKET,GCS_VIDEOS_BUCKET=$GCS_VIDEOS_BUCKET,VERTEX_AI_INDEX_ENDPOINT=$VERTEX_AI_INDEX_ENDPOINT,VERTEX_AI_DEPLOYED_INDEX_ID=$VERTEX_AI_DEPLOYED_INDEX_ID,API_V1_PREFIX=//api,SIGNED_URL_EXPIRATION=$SIGNED_URL_EXPIRATION"

# 5. 배포 확인
echo ""
echo "[5/5] 배포 확인..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)')

echo ""
echo "========================================="
echo "배포 완료!"
echo "========================================="
echo "서비스 URL: $SERVICE_URL"
echo ""
echo "테스트:"
echo "  curl $SERVICE_URL/health"
echo "  curl \"$SERVICE_URL/api/search?q=river+call&limit=5\""
echo ""
echo "API 문서:"
echo "  $SERVICE_URL/api/docs"
echo "========================================="
