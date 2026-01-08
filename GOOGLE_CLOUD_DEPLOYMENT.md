# 🚀 Google Cloud Deployment Guide - Flusso Workflow

Complete guide to deploy your Flusso Workflow webhook automation to Google Cloud Platform.

## 📋 Table of Contents

1. [Deployment Options](#deployment-options)
2. [Recommended: Cloud Run (Serverless)](#option-1-cloud-run-recommended)
3. [Alternative: GKE (Kubernetes)](#option-2-gke-kubernetes)
4. [Alternative: Compute Engine (VM)](#option-3-compute-engine-vm)
5. [Secret Management](#secret-management)
6. [CI/CD Setup](#cicd-with-cloud-build)
7. [Monitoring & Logging](#monitoring--logging)
8. [Cost Optimization](#cost-optimization)

---

## 🎯 Deployment Options

### Option 1: **Cloud Run** (RECOMMENDED) ⭐
- **Best for:** Serverless, auto-scaling webhook endpoints
- **Pros:** Easy deployment, pay-per-use, auto-scaling, HTTPS included
- **Cons:** Cold starts (mitigated with min instances)
- **Cost:** ~$5-50/month depending on usage

### Option 2: **GKE (Google Kubernetes Engine)**
- **Best for:** Complex microservices, heavy traffic
- **Pros:** Full control, horizontal scaling, advanced networking
- **Cons:** Complex setup, higher cost, requires K8s knowledge
- **Cost:** ~$75-300/month minimum

### Option 3: **Compute Engine (VM)**
- **Best for:** Simple deployment, full control
- **Pros:** Traditional server setup, predictable costs
- **Cons:** Manual scaling, no auto-scaling, maintenance overhead
- **Cost:** ~$30-100/month

---

## 🌟 Option 1: Cloud Run (RECOMMENDED)

Cloud Run is ideal for webhook-based applications with variable traffic patterns.

### Prerequisites

1. **Install Google Cloud SDK**
   ```bash
   # Download from: https://cloud.google.com/sdk/docs/install
   # After installation:
   gcloud init
   gcloud auth login
   ```

2. **Set your project**
   ```bash
   # Create new project (if needed)
   gcloud projects create flusso-workflow --name="Flusso Workflow"
   
   # Set active project
   gcloud config set project flusso-workflow
   
   # Enable required APIs
   gcloud services enable \
     run.googleapis.com \
     containerregistry.googleapis.com \
     cloudbuild.googleapis.com \
     secretmanager.googleapis.com \
     aiplatform.googleapis.com
   ```

### Step 1: Fix Dockerfile for Cloud Run

Your current Dockerfile references `app.main` but should reference `app.main_react` for the ReACT agent.

Create a new file `Dockerfile.cloudrun`:

```dockerfile
# Cloud Run optimized Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY data/ ./data/

# Create cache directory
RUN mkdir -p .cache/webhook_dedup

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Cloud Run uses PORT env variable (default 8080)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5.0)" || exit 1

# Run with ReACT agent (app.main_react)
CMD exec uvicorn app.main_react:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
```

### Step 2: Store Secrets in Secret Manager

```bash
# Create secrets (replace with your actual values)
echo -n "your_freshdesk_api_key" | gcloud secrets create freshdesk-api-key --data-file=-
echo -n "https://your-domain.freshdesk.com" | gcloud secrets create freshdesk-domain --data-file=-
echo -n "your_gemini_api_key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your_gemini_store_id" | gcloud secrets create gemini-file-search-store-id --data-file=-
echo -n "your_pinecone_api_key" | gcloud secrets create pinecone-api-key --data-file=-
echo -n "your_pinecone_image_index" | gcloud secrets create pinecone-image-index --data-file=-
echo -n "your_pinecone_tickets_index" | gcloud secrets create pinecone-tickets-index --data-file=-

# Verify secrets created
gcloud secrets list
```

### Step 3: Build and Push Docker Image

```bash
# Set environment variables
export PROJECT_ID=flusso-workflow
export REGION=us-central1
export SERVICE_NAME=flusso-webhook

# Build using Cloud Build (recommended - faster)
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest -f Dockerfile.cloudrun

# OR build locally and push
# docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest -f Dockerfile.cloudrun .
# docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest
```

### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 10 \
  --set-secrets="FRESHDESK_API_KEY=freshdesk-api-key:latest,FRESHDESK_DOMAIN=freshdesk-domain:latest,GEMINI_API_KEY=gemini-api-key:latest,GEMINI_FILE_SEARCH_STORE_ID=gemini-file-search-store-id:latest,PINECONE_API_KEY=pinecone-api-key:latest,PINECONE_IMAGE_INDEX=pinecone-image-index:latest,PINECONE_TICKETS_INDEX=pinecone-tickets-index:latest" \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,PINECONE_ENV=us-east-1"
```

### Step 5: Get Your Webhook URL

```bash
# Get the service URL
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)'

# Example output: https://flusso-webhook-abc123-uc.a.run.app
```

### Step 6: Configure Freshdesk Webhook

1. Go to Freshdesk Admin → **Automations** → **Webhooks**
2. Click **New Webhook**
3. Configure:
   - **URL**: `https://flusso-webhook-abc123-uc.a.run.app/webhook`
   - **Method**: POST
   - **Encoding**: JSON
   - **Events**: Select ticket events (created, updated, etc.)
4. Test the webhook with a sample ticket

### Step 7: Monitor Your Deployment

```bash
# View logs
gcloud run services logs tail ${SERVICE_NAME} --region ${REGION}

# Check service status
gcloud run services describe ${SERVICE_NAME} --region ${REGION}

# Test health endpoint
curl https://your-service-url.a.run.app/health
```

---

## 🏗️ Option 2: GKE (Kubernetes)

For high-traffic, production-grade deployments with advanced orchestration.

### Prerequisites

```bash
# Enable GKE API
gcloud services enable container.googleapis.com

# Create GKE cluster (autopilot mode - easier)
gcloud container clusters create-auto flusso-cluster \
  --region us-central1
```

### Kubernetes Deployment Files

Create `k8s/` directory with these files:

**`k8s/deployment.yaml`**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flusso-workflow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flusso-workflow
  template:
    metadata:
      labels:
        app: flusso-workflow
    spec:
      containers:
      - name: flusso-webhook
        image: gcr.io/flusso-workflow/flusso-webhook:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: PORT
          value: "8080"
        envFrom:
        - secretRef:
            name: flusso-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 5
```

**`k8s/service.yaml`**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: flusso-workflow-service
spec:
  type: LoadBalancer
  selector:
    app: flusso-workflow
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
```

**`k8s/secrets.yaml`** (create from Secret Manager):
```bash
kubectl create secret generic flusso-secrets \
  --from-literal=FRESHDESK_API_KEY="your_key" \
  --from-literal=FRESHDESK_DOMAIN="https://your-domain.freshdesk.com" \
  --from-literal=GEMINI_API_KEY="your_key" \
  --from-literal=GEMINI_FILE_SEARCH_STORE_ID="your_id" \
  --from-literal=PINECONE_API_KEY="your_key" \
  --from-literal=PINECONE_IMAGE_INDEX="your_index" \
  --from-literal=PINECONE_TICKETS_INDEX="your_index"
```

### Deploy to GKE

```bash
# Get cluster credentials
gcloud container clusters get-credentials flusso-cluster --region us-central1

# Apply configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods
kubectl get services

# Get external IP
kubectl get service flusso-workflow-service
```

---

## 💻 Option 3: Compute Engine (VM)

Traditional VM deployment for full control.

### Step 1: Create VM Instance

```bash
gcloud compute instances create flusso-vm \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=http-server,https-server
```

### Step 2: Configure Firewall

```bash
gcloud compute firewall-rules create allow-flusso-webhook \
  --allow tcp:8000 \
  --target-tags http-server
```

### Step 3: SSH and Setup

```bash
# SSH into VM
gcloud compute ssh flusso-vm --zone=us-central1-a

# On the VM:
# Install dependencies
sudo apt update
sudo apt install -y python3.12 python3-pip git

# Clone your repository
git clone <your-repo-url>
cd "Flusso workflow"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
FRESHDESK_DOMAIN=https://your-domain.freshdesk.com
FRESHDESK_API_KEY=your_key
GEMINI_API_KEY=your_key
GEMINI_FILE_SEARCH_STORE_ID=your_id
PINECONE_API_KEY=your_key
PINECONE_IMAGE_INDEX=your_index
PINECONE_TICKETS_INDEX=your_index
EOF

# Run as systemd service (recommended)
sudo nano /etc/systemd/system/flusso.service
```

**`/etc/systemd/system/flusso.service`**:
```ini
[Unit]
Description=Flusso Workflow Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/Flusso workflow
Environment="PATH=/home/your_username/Flusso workflow/.venv/bin"
ExecStart=/home/your_username/Flusso workflow/.venv/bin/uvicorn app.main_react:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl enable flusso
sudo systemctl start flusso
sudo systemctl status flusso

# View logs
sudo journalctl -u flusso -f
```

---

## 🔐 Secret Management

### Using Google Secret Manager (Recommended)

All deployment options should use Secret Manager for sensitive data.

```bash
# Grant service account access to secrets
gcloud projects add-iam-policy-binding flusso-workflow \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# For Cloud Run (automatic with --set-secrets flag)
# For GKE, use Workload Identity
# For Compute Engine, use metadata server
```

---

## 🔄 CI/CD with Cloud Build

Automate deployments with Cloud Build.

**`cloudbuild.yaml`**:
```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'gcr.io/$PROJECT_ID/flusso-webhook:$COMMIT_SHA',
      '-t', 'gcr.io/$PROJECT_ID/flusso-webhook:latest',
      '-f', 'Dockerfile.cloudrun',
      '.'
    ]

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/flusso-webhook:$COMMIT_SHA']
    
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/flusso-webhook:latest']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args: [
      'run', 'deploy', 'flusso-webhook',
      '--image', 'gcr.io/$PROJECT_ID/flusso-webhook:$COMMIT_SHA',
      '--region', 'us-central1',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--min-instances', '1',
      '--max-instances', '10',
      '--memory', '2Gi',
      '--cpu', '2',
      '--timeout', '600'
    ]

timeout: 1200s
```

**Setup triggers**:
```bash
# Connect GitHub repository
gcloud builds triggers create github \
  --repo-name=your-repo-name \
  --repo-owner=your-github-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

---

## 📊 Monitoring & Logging

### Cloud Logging

```bash
# View logs in real-time
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=flusso-webhook"

# Query specific errors
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.levelname=ERROR" --limit 50
```

### Cloud Monitoring

1. Go to **Cloud Console** → **Monitoring**
2. Create alerting policies:
   - High error rate (> 5% of requests)
   - High latency (> 30s response time)
   - Instance restarts
3. Set up notification channels (email, Slack, PagerDuty)

### Custom Metrics Dashboard

```bash
# Export logs to BigQuery for analysis
gcloud logging sinks create flusso-logs-bigquery \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/flusso_logs \
  --log-filter='resource.type="cloud_run_revision"'
```

---

## 💰 Cost Optimization

### Cloud Run Cost Optimization

1. **Reduce min instances** during low-traffic periods:
   ```bash
   gcloud run services update flusso-webhook --min-instances=0
   ```

2. **Use CPU throttling** (only allocate CPU during requests):
   ```bash
   gcloud run services update flusso-webhook --cpu-throttling
   ```

3. **Right-size resources**:
   - Start with 1GB memory, 1 CPU
   - Monitor actual usage
   - Scale up if needed

### Estimated Monthly Costs (Cloud Run)

- **Free tier**: 2M requests/month, 360,000 GB-seconds
- **Light usage** (10k webhooks/month): ~$5-10
- **Medium usage** (100k webhooks/month): ~$30-50
- **Heavy usage** (1M webhooks/month): ~$200-300

---

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://your-service-url.a.run.app/health
```

### 2. Debug Endpoint
```bash
curl -X POST https://your-service-url.a.run.app/debug/process/123 \
  -H "Content-Type: application/json"
```

### 3. Webhook Test
```bash
curl -X POST https://your-service-url.a.run.app/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "123",
    "freshdesk_webhook": {
      "ticket_id": "123",
      "ticket_updated_at": "2026-01-08T12:00:00Z"
    }
  }'
```

---

## 📝 Post-Deployment Checklist

- [ ] Service is deployed and accessible
- [ ] Health endpoint returns 200 OK
- [ ] Secrets are properly configured
- [ ] Freshdesk webhook is configured with correct URL
- [ ] Test ticket processing works end-to-end
- [ ] Logging is working (check Cloud Logging)
- [ ] Monitoring alerts are configured
- [ ] CI/CD pipeline is set up (optional)
- [ ] Documentation updated with production URL
- [ ] Cost alerts configured (billing budgets)
- [ ] Backup/disaster recovery plan in place

---

## 🆘 Troubleshooting

### Common Issues

**1. Container fails to start**
```bash
# Check logs
gcloud run services logs tail flusso-webhook --region us-central1

# Common causes:
# - Missing environment variables
# - Port mismatch (use PORT env variable)
# - Memory limits too low
```

**2. Webhook not receiving events**
```bash
# Verify service is accessible
curl https://your-service-url.a.run.app/health

# Check Freshdesk webhook configuration
# Ensure URL is correct: https://your-url/webhook
# Check Freshdesk webhook logs for errors
```

**3. Timeout errors**
```bash
# Increase timeout
gcloud run services update flusso-webhook --timeout=900

# Or optimize workflow to run faster
```

**4. Cold start issues**
```bash
# Keep minimum 1 instance warm
gcloud run services update flusso-webhook --min-instances=1
```

---

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs)
- [Cloud Build CI/CD](https://cloud.google.com/build/docs)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Freshdesk Webhook Documentation](https://developers.freshdesk.com/api/#webhooks)

---

**Need Help?** Check the [troubleshooting section](#troubleshooting) or review logs in Cloud Logging.
