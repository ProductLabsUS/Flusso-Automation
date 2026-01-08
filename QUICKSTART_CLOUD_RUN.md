# Quick Start: Deploy to Google Cloud Run

This is a quick reference for deploying Flusso Workflow to Google Cloud Run. For complete details, see [GOOGLE_CLOUD_DEPLOYMENT.md](GOOGLE_CLOUD_DEPLOYMENT.md).

## Prerequisites

- Google Cloud account
- `gcloud` CLI installed
- Docker (optional, Cloud Build can build for you)

## 1️⃣ Setup (One-time)

```bash
# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

## 2️⃣ Store Secrets

```bash
# Create secrets (replace with your actual values)
echo -n "YOUR_FRESHDESK_API_KEY" | gcloud secrets create freshdesk-api-key --data-file=-
echo -n "https://your-domain.freshdesk.com" | gcloud secrets create freshdesk-domain --data-file=-
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_GEMINI_STORE_ID" | gcloud secrets create gemini-file-search-store-id --data-file=-
echo -n "YOUR_PINECONE_API_KEY" | gcloud secrets create pinecone-api-key --data-file=-
echo -n "YOUR_PINECONE_IMAGE_INDEX" | gcloud secrets create pinecone-image-index --data-file=-
echo -n "YOUR_PINECONE_TICKETS_INDEX" | gcloud secrets create pinecone-tickets-index --data-file=-
```

## 3️⃣ Build & Deploy

```bash
# Build image using Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/flusso-webhook:latest -f Dockerfile.cloudrun

# Deploy to Cloud Run
gcloud run deploy flusso-webhook \
  --image gcr.io/YOUR_PROJECT_ID/flusso-webhook:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --set-secrets="FRESHDESK_API_KEY=freshdesk-api-key:latest,FRESHDESK_DOMAIN=freshdesk-domain:latest,GEMINI_API_KEY=gemini-api-key:latest,GEMINI_FILE_SEARCH_STORE_ID=gemini-file-search-store-id:latest,PINECONE_API_KEY=pinecone-api-key:latest,PINECONE_IMAGE_INDEX=pinecone-image-index:latest,PINECONE_TICKETS_INDEX=pinecone-tickets-index:latest" \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,PINECONE_ENV=us-east-1"
```

## 4️⃣ Get Webhook URL

```bash
gcloud run services describe flusso-webhook --region us-central1 --format='value(status.url)'
```

## 5️⃣ Configure Freshdesk

1. Go to Freshdesk Admin → **Automations** → **Webhooks**
2. Create new webhook:
   - **URL**: `https://your-service-url.a.run.app/webhook`
   - **Method**: POST
   - **Encoding**: JSON
   - **Events**: Select ticket created/updated

## 6️⃣ Test

```bash
# Health check
curl https://your-service-url.a.run.app/health

# View logs
gcloud run services logs tail flusso-webhook --region us-central1
```

## 🔄 Update Deployment

```bash
# Rebuild and redeploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/flusso-webhook:latest -f Dockerfile.cloudrun
gcloud run deploy flusso-webhook --image gcr.io/YOUR_PROJECT_ID/flusso-webhook:latest --region us-central1
```

## 📊 Monitor

- **Logs**: Cloud Console → Cloud Run → flusso-webhook → Logs
- **Metrics**: Cloud Console → Cloud Run → flusso-webhook → Metrics
- **Alerts**: Cloud Console → Monitoring → Alerting

## 💰 Estimated Cost

- **Free tier**: 2M requests/month
- **Light usage**: ~$5-10/month
- **Medium usage**: ~$30-50/month

---

For advanced configurations, troubleshooting, and alternative deployment options (GKE, Compute Engine), see [GOOGLE_CLOUD_DEPLOYMENT.md](GOOGLE_CLOUD_DEPLOYMENT.md).
