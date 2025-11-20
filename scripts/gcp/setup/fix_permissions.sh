#!/bin/bash
# Eventarc 권한 설정 및 Cloud Functions 배포
# v4.0.0

set -e

echo "========================================="
echo "Eventarc 권한 설정 및 배포"
echo "========================================="

# 프로젝트 번호 가져오기
echo "[1/4] 프로젝트 번호 확인 중..."
PROJECT_NUMBER=$(gcloud projects describe gg-poker-prod --format="value(projectNumber)")
echo "✅ 프로젝트 번호: $PROJECT_NUMBER"

# Eventarc 서비스 계정 권한 부여
echo ""
echo "[2/4] Eventarc 서비스 계정 권한 부여 중..."
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-eventarc.iam.gserviceaccount.com" \
  --role="roles/eventarc.serviceAgent" \
  --quiet

echo "✅ Eventarc 권한 부여 완료"

# Pub/Sub 서비스 계정 권한 부여
echo ""
echo "[3/4] Pub/Sub 서비스 계정 권한 부여 중..."
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --quiet

echo "✅ Pub/Sub 권한 부여 완료"

# 권한 전파 대기
echo ""
echo "[4/4] 권한 전파 대기 중 (10초)..."
sleep 10
echo "✅ 대기 완료"

# Cloud Functions 배포
echo ""
echo "========================================="
echo "Cloud Functions 배포 시작"
echo "========================================="

cd cloud_functions/index_metadata
bash deploy.sh

echo ""
echo "========================================="
echo "✅ 모든 작업 완료!"
echo "========================================="
