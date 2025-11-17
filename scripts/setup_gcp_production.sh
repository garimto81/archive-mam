#!/bin/bash
# GCP Production Environment Setup Script
# Issue: #16 - GCP Production Environment Configuration
# Version: 1.0.0
# Usage: bash scripts/setup_gcp_production.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="gg-poker-prod"
PROJECT_NAME="POKER-BRAIN Production"
REGION="us-central1"
DATASET_ID="prod"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GCP Production Environment Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verify prerequisites
echo -e "${YELLOW}[Prerequisite Check]${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

if ! command -v bq &> /dev/null; then
    echo -e "${RED}Error: bq CLI not found. Please install BigQuery CLI.${NC}"
    exit 1
fi

if ! command -v gsutil &> /dev/null; then
    echo -e "${RED}Error: gsutil not found. Please install Google Cloud Storage utilities.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites installed${NC}"
echo ""

# Step 1: Project Creation
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 1: Create GCP Project${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "This step requires manual action:"
echo "1. Go to: https://console.cloud.google.com/projectcreate"
echo "2. Project ID: ${PROJECT_ID}"
echo "3. Project Name: ${PROJECT_NAME}"
echo "4. Enable billing for the project"
echo ""
read -p "Have you created the project and enabled billing? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Setup cancelled. Please create the project first.${NC}"
    exit 1
fi

# Set default project
echo -e "${GREEN}Setting default project...${NC}"
gcloud config set project ${PROJECT_ID}
echo ""

# Step 2: Enable APIs
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 2: Enable Required APIs (15)${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${GREEN}Enabling APIs... (this may take 2-3 minutes)${NC}"

gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  dataflow.googleapis.com \
  vision.googleapis.com \
  aiplatform.googleapis.com \
  pubsub.googleapis.com \
  compute.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=${PROJECT_ID}

echo -e "${GREEN}✓ All APIs enabled${NC}"
echo ""

# Verification
echo -e "${GREEN}Verifying enabled APIs...${NC}"
ENABLED_COUNT=$(gcloud services list --enabled --project=${PROJECT_ID} | wc -l)
echo -e "${GREEN}✓ ${ENABLED_COUNT} APIs currently enabled${NC}"
echo ""

# Step 3: Service Accounts
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 3: Create Service Accounts (5)${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

declare -a SERVICE_ACCOUNTS=(
  "m1-dataflow-sa:M1 Dataflow Service Account"
  "m2-video-metadata-sa:M2 Video Metadata Service Account"
  "m3-timecode-validation-sa:M3 Timecode Validation Service Account"
  "m4-rag-search-sa:M4 RAG Search Service Account"
  "m5-clipping-sa:M5 Clipping Service Account"
)

for sa in "${SERVICE_ACCOUNTS[@]}"; do
  IFS=':' read -r SA_NAME SA_DISPLAY_NAME <<< "$sa"
  echo -e "${GREEN}Creating ${SA_NAME}...${NC}"

  # Check if service account already exists
  if gcloud iam service-accounts describe ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --project=${PROJECT_ID} &>/dev/null; then
    echo -e "${YELLOW}  ⚠ ${SA_NAME} already exists, skipping...${NC}"
  else
    gcloud iam service-accounts create ${SA_NAME} \
      --display-name="${SA_DISPLAY_NAME}" \
      --project=${PROJECT_ID}
    echo -e "${GREEN}  ✓ Created ${SA_NAME}${NC}"
  fi
done
echo ""

# Step 4: IAM Permissions
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 4: Assign IAM Permissions${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

echo -e "${GREEN}M1 Dataflow: BigQuery + GCS${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m1-dataflow-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m1-dataflow-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" \
  --quiet

echo -e "${GREEN}M2 Video Metadata: GCS + BigQuery${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m2-video-metadata-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m2-video-metadata-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  --quiet

echo -e "${GREEN}M3 Timecode Validation: Vision API + BigQuery${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m3-timecode-validation-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/visionai.user" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m3-timecode-validation-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  --quiet

echo -e "${GREEN}M4 RAG Search: Vertex AI + BigQuery${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m4-rag-search-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m4-rag-search-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  --quiet

echo -e "${GREEN}M5 Clipping: Pub/Sub + GCS${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m5-clipping-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:m5-clipping-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" \
  --quiet

echo -e "${GREEN}✓ All IAM permissions assigned${NC}"
echo ""

# Step 5: BigQuery Dataset
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 5: Create BigQuery Dataset${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

echo -e "${GREEN}Creating dataset: ${DATASET_ID}${NC}"
if bq ls -d ${PROJECT_ID}:${DATASET_ID} &>/dev/null; then
  echo -e "${YELLOW}  ⚠ Dataset ${DATASET_ID} already exists, skipping...${NC}"
else
  bq mk -d \
    --project_id=${PROJECT_ID} \
    --location=${REGION} \
    --description="POKER-BRAIN Production Dataset" \
    ${DATASET_ID}
  echo -e "${GREEN}  ✓ Dataset created${NC}"
fi
echo ""

# Step 6: BigQuery Tables
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 6: Create BigQuery Tables (5)${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

echo -e "${GREEN}Creating table: hand_summary${NC}"
bq mk -t ${PROJECT_ID}:${DATASET_ID}.hand_summary \
  hand_id:STRING,event_id:STRING,tournament_id:STRING,table_id:STRING,\
hand_number:INTEGER,timestamp:TIMESTAMP,summary_text:STRING,\
player_names:STRING,pot_size_usd:FLOAT,created_at:TIMESTAMP \
  2>/dev/null || echo -e "${YELLOW}  ⚠ Table already exists${NC}"

echo -e "${GREEN}Creating table: video_files${NC}"
bq mk -t ${PROJECT_ID}:${DATASET_ID}.video_files \
  file_id:STRING,video_path:STRING,proxy_path:STRING,duration_seconds:FLOAT,\
resolution:STRING,codec:STRING,file_size_bytes:INTEGER,created_at:TIMESTAMP \
  2>/dev/null || echo -e "${YELLOW}  ⚠ Table already exists${NC}"

echo -e "${GREEN}Creating table: timecode_validation${NC}"
bq mk -t ${PROJECT_ID}:${DATASET_ID}.timecode_validation \
  validation_id:STRING,hand_id:STRING,video_path:STRING,sync_score:FLOAT,\
vision_confidence:FLOAT,suggested_offset:INTEGER,status:STRING,created_at:TIMESTAMP \
  2>/dev/null || echo -e "${YELLOW}  ⚠ Table already exists${NC}"

echo -e "${GREEN}Creating table: hand_embeddings${NC}"
bq mk -t ${PROJECT_ID}:${DATASET_ID}.hand_embeddings \
  hand_id:STRING,summary_text:STRING,embedding:STRING,created_at:TIMESTAMP \
  2>/dev/null || echo -e "${YELLOW}  ⚠ Table already exists${NC}"

echo -e "${GREEN}Creating table: clipping_requests${NC}"
bq mk -t ${PROJECT_ID}:${DATASET_ID}.clipping_requests \
  request_id:STRING,hand_id:STRING,status:STRING,output_gcs_path:STRING,\
download_url:STRING,created_at:TIMESTAMP,completed_at:TIMESTAMP \
  2>/dev/null || echo -e "${YELLOW}  ⚠ Table already exists${NC}"

echo -e "${GREEN}✓ All tables created${NC}"
echo ""

# Step 7: GCS Buckets
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 7: Create GCS Buckets (3)${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

declare -a BUCKETS=(
  "gg-poker-source:Source data bucket"
  "gg-poker-proxies:Proxy videos bucket"
  "gg-subclips:Clipped videos bucket"
)

for bucket in "${BUCKETS[@]}"; do
  IFS=':' read -r BUCKET_NAME BUCKET_DESC <<< "$bucket"
  echo -e "${GREEN}Creating bucket: ${BUCKET_NAME}${NC}"

  if gsutil ls -b gs://${BUCKET_NAME} &>/dev/null; then
    echo -e "${YELLOW}  ⚠ Bucket already exists, skipping...${NC}"
  else
    gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${BUCKET_NAME}
    echo -e "${GREEN}  ✓ Created gs://${BUCKET_NAME}${NC}"
  fi
done
echo ""

# Step 8: Lifecycle Policy
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Step 8: Configure Lifecycle Policy${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

echo -e "${GREEN}Setting lifecycle policy for gs://gg-subclips (30 days)${NC}"
cat > /tmp/lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json gs://gg-subclips
rm /tmp/lifecycle.json
echo -e "${GREEN}✓ Lifecycle policy configured${NC}"
echo ""

# Final Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Resources Created:${NC}"
echo "  • Project: ${PROJECT_ID}"
echo "  • APIs: 15 enabled"
echo "  • Service Accounts: 5"
echo "  • BigQuery Dataset: ${DATASET_ID}"
echo "  • BigQuery Tables: 5"
echo "  • GCS Buckets: 3"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set up billing budget and alerts (Manual - See docs/GCP_SETUP_CHECKLIST.md)"
echo "2. Upload sample data: bash scripts/upload_sample_data.sh"
echo "3. Verify all resources: bash scripts/verify_gcp_setup.sh"
echo ""
echo -e "${GREEN}Done! 🎉${NC}"
