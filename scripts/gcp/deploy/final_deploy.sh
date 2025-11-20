#!/bin/bash
# 최종 권한 설정 및 배포
# v4.0.0

set -e

echo "========================================="
echo "Storage 권한 설정 및 최종 배포"
echo "========================================="

# Storage 서비스 계정 권한 부여
echo "[1/3] Storage 서비스 계정 권한 부여 중..."
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:service-45067711104@gs-project-accounts.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher" \
  --quiet

echo "✅ Storage 권한 부여 완료"

# 권한 전파 대기
echo ""
echo "[2/3] 권한 전파 대기 중 (10초)..."
sleep 10
echo "✅ 대기 완료"

# Cloud Functions 배포
echo ""
echo "[3/3] Cloud Functions 배포 중..."
cd cloud_functions/index_metadata
bash deploy.sh

echo ""
echo "========================================="
echo "✅ 배포 완료!"
echo "========================================="
