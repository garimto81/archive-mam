#!/bin/bash
# 완전한 GCS → Cloud Functions → BigQuery 파이프라인 설정
# v4.0.0 - 모든 권한 및 배포 자동화

set -e

echo "========================================="
echo "ATI 메타데이터 인덱싱 파이프라인 설정"
echo "========================================="

# 환경변수 확인
if [ -z "$GCP_PROJECT" ]; then
    echo "Error: GCP_PROJECT 환경변수가 설정되지 않았습니다."
    echo "사용법: export GCP_PROJECT=gg-poker-prod"
    exit 1
fi

# 프로젝트 번호 가져오기
echo ""
echo "[1/5] 프로젝트 정보 확인 중..."
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT --format="value(projectNumber)")
echo "✅ 프로젝트 번호: $PROJECT_NUMBER"

# Eventarc 서비스 계정 권한
echo ""
echo "[2/5] Eventarc 서비스 계정 권한 부여 중..."
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-eventarc.iam.gserviceaccount.com" \
  --role="roles/eventarc.serviceAgent" \
  --quiet

echo "✅ Eventarc 권한 부여 완료"

# Pub/Sub 서비스 계정 권한
echo ""
echo "[3/5] Pub/Sub 서비스 계정 권한 부여 중..."
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --quiet

echo "✅ Pub/Sub 권한 부여 완료"

# BigQuery 권한
echo ""
echo "[4/5] Cloud Functions 서비스 계정 BigQuery 권한 부여 중..."
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  --quiet

echo "✅ BigQuery 권한 부여 완료"

# Cloud Functions 배포
echo ""
echo "[5/5] Cloud Functions 배포 중..."
cd cloud_functions/index_metadata
bash deploy.sh

echo ""
echo "========================================="
echo "배포 후 권한 설정"
echo "========================================="

# Storage 서비스 계정 Pub/Sub 권한
echo ""
echo "[추가 1/2] Storage 서비스 계정 Pub/Sub 권한 부여 중..."
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher" \
  --quiet

echo "✅ Storage Pub/Sub 권한 부여 완료"

# Pub/Sub 토픽 직접 권한 부여
echo ""
echo "[추가 2/2] Pub/Sub 토픽 직접 권한 부여 중..."
TOPIC=$(gcloud eventarc triggers describe index-ati-metadata-* \
  --location us-central1 \
  --format="value(transport.pubsub.topic)" 2>/dev/null | head -1)

if [ -n "$TOPIC" ]; then
    TOPIC_NAME=$(basename $TOPIC)
    gcloud pubsub topics add-iam-policy-binding $TOPIC_NAME \
      --member="serviceAccount:service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com" \
      --role="roles/pubsub.publisher" \
      --quiet
    echo "✅ Pub/Sub 토픽 권한 부여 완료"
else
    echo "⚠️  Pub/Sub 토픽을 찾을 수 없습니다. 수동으로 권한 부여 필요"
fi

# 권한 전파 대기
echo ""
echo "권한 전파 대기 중 (10초)..."
sleep 10
echo "✅ 대기 완료"

echo ""
echo "========================================="
echo "🎉 전체 설정 완료!"
echo "========================================="
echo ""
echo "테스트 방법:"
echo "  bash test_deployment.sh"
echo ""
echo "========================================="
