# M3 Timecode Validation Service - Deployment Guide

**Version**: 1.0.0
**Last Updated**: 2025-01-17

---

## Pre-Deployment Checklist

### 1. Code Quality

- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] Pylint score > 8.0
- [ ] No critical security issues
- [ ] All TODO comments resolved

```bash
# Run full test suite
bash run_tests.sh

# Expected output: All tests PASSED, Coverage > 80%
```

### 2. Environment Configuration

- [ ] GCP project ID set: `gg-poker`
- [ ] Service account created: `timecode-validation-sa@gg-poker.iam.gserviceaccount.com`
- [ ] IAM permissions granted:
  - BigQuery Data Editor
  - Vision API User
  - Storage Object Viewer
- [ ] Environment variables documented

### 3. Dependencies

- [ ] M1 (hand_summary) table ready
- [ ] M2 (video_files) table ready
- [ ] BigQuery output table created: `prod.timecode_validation`
- [ ] GCS bucket created: `gs://gg-poker-validation-frames`

---

## Deployment Steps

### Step 1: Build Docker Image

```bash
# Navigate to module directory
cd modules/m3-timecode-validation

# Build Docker image
docker build -t gcr.io/gg-poker/m3-timecode-validation:1.0.0 .

# Test locally
docker run -p 8003:8003 \
  -e POKER_ENV=development \
  -e VISION_API_ENABLED=false \
  gcr.io/gg-poker/m3-timecode-validation:1.0.0

# Verify health
curl http://localhost:8003/health
# Expected: {"status": "healthy", ...}
```

### Step 2: Push to Google Container Registry

```bash
# Authenticate Docker with GCP
gcloud auth configure-docker

# Push image
docker push gcr.io/gg-poker/m3-timecode-validation:1.0.0

# Verify image in GCR
gcloud container images list --repository=gcr.io/gg-poker
```

### Step 3: Deploy to Cloud Run (Development)

```bash
# Deploy development environment
gcloud run deploy m3-timecode-validation-dev \
  --image gcr.io/gg-poker/m3-timecode-validation:1.0.0 \
  --region us-central1 \
  --platform managed \
  --set-env-vars="POKER_ENV=development,VISION_API_ENABLED=false" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 120s \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 80 \
  --allow-unauthenticated \
  --project gg-poker

# Get service URL
gcloud run services describe m3-timecode-validation-dev \
  --region us-central1 \
  --format='value(status.url)'

# Test deployment
DEV_URL=$(gcloud run services describe m3-timecode-validation-dev --region us-central1 --format='value(status.url)')
curl $DEV_URL/health
```

### Step 4: Deploy to Cloud Run (Production)

```bash
# Deploy production environment
gcloud run deploy m3-timecode-validation \
  --image gcr.io/gg-poker/m3-timecode-validation:1.0.0 \
  --region us-central1 \
  --platform managed \
  --set-env-vars="POKER_ENV=production,VISION_API_ENABLED=true" \
  --memory 4Gi \
  --cpu 4 \
  --timeout 120s \
  --max-instances 50 \
  --min-instances 2 \
  --concurrency 80 \
  --service-account timecode-validation-sa@gg-poker.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --project gg-poker

# Get service URL
gcloud run services describe m3-timecode-validation \
  --region us-central1 \
  --format='value(status.url)'
```

### Step 5: Verify Deployment

```bash
# Get production URL
PROD_URL=$(gcloud run services describe m3-timecode-validation --region us-central1 --format='value(status.url)')

# Test health endpoint (requires authentication)
gcloud run services proxy m3-timecode-validation \
  --region us-central1 &

curl http://localhost:8080/health

# Expected output:
# {
#   "status": "healthy",
#   "environment": "production",
#   "version": "1.0.0",
#   "dependencies": {
#     "vision_api": "ok",
#     "bigquery": "ok",
#     "ffmpeg": "ok"
#   }
# }
```

---

## Post-Deployment Tasks

### 1. Smoke Tests

Run smoke tests against production:

```bash
# Test validation endpoint
curl -X POST $PROD_URL/v1/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -d '{
    "hand_id": "wsop2024_me_d1_h001",
    "timestamp_start_utc": "2024-07-15T15:24:15Z",
    "timestamp_end_utc": "2024-07-15T15:26:45Z",
    "nas_video_path": "/nas/poker/2024/wsop/me_d1.mp4",
    "use_vision_api": true
  }'

# Verify validation result
# Get validation_id from response, then:
curl $PROD_URL/v1/validate/{validation_id}/result \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"

# Check stats
curl $PROD_URL/v1/stats \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### 2. Monitoring Setup

Set up Cloud Monitoring alerts:

```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="M3 High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

### 3. Logging

View logs in Cloud Logging:

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=m3-timecode-validation" \
  --limit 50 \
  --format json

# Filter by error level
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=m3-timecode-validation AND severity>=ERROR" \
  --limit 20
```

---

## Rollback Procedure

If deployment fails or issues are detected:

```bash
# 1. List revisions
gcloud run revisions list \
  --service m3-timecode-validation \
  --region us-central1

# 2. Rollback to previous revision
gcloud run services update-traffic m3-timecode-validation \
  --to-revisions PREVIOUS_REVISION=100 \
  --region us-central1

# 3. Verify rollback
curl $PROD_URL/health
```

---

## Scaling Configuration

### Auto-Scaling Metrics

- **Min instances**: 2 (production), 0 (development)
- **Max instances**: 50 (production), 10 (development)
- **Concurrency**: 80 requests per instance
- **CPU allocation**: 4 CPUs (production), 2 CPUs (development)
- **Memory**: 4Gi (production), 2Gi (development)

### Expected Load

| Metric | Development | Production |
|--------|-------------|------------|
| Requests/second | < 10 | 100-500 |
| Avg response time | < 15s | < 10s |
| P95 response time | < 30s | < 20s |
| Error rate | < 10% | < 5% |

---

## Cost Estimation

### Cloud Run Costs (Monthly)

**Production**:
- CPU: 4 vCPU × $0.00002400/vCPU-second × 2,592,000 seconds/month × 0.5 utilization = $124.42
- Memory: 4Gi × $0.00000250/GiB-second × 2,592,000 seconds/month × 0.5 utilization = $12.96
- Requests: 10M requests/month × $0.40/million = $4.00
- **Total**: ~$141/month

**Development**:
- CPU: 2 vCPU × $0.00002400/vCPU-second × 0.1 utilization = $12.44
- Memory: 2Gi × $0.00000250/GiB-second × 0.1 utilization = $1.30
- Requests: 100K requests/month × $0.40/million = $0.04
- **Total**: ~$14/month

### Vision API Costs

- 1000 requests/month: $1.50/1000 = **$1.50/month**
- 10,000 requests/month: $15.00/month

### BigQuery Costs

- Storage: 10GB × $0.02/GB/month = **$0.20/month**
- Queries: Minimal (reads from M1/M2)

**Total Estimated Cost**: $160-$170/month (production + development)

---

## Troubleshooting Deployment Issues

### Issue 1: Container fails to start

**Symptom**: Cloud Run shows "Container failed to start"

**Solution**:
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=m3-timecode-validation" \
  --limit 50

# Common causes:
# - Missing environment variables
# - FFmpeg not installed in container
# - Port mismatch (ensure PORT=8003)
```

### Issue 2: Vision API 403 Forbidden

**Symptom**: Vision API returns 403 errors

**Solution**:
```bash
# Check service account permissions
gcloud projects get-iam-policy gg-poker \
  --flatten="bindings[].members" \
  --filter="bindings.members:timecode-validation-sa@gg-poker.iam.gserviceaccount.com"

# Add Vision API permission
gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:timecode-validation-sa@gg-poker.iam.gserviceaccount.com" \
  --role="roles/visionai.admin"
```

### Issue 3: BigQuery access denied

**Symptom**: BigQuery queries fail with "Access Denied"

**Solution**:
```bash
# Grant BigQuery access
gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:timecode-validation-sa@gg-poker.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

---

## Security Considerations

1. **Authentication**: Production requires IAP or service account authentication
2. **Secrets**: Never commit GCP credentials to Git
3. **Network**: Use VPC connector for internal services
4. **Logging**: Sanitize logs to remove sensitive data

---

## Deployment Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Build Docker image | 5 min | Multi-stage build |
| Push to GCR | 2 min | ~500MB image |
| Deploy to Cloud Run | 3 min | Cold start |
| Smoke tests | 5 min | Manual verification |
| **Total** | **15 min** | Per environment |

---

## Contact

**Deployment Support**: aiden.kim@ggproduction.net
**On-Call**: #poker-brain-alerts (Slack)
**Runbook**: `docs/runbook.md`

---

**Last Updated**: 2025-01-17
**Deployed By**: Charlie (M3 Agent)
