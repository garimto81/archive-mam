#!/bin/bash
# Deployment script for M1 Data Ingestion Service to Cloud Run

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"gg-poker"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="m1-data-ingestion"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
VERSION="1.0.0"

echo "🚀 Deploying M1 Data Ingestion Service"
echo "======================================"
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Service:  ${SERVICE_NAME}"
echo "Version:  ${VERSION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Build and push image
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}:${VERSION} --tag ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:${VERSION} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8001 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300 \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},DATASET=prod,TABLE=hand_summary,ENVIRONMENT=production,REGION=${REGION}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📋 Health check:"
curl -s ${SERVICE_URL}/health | jq .

echo ""
echo "🎉 M1 Data Ingestion Service is live!"
