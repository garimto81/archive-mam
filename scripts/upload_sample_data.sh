#!/bin/bash
# Upload Sample Data to GCP BigQuery
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
MOCK_DATA_DIR="mock_data/bigquery"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Upload Sample Data to BigQuery${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verify prerequisites
if ! command -v bq &> /dev/null; then
    echo -e "${RED}Error: bq CLI not found${NC}"
    exit 1
fi

# Check if mock data exists
if [ ! -d "$MOCK_DATA_DIR" ]; then
    echo -e "${RED}Error: Mock data directory not found: $MOCK_DATA_DIR${NC}"
    exit 1
fi

# Set default project
gcloud config set project ${PROJECT_ID}
echo ""

# Upload hand_summary
echo -e "${GREEN}Uploading hand_summary data...${NC}"
if [ -f "$MOCK_DATA_DIR/hand_summary_real.json" ]; then
    bq load --source_format=NEWLINE_DELIMITED_JSON \
        --replace \
        ${PROJECT_ID}:${DATASET_ID}.hand_summary \
        $MOCK_DATA_DIR/hand_summary_real.json
    echo -e "${GREEN}✓ hand_summary uploaded${NC}"
else
    echo -e "${YELLOW}⚠ hand_summary_real.json not found, using mock data${NC}"
    if [ -f "$MOCK_DATA_DIR/hand_summary_mock.json" ]; then
        bq load --source_format=NEWLINE_DELIMITED_JSON \
            --replace \
            ${PROJECT_ID}:${DATASET_ID}.hand_summary \
            $MOCK_DATA_DIR/hand_summary_mock.json
        echo -e "${GREEN}✓ hand_summary (mock) uploaded${NC}"
    else
        echo -e "${RED}✗ No hand_summary data found${NC}"
    fi
fi
echo ""

# Upload video_files
echo -e "${GREEN}Uploading video_files data...${NC}"
if [ -f "$MOCK_DATA_DIR/video_files_real.json" ]; then
    bq load --source_format=NEWLINE_DELIMITED_JSON \
        --replace \
        ${PROJECT_ID}:${DATASET_ID}.video_files \
        $MOCK_DATA_DIR/video_files_real.json
    echo -e "${GREEN}✓ video_files uploaded${NC}"
else
    echo -e "${YELLOW}⚠ video_files_real.json not found, using mock data${NC}"
    if [ -f "$MOCK_DATA_DIR/video_files_mock.json" ]; then
        bq load --source_format=NEWLINE_DELIMITED_JSON \
            --replace \
            ${PROJECT_ID}:${DATASET_ID}.video_files \
            $MOCK_DATA_DIR/video_files_mock.json
        echo -e "${GREEN}✓ video_files (mock) uploaded${NC}"
    else
        echo -e "${RED}✗ No video_files data found${NC}"
    fi
fi
echo ""

# Upload embeddings
echo -e "${GREEN}Uploading hand_embeddings data...${NC}"
EMBEDDINGS_FILE="mock_data/embeddings/hand_embeddings_real.json"
if [ ! -f "$EMBEDDINGS_FILE" ]; then
    EMBEDDINGS_FILE="mock_data/embeddings/hand_embeddings_mock.json"
fi

if [ -f "$EMBEDDINGS_FILE" ]; then
    bq load --source_format=NEWLINE_DELIMITED_JSON \
        --replace \
        ${PROJECT_ID}:${DATASET_ID}.hand_embeddings \
        $EMBEDDINGS_FILE
    echo -e "${GREEN}✓ hand_embeddings uploaded${NC}"
else
    echo -e "${YELLOW}⚠ No embeddings data found, skipping${NC}"
fi
echo ""

# Verify uploads
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Verification${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${GREEN}hand_summary:${NC}"
HAND_COUNT=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_ID}.hand_summary\`" | tail -n 1)
echo "  Total hands: $HAND_COUNT"

echo -e "${GREEN}video_files:${NC}"
VIDEO_COUNT=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_ID}.video_files\`" | tail -n 1)
echo "  Total videos: $VIDEO_COUNT"

echo -e "${GREEN}hand_embeddings:${NC}"
EMBEDDING_COUNT=$(bq query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_ID}.hand_embeddings\`" | tail -n 1)
echo "  Total embeddings: $EMBEDDING_COUNT"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Upload Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  • Hands: $HAND_COUNT"
echo "  • Videos: $VIDEO_COUNT"
echo "  • Embeddings: $EMBEDDING_COUNT"
echo ""
echo -e "${GREEN}Done! 🎉${NC}"
