#!/bin/bash
# Verify GCP Production Environment Setup
# Issue: #16 - GCP Production Environment Configuration
# Version: 1.0.0

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_ID="gg-poker-prod"
DATASET_ID="prod"
REGION="us-central1"

# Counters
PASSED=0
FAILED=0
TOTAL=0

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GCP Production Environment Verification${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Helper function
check_test() {
    TOTAL=$((TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} $2"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗${NC} $2"
        FAILED=$((FAILED + 1))
    fi
}

# Test 1: Project Exists
echo -e "${YELLOW}[1/12] Checking Project...${NC}"
gcloud projects describe ${PROJECT_ID} &>/dev/null
check_test $? "Project ${PROJECT_ID} exists"

# Test 2: Billing Enabled
BILLING_ENABLED=$(gcloud beta billing projects describe ${PROJECT_ID} --format="value(billingEnabled)" 2>/dev/null)
[ "$BILLING_ENABLED" = "True" ]
check_test $? "Billing enabled"
echo ""

# Test 3: APIs Enabled
echo -e "${YELLOW}[2/12] Checking APIs (15)...${NC}"
declare -a REQUIRED_APIS=(
    "run.googleapis.com"
    "bigquery.googleapis.com"
    "storage.googleapis.com"
    "dataflow.googleapis.com"
    "vision.googleapis.com"
    "aiplatform.googleapis.com"
    "pubsub.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    gcloud services list --enabled --project=${PROJECT_ID} --filter="name:${api}" --format="value(name)" | grep -q "${api}"
    check_test $? "${api}"
done
echo ""

# Test 4: Service Accounts
echo -e "${YELLOW}[3/12] Checking Service Accounts (5)...${NC}"
declare -a SERVICE_ACCOUNTS=(
    "m1-dataflow-sa"
    "m2-video-metadata-sa"
    "m3-timecode-validation-sa"
    "m4-rag-search-sa"
    "m5-clipping-sa"
)

for sa in "${SERVICE_ACCOUNTS[@]}"; do
    gcloud iam service-accounts describe ${sa}@${PROJECT_ID}.iam.gserviceaccount.com --project=${PROJECT_ID} &>/dev/null
    check_test $? "${sa}"
done
echo ""

# Test 5: IAM Permissions
echo -e "${YELLOW}[4/12] Checking IAM Permissions...${NC}"
# M1: BigQuery + Storage
gcloud projects get-iam-policy ${PROJECT_ID} --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:m1-dataflow-sa@${PROJECT_ID}.iam.gserviceaccount.com AND bindings.role:roles/bigquery.dataEditor" \
    --format="value(bindings.role)" | grep -q "bigquery.dataEditor"
check_test $? "M1: bigquery.dataEditor"

# M4: Vertex AI
gcloud projects get-iam-policy ${PROJECT_ID} --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:m4-rag-search-sa@${PROJECT_ID}.iam.gserviceaccount.com AND bindings.role:roles/aiplatform.user" \
    --format="value(bindings.role)" | grep -q "aiplatform.user"
check_test $? "M4: aiplatform.user"

# M5: Pub/Sub
gcloud projects get-iam-policy ${PROJECT_ID} --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:m5-clipping-sa@${PROJECT_ID}.iam.gserviceaccount.com AND bindings.role:roles/pubsub.editor" \
    --format="value(bindings.role)" | grep -q "pubsub.editor"
check_test $? "M5: pubsub.editor"
echo ""

# Test 6: BigQuery Dataset
echo -e "${YELLOW}[5/12] Checking BigQuery Dataset...${NC}"
bq ls -d ${PROJECT_ID}:${DATASET_ID} &>/dev/null
check_test $? "Dataset ${DATASET_ID} exists"

DATASET_LOCATION=$(bq show --format=prettyjson ${PROJECT_ID}:${DATASET_ID} | grep -o '"location": "[^"]*"' | cut -d'"' -f4)
[ "$DATASET_LOCATION" = "us-central1" ]
check_test $? "Dataset location: ${DATASET_LOCATION}"
echo ""

# Test 7: BigQuery Tables
echo -e "${YELLOW}[6/12] Checking BigQuery Tables (5)...${NC}"
declare -a TABLES=(
    "hand_summary"
    "video_files"
    "timecode_validation"
    "hand_embeddings"
    "clipping_requests"
)

for table in "${TABLES[@]}"; do
    bq show ${PROJECT_ID}:${DATASET_ID}.${table} &>/dev/null
    check_test $? "Table: ${table}"
done
echo ""

# Test 8: GCS Buckets
echo -e "${YELLOW}[7/12] Checking GCS Buckets (3)...${NC}"
declare -a BUCKETS=(
    "gg-poker-source"
    "gg-poker-proxies"
    "gg-subclips"
)

for bucket in "${BUCKETS[@]}"; do
    gsutil ls -b gs://${bucket} &>/dev/null
    check_test $? "Bucket: gs://${bucket}"
done
echo ""

# Test 9: Lifecycle Policy
echo -e "${YELLOW}[8/12] Checking Lifecycle Policy...${NC}"
LIFECYCLE=$(gsutil lifecycle get gs://gg-subclips 2>/dev/null)
echo "$LIFECYCLE" | grep -q '"age": 30'
check_test $? "Clips bucket lifecycle: 30 days"
echo ""

# Test 10: Sample Data
echo -e "${YELLOW}[9/12] Checking Sample Data...${NC}"
HAND_COUNT=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_ID}.hand_summary\`" 2>/dev/null | tail -n 1)
[ "$HAND_COUNT" -ge 20 ]
check_test $? "Hand summary data: ${HAND_COUNT} rows (expected: 20+)"

VIDEO_COUNT=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_ID}.video_files\`" 2>/dev/null | tail -n 1)
[ "$VIDEO_COUNT" -ge 1 ]
check_test $? "Video files data: ${VIDEO_COUNT} rows (expected: 1+)"
echo ""

# Test 11: Query Performance
echo -e "${YELLOW}[10/12] Testing Query Performance...${NC}"
START_TIME=$(date +%s)
bq query --use_legacy_sql=false \
    "SELECT hand_id, summary_text FROM \`${PROJECT_ID}.${DATASET_ID}.hand_summary\` LIMIT 10" &>/dev/null
END_TIME=$(date +%s)
QUERY_TIME=$((END_TIME - START_TIME))
[ $QUERY_TIME -lt 5 ]
check_test $? "Query performance: ${QUERY_TIME}s (expected: <5s)"
echo ""

# Test 12: Storage Access
echo -e "${YELLOW}[11/12] Testing Storage Access...${NC}"
echo "test" | gsutil cp - gs://gg-poker-source/test.txt &>/dev/null
check_test $? "Write to source bucket"

gsutil rm gs://gg-poker-source/test.txt &>/dev/null
check_test $? "Delete from source bucket"
echo ""

# Test 13: Overall Health
echo -e "${YELLOW}[12/12] Overall Health Check...${NC}"
[ $FAILED -eq 0 ]
check_test $? "All critical components operational"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Verification Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Total Tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "Failed: ${RED}$FAILED${NC}"
else
    echo -e "Failed: ${GREEN}0${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! GCP environment is ready.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update .env.production with actual values"
    echo "2. Deploy modules (see PRODUCTION_ROADMAP.md)"
    echo "3. Run integration tests"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Re-run: bash scripts/setup_gcp_production.sh"
    echo "2. Check permissions: gcloud projects get-iam-policy ${PROJECT_ID}"
    echo "3. Enable missing APIs manually in GCP Console"
    exit 1
fi
