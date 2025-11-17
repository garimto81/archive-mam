# GCP Production Setup Checklist

**Issue**: #16 - GCP Production Environment Configuration
**Version**: 1.0.0
**Last Updated**: 2025-01-17
**Estimated Time**: 1 week (7 days)

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] Google Cloud account with **Owner** or **Editor** role
- [ ] Billing account enabled and linked
- [ ] `gcloud` CLI installed and authenticated
  ```bash
  gcloud --version
  gcloud auth login
  ```
- [ ] `bq` CLI installed (part of gcloud)
- [ ] `gsutil` CLI installed (part of gcloud)
- [ ] Access to billing account ID

---

## 🚀 Day 1: Project & APIs

### Step 1.1: Create GCP Project

**Manual Steps** (GCP Console):
1. Go to: https://console.cloud.google.com/projectcreate
2. Fill in:
   - **Project ID**: `gg-poker-prod`
   - **Project Name**: `POKER-BRAIN Production`
   - **Organization**: (Optional)
3. Click "Create"

**Verification**:
```bash
gcloud projects describe gg-poker-prod
```

- [ ] Project created
- [ ] Project ID confirmed: `gg-poker-prod`

---

### Step 1.2: Link Billing Account

**Manual Steps** (GCP Console):
1. Go to: https://console.cloud.google.com/billing/linkedaccount?project=gg-poker-prod
2. Select your billing account
3. Click "Set Account"

**CLI Alternative**:
```bash
# Find your billing account ID
gcloud billing accounts list

# Link to project
gcloud billing projects link gg-poker-prod \
  --billing-account=XXXXXX-YYYYYY-ZZZZZZ
```

**Verification**:
```bash
gcloud billing projects describe gg-poker-prod
```

- [ ] Billing account linked
- [ ] Billing enabled confirmed

---

### Step 1.3: Set Default Project

```bash
gcloud config set project gg-poker-prod
```

**Verification**:
```bash
gcloud config get-value project
# Output: gg-poker-prod
```

- [ ] Default project set

---

### Step 1.4: Enable Required APIs (15)

**Automated** (Run setup script):
```bash
bash scripts/setup_gcp_production.sh
```

**Manual** (If script fails):
```bash
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
  --project=gg-poker-prod
```

**Verification**:
```bash
gcloud services list --enabled --project=gg-poker-prod
```

Expected APIs:
- [ ] Cloud Run API
- [ ] BigQuery API
- [ ] Cloud Storage API
- [ ] Dataflow API
- [ ] Vision AI API
- [ ] Vertex AI API
- [ ] Pub/Sub API
- [ ] Compute Engine API
- [ ] Cloud Build API
- [ ] Cloud Scheduler API
- [ ] Monitoring API
- [ ] Logging API
- [ ] Secret Manager API
- [ ] IAM Credentials API
- [ ] Cloud Resource Manager API

---

## 🔐 Day 2: Service Accounts & IAM

### Step 2.1: Create Service Accounts (5)

**Automated**:
```bash
bash scripts/setup_gcp_production.sh
```

**Manual**:
```bash
# M1 Dataflow
gcloud iam service-accounts create m1-dataflow-sa \
  --display-name="M1 Dataflow Service Account" \
  --project=gg-poker-prod

# M2 Video Metadata
gcloud iam service-accounts create m2-video-metadata-sa \
  --display-name="M2 Video Metadata Service Account" \
  --project=gg-poker-prod

# M3 Timecode Validation
gcloud iam service-accounts create m3-timecode-validation-sa \
  --display-name="M3 Timecode Validation Service Account" \
  --project=gg-poker-prod

# M4 RAG Search
gcloud iam service-accounts create m4-rag-search-sa \
  --display-name="M4 RAG Search Service Account" \
  --project=gg-poker-prod

# M5 Clipping
gcloud iam service-accounts create m5-clipping-sa \
  --display-name="M5 Clipping Service Account" \
  --project=gg-poker-prod
```

**Verification**:
```bash
gcloud iam service-accounts list --project=gg-poker-prod
```

- [ ] m1-dataflow-sa created
- [ ] m2-video-metadata-sa created
- [ ] m3-timecode-validation-sa created
- [ ] m4-rag-search-sa created
- [ ] m5-clipping-sa created

---

### Step 2.2: Assign IAM Permissions

**M1 Dataflow** (BigQuery + GCS):
```bash
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m1-dataflow-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m1-dataflow-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

- [ ] M1: bigquery.dataEditor
- [ ] M1: storage.objectAdmin

**M2 Video Metadata** (GCS + BigQuery):
```bash
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m2-video-metadata-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m2-video-metadata-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

- [ ] M2: storage.objectAdmin
- [ ] M2: bigquery.dataEditor

**M3 Timecode Validation** (Vision AI + BigQuery):
```bash
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m3-timecode-validation-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/visionai.user"

gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m3-timecode-validation-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

- [ ] M3: visionai.user
- [ ] M3: bigquery.dataEditor

**M4 RAG Search** (Vertex AI + BigQuery):
```bash
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m4-rag-search-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m4-rag-search-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

- [ ] M4: aiplatform.user
- [ ] M4: bigquery.dataEditor

**M5 Clipping** (Pub/Sub + GCS):
```bash
gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m5-clipping-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"

gcloud projects add-iam-policy-binding gg-poker-prod \
  --member="serviceAccount:m5-clipping-sa@gg-poker-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

- [ ] M5: pubsub.editor
- [ ] M5: storage.objectAdmin

---

## 📊 Day 3: BigQuery Setup

### Step 3.1: Create Dataset

```bash
bq mk -d \
  --project_id=gg-poker-prod \
  --location=us-central1 \
  --description="POKER-BRAIN Production Dataset" \
  prod
```

**Verification**:
```bash
bq ls -d gg-poker-prod
```

- [ ] Dataset `prod` created in us-central1

---

### Step 3.2: Create Tables (5)

**Table 1: hand_summary**
```bash
bq mk -t gg-poker-prod:prod.hand_summary \
  hand_id:STRING,event_id:STRING,tournament_id:STRING,table_id:STRING,\
hand_number:INTEGER,timestamp:TIMESTAMP,summary_text:STRING,\
player_names:STRING,pot_size_usd:FLOAT,created_at:TIMESTAMP
```

- [ ] hand_summary created

**Table 2: video_files**
```bash
bq mk -t gg-poker-prod:prod.video_files \
  file_id:STRING,video_path:STRING,proxy_path:STRING,duration_seconds:FLOAT,\
resolution:STRING,codec:STRING,file_size_bytes:INTEGER,created_at:TIMESTAMP
```

- [ ] video_files created

**Table 3: timecode_validation**
```bash
bq mk -t gg-poker-prod:prod.timecode_validation \
  validation_id:STRING,hand_id:STRING,video_path:STRING,sync_score:FLOAT,\
vision_confidence:FLOAT,suggested_offset:INTEGER,status:STRING,created_at:TIMESTAMP
```

- [ ] timecode_validation created

**Table 4: hand_embeddings**
```bash
bq mk -t gg-poker-prod:prod.hand_embeddings \
  hand_id:STRING,summary_text:STRING,embedding:STRING,created_at:TIMESTAMP
```

- [ ] hand_embeddings created

**Table 5: clipping_requests**
```bash
bq mk -t gg-poker-prod:prod.clipping_requests \
  request_id:STRING,hand_id:STRING,status:STRING,output_gcs_path:STRING,\
download_url:STRING,created_at:TIMESTAMP,completed_at:TIMESTAMP
```

- [ ] clipping_requests created

**Verification**:
```bash
bq ls gg-poker-prod:prod
```

Expected output: 5 tables listed

---

## 🗄️ Day 4: Cloud Storage Setup

### Step 4.1: Create Buckets (3)

**Bucket 1: Source Data**
```bash
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-poker-source
```

- [ ] gs://gg-poker-source created

**Bucket 2: Proxy Videos**
```bash
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-poker-proxies
```

- [ ] gs://gg-poker-proxies created

**Bucket 3: Clips**
```bash
gsutil mb -p gg-poker-prod -c STANDARD -l us-central1 gs://gg-subclips
```

- [ ] gs://gg-subclips created

**Verification**:
```bash
gsutil ls -p gg-poker-prod
```

Expected: 3 buckets listed

---

### Step 4.2: Configure Lifecycle Policy

**Create lifecycle.json**:
```bash
cat > lifecycle.json << 'EOF'
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
```

**Apply to clips bucket**:
```bash
gsutil lifecycle set lifecycle.json gs://gg-subclips
```

**Verification**:
```bash
gsutil lifecycle get gs://gg-subclips
```

- [ ] Lifecycle policy applied (30-day auto-delete)

---

## 💰 Day 5: Billing & Budgets

### Step 5.1: Set Monthly Budget

**Manual Steps** (GCP Console):
1. Go to: https://console.cloud.google.com/billing/budgets?project=gg-poker-prod
2. Click "Create Budget"
3. Fill in:
   - **Name**: POKER-BRAIN Monthly Budget
   - **Budget type**: Specified amount
   - **Projects**: gg-poker-prod
   - **Budget amount**: $200
4. Set alert thresholds:
   - 50% ($100)
   - 90% ($180)
   - 100% ($200)
5. Add notification email: `aiden.kim@ggproduction.net`
6. Click "Finish"

- [ ] Budget created ($200/month)
- [ ] 50% alert configured
- [ ] 90% alert configured
- [ ] 100% alert configured
- [ ] Email notification set

---

### Step 5.2: Enable Cost Breakdown

**Enable detailed billing export**:
1. Go to: https://console.cloud.google.com/billing/export?project=gg-poker-prod
2. Create BigQuery export (optional but recommended):
   - Dataset: `billing_export`
   - Location: us-central1

- [ ] Billing export configured (optional)

---

## 📤 Day 6-7: Sample Data Upload

### Step 6.1: Upload Hand Summary Data

```bash
bash scripts/upload_sample_data.sh
```

**Manual**:
```bash
bq load --source_format=NEWLINE_DELIMITED_JSON \
  gg-poker-prod:prod.hand_summary \
  mock_data/bigquery/hand_summary_real.json
```

**Verification**:
```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total_hands FROM `gg-poker-prod.prod.hand_summary`'
```

Expected: 22-23 hands

- [ ] Hand summary data uploaded
- [ ] Row count verified

---

### Step 6.2: Upload Embeddings (Optional)

```bash
bq load --source_format=NEWLINE_DELIMITED_JSON \
  gg-poker-prod:prod.hand_embeddings \
  mock_data/embeddings/hand_embeddings_real.json
```

- [ ] Embeddings uploaded (optional)

---

## ✅ Final Verification

### Run Verification Script

```bash
bash scripts/verify_gcp_setup.sh
```

This will check:
- [ ] Project exists and billing enabled
- [ ] All 15 APIs enabled
- [ ] 5 service accounts created
- [ ] 10+ IAM bindings configured
- [ ] BigQuery dataset and 5 tables exist
- [ ] 3 GCS buckets exist
- [ ] Lifecycle policy on clips bucket
- [ ] Sample data loaded (22+ hands)

---

## 📝 Post-Setup Tasks

### Update Environment Variables

Create `.env.production`:
```bash
cp .env.production.example .env.production
```

Edit with actual values:
```env
POKER_ENV=production
GCP_PROJECT=gg-poker-prod
BIGQUERY_DATASET=prod
GCS_BUCKET_SOURCE=gs://gg-poker-source
GCS_BUCKET_PROXIES=gs://gg-poker-proxies
GCS_BUCKET_CLIPS=gs://gg-subclips
```

- [ ] .env.production created
- [ ] All variables set

---

### Update Issue #16

1. Update checklist in GitHub issue
2. Add completion comment with summary
3. Close issue if all steps complete

- [ ] Issue #16 updated
- [ ] Issue #16 closed

---

## 📊 Summary

**Expected Results**:
- **Project**: gg-poker-prod
- **APIs**: 15 enabled
- **Service Accounts**: 5
- **BigQuery Tables**: 5
- **GCS Buckets**: 3
- **Sample Data**: 22 hands
- **Cost**: $0 (initial setup on free tier)

**Next Phase**: Module Deployment (Week 2-3)

---

## 🆘 Troubleshooting

### Issue: "Permission denied"

**Solution**:
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Verify permissions
gcloud projects get-iam-policy gg-poker-prod
```

### Issue: "Billing account not enabled"

**Solution**:
1. Go to: https://console.cloud.google.com/billing
2. Enable billing account
3. Link to project

### Issue: "API not enabled"

**Solution**:
```bash
# Enable specific API
gcloud services enable {api-name}.googleapis.com --project=gg-poker-prod
```

### Issue: "Bucket name already taken"

**Solution**:
```bash
# Use alternative names
gs://gg-poker-prod-source
gs://gg-poker-prod-proxies
gs://gg-poker-prod-subclips
```

---

**Last Updated**: 2025-01-17
**Maintained By**: aiden.kim@ggproduction.net
**Support**: #poker-brain-infra (Slack)
