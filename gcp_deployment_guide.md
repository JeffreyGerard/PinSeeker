# ☁️ GCP Cloud Run Deployment Guide

This guide covers deploying the PinSeeker application to Google Cloud Run, optimizing the container memory and CPU settings for headless Playwright execution, and configuring Cloud Run to scale to 0 to minimize costs.

---

## 🛠️ GCP Infrastructure Requirements

Headless browser automation (Playwright/Chromium) requires substantial resources compared to basic API routers. If the memory or CPU allocation is too low, Chromium will crash with Out Of Memory (OOM) errors or run too slowly, causing the booking bot to miss the highly competitive tee time slots.

### Recommended Container Sizing
* **Memory**: 🔲 **2 GiB** (Minimum required for single Playwright executions). Set to **4 GiB** if scheduling multiple parallel snipes.
* **CPU**: ⚡ **2 vCPUs** (Ensures pages load quickly, JavaScript evaluates dynamically, and interactions are snappy).
* **Scaling**: 📉 **Min Instances: 0** (Scales down to absolute zero when idle, costing $0.00). **Max Instances: 5** (Limits concurrency to protect your proxy and database).

---

## 🚀 Step-by-Step Deployment

Make sure you have installed the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and logged in:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 1. Build & Push Your Container

Use Google Cloud Build to compile and build your unified React + FastAPI container. Run this command from the root directory of your project:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pinseeker:latest .
```

### 2. Deploy to Cloud Run

Deploy the container using the command below, which configures the recommended sizing, sets minimum instances to 0, and enables scale-to-zero:

```bash
gcloud run deploy pinseeker \
  --image gcr.io/YOUR_PROJECT_ID/pinseeker:latest \
  --platform managed \
  --region us-east1 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 5 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID" \
  --set-env-vars="ENCRYPTION_KEY=YOUR_FERNET_ENCRYPTION_KEY" \
  --set-env-vars="PLAYWRIGHT_PROXY_SERVER=http://yourpi-ip-or-dns:port" \
  --set-env-vars="PLAYWRIGHT_PROXY_USERNAME=proxyuser" \
  --set-env-vars="PLAYWRIGHT_PROXY_PASSWORD=proxypassword" \
  --set-env-vars="VITE_FIREBASE_API_KEY=YOUR_API_KEY" \
  --set-env-vars="VITE_FIREBASE_AUTH_DOMAIN=YOUR_PROJECT.firebaseapp.com" \
  --set-env-vars="VITE_FIREBASE_PROJECT_ID=YOUR_PROJECT" \
  --set-env-vars="VITE_FIREBASE_STORAGE_BUCKET=YOUR_PROJECT.appspot.com" \
  --set-env-vars="VITE_FIREBASE_MESSAGING_SENDER_ID=SENDER_ID" \
  --set-env-vars="VITE_FIREBASE_APP_ID=APP_ID"
```

> [!NOTE]
> Make sure to replace `YOUR_PROJECT_ID` with your actual Google Cloud Project ID, and supply your custom encryption key and proxy credentials.

---

## ⏰ Automated Cron Triggering (Cloud Scheduler)

Since the Cloud Run service scales down to 0 to save money, it cannot run background threads that sleep and wake up to run booking snipes. Instead, we use **Cloud Scheduler** to wake up the service exactly when needed.

We will configure a Cloud Scheduler job to hit `/api/cron` every minute. When hit, the FastAPI endpoint queries Firestore. If a tee time booking has an upcoming release window (releasing in the next 60 seconds), the service stays active to launch a background thread and complete the snipe before scaling back to 0.

### Create the Scheduler Job

1. **Get your Cloud Run Service URL**:
   ```bash
   gcloud run services describe pinseeker --region us-east1 --format="value(status.url)"
   ```
   Assume this returns `https://pinseeker-abcdef-ue.a.run.app`.

2. **Create the Cloud Scheduler Cron**:
   ```bash
   gcloud scheduler jobs create http pinseeker-minute-cron \
     --schedule="* * * * *" \
     --uri="https://pinseeker-abcdef-ue.a.run.app/api/cron" \
     --http-method=GET \
     --time-zone="America/New_York" \
     --description="Trigger PinSeeker release scan every minute"
   ```

This configuration ensures PinSeeker operates fully serverless. You pay nothing during the day when no bookings are active, but the service wakes up exactly on target to book your tee times, routing through your home Raspberry Pi seamlessly!
