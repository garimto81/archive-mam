# M2 Video Metadata Service - Deployment Guide

## Pre-Deployment Checklist

### 1. GCP Resources Setup

#### BigQuery Table

```bash
# Create dataset if not exists
bq mk --dataset --location=us-central1 gg-poker:prod

# Create video_files table
bq mk --table \
  gg-poker:prod.video_files \
  video_id:STRING,event_id:STRING,tournament_day:INTEGER,table_number:INTEGER,\
  nas_file_path:STRING,file_name:STRING,gcs_proxy_path:STRING,\
  duration_seconds:INTEGER,resolution:STRING,codec:STRING,\
  bitrate_kbps:INTEGER,fps:FLOAT,file_size_bytes:INTEGER,proxy_size_bytes:INTEGER,\
  created_at:TIMESTAMP,scanned_at:TIMESTAMP,indexed_at:TIMESTAMP

# Verify table
bq show gg-poker:prod.video_files
```

#### GCS Bucket

```bash
# Create bucket for proxy videos
gsutil mb -c STANDARD -l us-central1 gs://gg-poker-proxy

# Set lifecycle policy (optional - delete after 90 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://gg-poker-proxy

# Verify bucket
gsutil ls -L -b gs://gg-poker-proxy
```

#### Service Account

```bash
# Create service account
gcloud iam service-accounts create m2-video-metadata \
  --display-name="M2 Video Metadata Service"

# Grant permissions
gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:m2-video-metadata@gg-poker.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding gg-poker \
  --member="serviceAccount:m2-video-metadata@gg-poker.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Create key for local development
gcloud iam service-accounts keys create m2-service-account.json \
  --iam-account=m2-video-metadata@gg-poker.iam.gserviceaccount.com
```

### 2. NAS Mount Setup

#### Linux/macOS

```bash
# Install NFS client
# Ubuntu/Debian
sudo apt-get install nfs-common

# macOS (already installed)

# Create mount point
sudo mkdir -p /nas/poker

# Mount NAS (example)
sudo mount -t nfs \
  -o ro,soft,timeo=30,retrans=3 \
  nas-server.example.com:/poker \
  /nas/poker

# Add to /etc/fstab for auto-mount
echo "nas-server.example.com:/poker /nas/poker nfs ro,soft,timeo=30,retrans=3 0 0" | sudo tee -a /etc/fstab

# Verify mount
df -h | grep /nas
```

#### Windows

```cmd
# Map network drive
net use Z: \\nas-server\poker /persistent:yes

# Or use mount command
mount \\nas-server\poker Z:
```

### 3. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/m2-service-account.json
export GCP_PROJECT_ID=gg-poker
export NAS_BASE_PATH=/nas/poker

# Run tests
pytest tests/ -v --cov=app

# Run service locally
python -m app.api

# Test health endpoint
curl http://localhost:8002/health
```

## Deployment Methods

### Method 1: Cloud Run (Recommended)

#### Build and Deploy

```bash
# 1. Build Docker image
gcloud builds submit --tag gcr.io/gg-poker/m2-video-metadata

# 2. Deploy to Cloud Run
gcloud run deploy m2-video-metadata \
  --image gcr.io/gg-poker/m2-video-metadata \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account m2-video-metadata@gg-poker.iam.gserviceaccount.com \
  --port 8002 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 10 \
  --min-instances 1 \
  --max-instances 5 \
  --set-env-vars "GCP_PROJECT_ID=gg-poker,GCS_BUCKET=gg-poker-proxy,LOG_LEVEL=INFO"

# 3. Get service URL
gcloud run services describe m2-video-metadata \
  --region=us-central1 \
  --format='value(status.url)'
```

#### Update Deployment

```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/gg-poker/m2-video-metadata
gcloud run deploy m2-video-metadata \
  --image gcr.io/gg-poker/m2-video-metadata \
  --region us-central1
```

#### Configure NAS Access

**Note**: Cloud Run doesn't support NFS mounts directly. Options:

1. **Cloud Storage FUSE** (Recommended):
```bash
# Mount GCS bucket as filesystem
gcsfuse gg-poker-nas /nas/poker
```

2. **Cloud Filestore**:
```bash
# Create Filestore instance
gcloud filestore instances create poker-nas \
  --location=us-central1-a \
  --tier=BASIC_HDD \
  --file-share=name="poker",capacity=1TB \
  --network=name="default"
```

3. **Pre-copy files to GCS** (For testing):
```bash
gsutil -m rsync -r /nas/poker gs://gg-poker-nas
```

### Method 2: Compute Engine VM

#### Create VM

```bash
# Create VM with sufficient resources
gcloud compute instances create m2-video-metadata-vm \
  --machine-type=n2-standard-4 \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --service-account=m2-video-metadata@gg-poker.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y python3-pip ffmpeg nfs-common docker.io
    systemctl start docker
    systemctl enable docker'
```

#### Deploy to VM

```bash
# SSH to VM
gcloud compute ssh m2-video-metadata-vm --zone=us-central1-a

# Clone repository or copy files
git clone https://github.com/your-org/poker-brain.git
cd poker-brain/modules/m2-video-metadata

# Build and run Docker container
docker build -t m2-video-metadata .
docker run -d \
  --name m2-video-metadata \
  --restart always \
  -p 8002:8002 \
  -v /nas/poker:/nas/poker:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  -e GCP_PROJECT_ID=gg-poker \
  m2-video-metadata
```

### Method 3: Kubernetes (GKE)

#### Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: m2-video-metadata
  namespace: poker-brain
spec:
  replicas: 2
  selector:
    matchLabels:
      app: m2-video-metadata
  template:
    metadata:
      labels:
        app: m2-video-metadata
    spec:
      serviceAccountName: m2-video-metadata
      containers:
      - name: m2-video-metadata
        image: gcr.io/gg-poker/m2-video-metadata:latest
        ports:
        - containerPort: 8002
        env:
        - name: GCP_PROJECT_ID
          value: "gg-poker"
        - name: GCS_BUCKET
          value: "gg-poker-proxy"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: nas-poker
          mountPath: /nas/poker
          readOnly: true
      volumes:
      - name: nas-poker
        nfs:
          server: nas-server.example.com
          path: /poker
          readOnly: true
---
apiVersion: v1
kind: Service
metadata:
  name: m2-video-metadata
  namespace: poker-brain
spec:
  selector:
    app: m2-video-metadata
  ports:
  - port: 80
    targetPort: 8002
  type: LoadBalancer
```

#### Deploy to GKE

```bash
# Apply deployment
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -n poker-brain
kubectl get svc -n poker-brain

# View logs
kubectl logs -n poker-brain -l app=m2-video-metadata --follow
```

## Post-Deployment

### 1. Verify Service

```bash
SERVICE_URL="https://m2-video-metadata-xxxxx.run.app"

# Health check
curl $SERVICE_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "dependencies": {
#     "nas": "ok",
#     "bigquery": "ok",
#     "gcs": "ok"
#   }
# }
```

### 2. Run Test Scan

```bash
# Start scan
curl -X POST $SERVICE_URL/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "nas_path": "/nas/poker/test/",
    "recursive": true,
    "generate_proxy": false
  }'

# Response:
# {
#   "scan_id": "scan-20241117-001",
#   "status": "queued"
# }

# Check status
curl $SERVICE_URL/v1/scan/scan-20241117-001/status
```

### 3. Configure Monitoring

#### Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=m2-video-metadata" \
  --limit 50 \
  --format json
```

#### Cloud Monitoring

```bash
# Create uptime check
gcloud monitoring uptime-checks create health-check \
  --display-name="M2 Video Metadata Health Check" \
  --resource-type=uptime-url \
  --monitored-resource=https://m2-video-metadata-xxxxx.run.app/health \
  --period=60
```

#### Alerts

```yaml
# alert-policy.yaml
displayName: "M2 Video Metadata - High Error Rate"
conditions:
- displayName: "Error rate > 10%"
  conditionThreshold:
    filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="m2-video-metadata" AND severity="ERROR"'
    comparison: COMPARISON_GT
    thresholdValue: 10
    duration: 300s
notificationChannels:
- projects/gg-poker/notificationChannels/email-alerts
```

### 4. Schedule Regular Scans

#### Cloud Scheduler

```bash
# Create cron job to scan NAS daily at 2 AM
gcloud scheduler jobs create http daily-nas-scan \
  --schedule="0 2 * * *" \
  --uri="https://m2-video-metadata-xxxxx.run.app/v1/scan" \
  --http-method=POST \
  --message-body='{"nas_path":"/nas/poker/","recursive":true,"generate_proxy":true}' \
  --headers="Content-Type=application/json"
```

## Rollback

### Cloud Run Rollback

```bash
# List revisions
gcloud run revisions list --service=m2-video-metadata --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic m2-video-metadata \
  --region=us-central1 \
  --to-revisions=m2-video-metadata-00002-xxx=100
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
gcloud run services logs read m2-video-metadata --region=us-central1

# Common issues:
# 1. Service account permissions
# 2. Missing environment variables
# 3. NAS mount failure
```

### High Memory Usage

```bash
# Increase memory limit
gcloud run services update m2-video-metadata \
  --region=us-central1 \
  --memory=8Gi
```

### Slow Proxy Generation

```bash
# Increase CPU
gcloud run services update m2-video-metadata \
  --region=us-central1 \
  --cpu=4
```

## Performance Tuning

### Optimize FFmpeg Settings

```python
# In proxy_generator.py, adjust:
- preset='ultrafast'  # Faster encoding, larger files
- preset='slow'       # Slower encoding, smaller files
- crf=18             # Higher quality (18)
- crf=28             # Lower quality (28)
```

### Increase Concurrency

```bash
# Allow more concurrent requests
gcloud run services update m2-video-metadata \
  --region=us-central1 \
  --concurrency=20
```

## Cost Optimization

### Estimated Monthly Costs

| Resource | Usage | Cost |
|----------|-------|------|
| Cloud Run | 2 instances, 4GB RAM | $50-100 |
| Cloud Storage | 10TB proxies | $200 |
| BigQuery | 10M rows | $10 |
| **Total** | | **$260-310/month** |

### Optimization Tips

1. **Use preemptible VMs** instead of Cloud Run for batch processing
2. **Set GCS lifecycle** to delete old proxies after 90 days
3. **Use lower proxy quality** (CRF 28 instead of 23)
4. **Enable Cloud CDN** for proxy delivery

## Security

### Enable IAP (Identity-Aware Proxy)

```bash
# Restrict access to authenticated users only
gcloud run services update m2-video-metadata \
  --region=us-central1 \
  --no-allow-unauthenticated

# Add IAM binding for authorized users
gcloud run services add-iam-policy-binding m2-video-metadata \
  --region=us-central1 \
  --member="user:authorized-user@example.com" \
  --role="roles/run.invoker"
```

## Maintenance

### Update Dependencies

```bash
# Update Python packages
pip list --outdated
pip install -U package-name

# Rebuild and redeploy
gcloud builds submit --tag gcr.io/gg-poker/m2-video-metadata
```

### Database Maintenance

```bash
# Optimize BigQuery table (partition/cluster)
bq update --time_partitioning_field=indexed_at \
  --clustering_fields=event_id,tournament_day \
  gg-poker:prod.video_files
```

## Support

- **Documentation**: See README.md
- **Issues**: Create GitHub issue
- **Contact**: aiden.kim@ggproduction.net
