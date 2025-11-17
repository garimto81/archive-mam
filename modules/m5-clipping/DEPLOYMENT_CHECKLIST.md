# M5 Clipping Service - Deployment Checklist

Use this checklist to ensure successful deployment to staging and production environments.

## Pre-Deployment Checklist

### Code Preparation

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Test coverage >= 80%: `pytest tests/ --cov=app --cov=local_agent`
- [ ] No hardcoded secrets in code
- [ ] `.env.example` updated with all required variables
- [ ] Documentation updated (README.md, QUICK_START.md)
- [ ] Version number updated in `__init__.py` files

### Environment Configuration

- [ ] GCP project created (staging/production)
- [ ] Pub/Sub topics created:
  - [ ] `clipping-requests`
  - [ ] `clipping-complete`
- [ ] Pub/Sub subscriptions created:
  - [ ] `clipping-requests-sub`
- [ ] GCS bucket created: `gg-subclips` (or configured name)
- [ ] GCS lifecycle policy configured (30-day auto-delete)
- [ ] Service account created with permissions:
  - [ ] Pub/Sub Publisher
  - [ ] Pub/Sub Subscriber
  - [ ] Storage Object Creator
  - [ ] Storage Object Viewer

## Staging Deployment

### 1. Flask API (Cloud Run)

- [ ] Build Docker image:
  ```bash
  docker build -t gcr.io/gg-poker-staging/m5-clipping:v1.0.0 .
  ```

- [ ] Test Docker image locally:
  ```bash
  docker run -p 8005:8005 \
    -e POKER_ENV=production \
    -e GCP_PROJECT_ID=gg-poker-staging \
    gcr.io/gg-poker-staging/m5-clipping:v1.0.0
  ```

- [ ] Push to Google Container Registry:
  ```bash
  docker push gcr.io/gg-poker-staging/m5-clipping:v1.0.0
  ```

- [ ] Deploy to Cloud Run:
  ```bash
  gcloud run deploy m5-clipping \
    --image gcr.io/gg-poker-staging/m5-clipping:v1.0.0 \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars POKER_ENV=production,GCP_PROJECT_ID=gg-poker-staging
  ```

- [ ] Verify deployment:
  ```bash
  curl https://m5-clipping-<hash>.run.app/health
  ```

### 2. Local Agent (Staging NAS Server)

- [ ] Copy files to staging NAS:
  ```bash
  scp -r . poker@staging-nas:/opt/poker-brain/m5-clipping/
  ```

- [ ] SSH to staging NAS and install:
  ```bash
  ssh poker@staging-nas
  cd /opt/poker-brain/m5-clipping
  python3.11 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] Configure environment:
  ```bash
  cp .env.example .env
  # Edit .env with staging values
  ```

- [ ] Install and start systemd service:
  ```bash
  sudo cp local_agent/systemd/clipping-agent.service /etc/systemd/system/
  # Edit service file with correct paths
  sudo systemctl daemon-reload
  sudo systemctl enable clipping-agent
  sudo systemctl start clipping-agent
  ```

- [ ] Verify agent status:
  ```bash
  sudo systemctl status clipping-agent
  sudo journalctl -u clipping-agent -f
  ```

### 3. Integration Testing (Staging)

- [ ] Submit test clipping request:
  ```bash
  curl -X POST https://m5-clipping-<hash>.run.app/v1/clip/request \
    -H "Content-Type: application/json" \
    -d '{
      "hand_id": "test_staging_001",
      "nas_video_path": "/nas/poker/test.mp4",
      "start_seconds": 10,
      "end_seconds": 60,
      "output_quality": "high"
    }'
  ```

- [ ] Check status until completed:
  ```bash
  curl https://m5-clipping-<hash>.run.app/v1/clip/<request_id>/status
  ```

- [ ] Get download URL:
  ```bash
  curl https://m5-clipping-<hash>.run.app/v1/clip/<request_id>/download
  ```

- [ ] Verify clip was created in GCS:
  ```bash
  gsutil ls gs://gg-subclips/
  ```

- [ ] Download and verify clip plays correctly

- [ ] Test error cases:
  - [ ] Invalid time range (start > end)
  - [ ] Excessive duration (> 10 minutes)
  - [ ] Non-existent video file
  - [ ] Invalid hand_id format

- [ ] Test high availability:
  - [ ] Stop primary agent
  - [ ] Verify standby takes over (if configured)
  - [ ] Submit new request
  - [ ] Verify processing continues

- [ ] Load testing (optional):
  ```bash
  # Submit 100 concurrent requests
  for i in {1..100}; do
    curl -X POST https://m5-clipping-<hash>.run.app/v1/clip/request \
      -H "Content-Type: application/json" \
      -d "{...}" &
  done
  wait
  ```

### 4. Monitoring Setup (Staging)

- [ ] Configure Cloud Monitoring alerts:
  - [ ] API response time > 1s
  - [ ] Error rate > 5%
  - [ ] Agent down for > 2 minutes
  - [ ] GCS upload failures

- [ ] Set up log aggregation:
  - [ ] Cloud Logging for API
  - [ ] systemd journal for agent

- [ ] Create monitoring dashboard with:
  - [ ] Request rate
  - [ ] Success/failure rate
  - [ ] Processing time (avg, p95, p99)
  - [ ] Queue depth
  - [ ] GCS storage usage

## Production Deployment

### Pre-Production Checklist

- [ ] All staging tests passed
- [ ] No critical bugs in staging
- [ ] Performance benchmarks met:
  - [ ] API response < 100ms
  - [ ] Clipping time ~30s for 2-min clip
  - [ ] Success rate > 95%
- [ ] Security review completed
- [ ] Disaster recovery plan documented
- [ ] Rollback plan documented

### 1. Flask API (Production Cloud Run)

- [ ] Build production Docker image:
  ```bash
  docker build -t gcr.io/gg-poker-prod/m5-clipping:v1.0.0 .
  ```

- [ ] Push to production GCR:
  ```bash
  docker push gcr.io/gg-poker-prod/m5-clipping:v1.0.0
  ```

- [ ] Deploy to production Cloud Run:
  ```bash
  gcloud run deploy m5-clipping \
    --image gcr.io/gg-poker-prod/m5-clipping:v1.0.0 \
    --platform managed \
    --region us-central1 \
    --set-env-vars POKER_ENV=production,GCP_PROJECT_ID=gg-poker-prod \
    --min-instances 1 \
    --max-instances 10 \
    --cpu 2 \
    --memory 4Gi
  ```

- [ ] Configure custom domain (optional):
  ```bash
  gcloud run domain-mappings create \
    --service m5-clipping \
    --domain clipping.ggproduction.net
  ```

### 2. Local Agents (Production NAS Servers)

#### Primary Agent (nas-server-01)

- [ ] Deploy primary agent following same steps as staging
- [ ] Set `AGENT_ID=nas-server-01`, `AGENT_ROLE=primary`
- [ ] Verify agent running and processing requests

#### Standby Agent (nas-server-02)

- [ ] Deploy standby agent following same steps
- [ ] Set `AGENT_ID=nas-server-02`, `AGENT_ROLE=standby`
- [ ] Verify agent subscribed to same subscription
- [ ] Test failover:
  - [ ] Stop primary agent
  - [ ] Submit request
  - [ ] Verify standby processes it
  - [ ] Restart primary

### 3. Production Smoke Tests

- [ ] Submit production clipping request
- [ ] Verify completion within expected time
- [ ] Download clip and verify quality
- [ ] Check all monitoring dashboards
- [ ] Verify logs are being collected

### 4. Production Monitoring

- [ ] Verify all alerts configured:
  - [ ] PagerDuty/Slack integration
  - [ ] On-call rotation configured
  - [ ] Escalation policy defined

- [ ] Set up weekly reports:
  - [ ] Request volume
  - [ ] Success/failure rates
  - [ ] Processing times
  - [ ] Cost analysis

## Post-Deployment

### Documentation

- [ ] Update internal documentation with:
  - [ ] Production URLs
  - [ ] Monitoring dashboard links
  - [ ] On-call procedures
  - [ ] Troubleshooting guide

- [ ] Share with stakeholders:
  - [ ] M6 team (API consumers)
  - [ ] DevOps team
  - [ ] Support team

### Handoff

- [ ] Demo to stakeholders
- [ ] Training session for support team
- [ ] Runbook created for common issues
- [ ] Knowledge transfer session

## Rollback Plan

If issues occur in production:

1. **Immediate Rollback (API)**:
   ```bash
   gcloud run services update-traffic m5-clipping \
     --to-revisions <previous-revision>=100
   ```

2. **Immediate Rollback (Agent)**:
   ```bash
   ssh poker@nas-server-01
   sudo systemctl stop clipping-agent
   cd /opt/poker-brain/m5-clipping-backup
   sudo systemctl start clipping-agent
   ```

3. **Verify Rollback**:
   - [ ] Check health endpoints
   - [ ] Submit test request
   - [ ] Monitor error rates

4. **Incident Post-Mortem**:
   - [ ] Document what went wrong
   - [ ] Root cause analysis
   - [ ] Action items to prevent recurrence

## Sign-Off

### Staging Deployment

- [ ] Developer: __________________ Date: __________
- [ ] QA Lead: __________________ Date: __________
- [ ] DevOps: __________________ Date: __________

### Production Deployment

- [ ] Developer: __________________ Date: __________
- [ ] QA Lead: __________________ Date: __________
- [ ] DevOps: __________________ Date: __________
- [ ] Engineering Manager: __________________ Date: __________

---

**Deployment Guide Version**: 1.0.0
**Last Updated**: 2024-11-17
**Maintained By**: Eve (M5 Clipping Service Agent)
