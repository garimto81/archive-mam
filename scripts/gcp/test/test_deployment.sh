#!/bin/bash
# 배포 검증 테스트
# v4.0.0 - GCS → Cloud Functions → BigQuery 플로우 검증

set -e

echo "========================================="
echo "배포 검증 테스트"
echo "========================================="

# Step 1: 테스트 데이터 업로드
echo ""
echo "[1/4] 테스트 데이터 업로드 중..."
gsutil cp mock_data/synthetic_ati/ati_metadata_001.json gs://ati-metadata-prod/test/
echo "✅ 파일 업로드 완료"

# Step 2: Cloud Functions 실행 대기
echo ""
echo "[2/4] Cloud Functions 자동 실행 대기 중..."
echo "⏳ 10초 대기..."
sleep 10
echo "✅ 대기 완료"

# Step 3: 로그 확인
echo ""
echo "[3/4] Cloud Functions 로그 확인..."
echo "========================================="
gcloud functions logs read index-ati-metadata \
  --region us-central1 \
  --gen2 \
  --limit 20 \
  --format "table(time.format('%Y-%m-%d %H:%M:%S'),severity,textPayload)" 2>/dev/null || echo "로그 조회 실패"

# 성공 메시지 확인
echo ""
echo "성공 메시지 필터링..."
SUCCESS_COUNT=$(gcloud functions logs read index-ati-metadata \
  --region us-central1 \
  --gen2 \
  --filter "textPayload=~'Processing completed successfully'" \
  --limit 5 \
  --format "value(textPayload)" 2>/dev/null | wc -l)

if [ "$SUCCESS_COUNT" -gt 0 ]; then
  echo "✅ Cloud Functions 처리 성공 ($SUCCESS_COUNT 건)"
else
  echo "❌ 성공 로그 없음 - 에러 확인 필요"
fi

# Step 4: BigQuery 데이터 확인
echo ""
echo "[4/4] BigQuery 데이터 확인..."
echo "========================================="

# 행 수 확인
TOTAL_ROWS=$(bq query --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) FROM poker_archive.hands" 2>/dev/null | tail -n 1)

echo "전체 행 수: $TOTAL_ROWS"

# 최근 데이터 조회
echo ""
echo "최근 삽입된 데이터 (5개):"
bq query --use_legacy_sql=false --format=pretty \
  "SELECT hand_id, hero_name, pot_bb, created_at
   FROM poker_archive.hands
   ORDER BY created_at DESC
   LIMIT 5" 2>/dev/null || echo "BigQuery 조회 실패"

# 최종 결과
echo ""
echo "========================================="
if [ "$TOTAL_ROWS" -gt 0 ] && [ "$SUCCESS_COUNT" -gt 0 ]; then
  echo "🎉 테스트 성공!"
  echo "========================================="
  echo "✅ Cloud Functions 실행 성공"
  echo "✅ BigQuery 데이터 삽입 성공"
  echo "✅ 전체 행 수: $TOTAL_ROWS"
  echo ""
  echo "다음 단계:"
  echo "  1. 대량 테스트: gsutil -m cp mock_data/synthetic_ati/*.json gs://ati-metadata-prod/batch/"
  echo "  2. FastAPI 백엔드 개발"
  echo "  3. Vertex AI Embedding 추가"
else
  echo "⚠️  테스트 실패 - 문제 확인 필요"
  echo "========================================="
  echo "로그 상세 확인:"
  echo "  gcloud functions logs read index-ati-metadata --region us-central1 --gen2 --limit 50"
  echo ""
  echo "에러 로그 확인:"
  echo "  gcloud functions logs read index-ati-metadata --region us-central1 --gen2 --filter 'severity>=ERROR' --limit 10"
fi
echo "========================================="
