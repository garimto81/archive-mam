#!/bin/bash
# Cloud Functions 배포 스크립트
# v4.0.0 - ATI 메타데이터 인덱싱

set -e

# 환경변수 확인
if [ -z "$GCP_PROJECT" ]; then
    echo "Error: GCP_PROJECT 환경변수가 설정되지 않았습니다."
    echo "사용법: export GCP_PROJECT=gg-poker-prod"
    exit 1
fi

FUNCTION_NAME="index-ati-metadata"
RUNTIME="python311"
TRIGGER_BUCKET="ati-metadata-prod"
ENTRY_POINT="process_ati_metadata"
REGION="us-central1"
MEMORY="512MB"
TIMEOUT="540s"

echo "========================================="
echo "Cloud Functions 배포"
echo "========================================="
echo "프로젝트: $GCP_PROJECT"
echo "함수 이름: $FUNCTION_NAME"
echo "런타임: $RUNTIME"
echo "트리거: gs://$TRIGGER_BUCKET"
echo "리전: $REGION"
echo "========================================="

# 1. 트리거 버킷 존재 확인
echo ""
echo "[1/3] GCS 버킷 확인 중..."
if gsutil ls -b "gs://$TRIGGER_BUCKET" &> /dev/null; then
    echo "✅ 버킷 '$TRIGGER_BUCKET' 존재 확인"
else
    echo "❌ 버킷 '$TRIGGER_BUCKET'이 존재하지 않습니다."
    echo "버킷을 먼저 생성하세요:"
    echo "  gsutil mb -p $GCP_PROJECT -l $REGION gs://$TRIGGER_BUCKET"
    exit 1
fi

# 2. Cloud Functions API 활성화 확인
echo ""
echo "[2/3] Cloud Functions API 확인 중..."
if gcloud services list --enabled --filter="name:cloudfunctions.googleapis.com" --format="value(name)" | grep -q cloudfunctions; then
    echo "✅ Cloud Functions API 활성화됨"
else
    echo "📝 Cloud Functions API 활성화 중..."
    gcloud services enable cloudfunctions.googleapis.com
    echo "✅ API 활성화 완료"
fi

# 3. Cloud Functions 배포
echo ""
echo "[3/3] Cloud Functions 배포 중..."
echo "⏳ 배포에 2-3분 소요됩니다..."

gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime="$RUNTIME" \
    --region="$REGION" \
    --source=. \
    --entry-point="$ENTRY_POINT" \
    --trigger-bucket="$TRIGGER_BUCKET" \
    --memory="$MEMORY" \
    --timeout="$TIMEOUT" \
    --set-env-vars="GCP_PROJECT=$GCP_PROJECT" \
    --max-instances=10 \
    --quiet

echo ""
echo "========================================="
echo "✅ Cloud Functions 배포 완료!"
echo "========================================="
echo ""
echo "함수 정보 확인:"
echo "  gcloud functions describe $FUNCTION_NAME --region=$REGION --gen2"
echo ""
echo "로그 확인:"
echo "  gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2 --limit=50"
echo ""
echo "테스트 방법:"
echo "  1. GCS에 테스트 파일 업로드:"
echo "     gsutil cp mock_data/synthetic_ati/ati_metadata_001.json gs://$TRIGGER_BUCKET/test/"
echo ""
echo "  2. 로그 확인:"
echo "     gcloud functions logs read $FUNCTION_NAME --region=$REGION --gen2 --limit=10"
echo ""
echo "  3. BigQuery 데이터 확인:"
echo "     bq query --use_legacy_sql=false 'SELECT * FROM poker_archive.hands ORDER BY created_at DESC LIMIT 5'"
echo ""
echo "========================================="
