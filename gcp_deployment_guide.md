# ☁️ GCP Cloud Run Deployment Guide (Tailscale Secure Tunnel)

This guide covers deploying the PinSeeker application to **Google Cloud Run** inside your hosting project (**`jeff-gcp-project`**), while securely connecting to your database/auth in your Firebase project (**`pinseeker-app`**) and bridging the connection to your private home Raspberry Pi SOCKS5 proxy using **Tailscale**.

Because you are using Tailscale to secure your Raspberry Pi, Cloud Run requires a **Tailscale sidecar container** to join your private tailnet and communicate with your SOCKS5 proxy at `100.113.62.1:1080` securely.

---

## 🛠️ GCP Infrastructure Requirements

Headless browser automation (Playwright/Chromium) is resource-intensive. If the memory or CPU allocation is too low, Chromium will crash with Out Of Memory (OOM) errors or run too slowly, causing the booking bot to miss the highly competitive tee time slots.

### Recommended Container Sizing
* **Memory**: 🔲 **2 GiB** (Minimum required for single Playwright executions). Set to **4 GiB** if scheduling multiple parallel snipes.
* **CPU**: ⚡ **2 vCPUs** (Ensures pages load quickly, JavaScript evaluates dynamically, and interactions are snappy).
* **Scaling**: 📉 **Min Instances: 0** (Scales down to absolute zero when idle, costing $0.00). **Max Instances: 5** (Limits concurrency to protect your proxy and database).

---

## 🔐 1. Upload Firebase Key to Secret Manager

Since your code runs on Cloud Run in `jeff-gcp-project` but needs access to `pinseeker-app` Firestore and Firebase Auth, we securely pass the `pinseeker-app` service account key file using **GCP Secret Manager**.

Download your service account key JSON from the `pinseeker-app` Firebase Console and upload it as a Secret inside your hosting project (`jeff-gcp-project`):

```bash
# 1. Ensure you are pointing to your hosting project
gcloud config set project jeff-gcp-project

# 2. Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# 3. Create the secret and upload the JSON key file
gcloud secrets create pinseeker-sa-key --data-file="/Users/jeffgerard/Projects/PinSeeker/backend/service-account.json"
```

---

## 🔑 2. Generate a Tailscale Auth Key

To let the Cloud Run sidecar container connect to your private Tailscale network automatically:
1. Open the [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys).
2. Go to **Settings -> Keys**.
3. Click **Generate Auth Key**.
4. Configure the key:
   - Check **Ephemeral** (this automatically deletes the device from your admin list when the container shuts down).
   - Check **Reusable** (so multiple container instances can use it).
5. Click **Generate** and copy the printed key (it starts with `tskey-auth-...`).

---

## 📄 3. Configure the `service.yaml` file

In the root of your repository, we have created a **`service.yaml`** configuration template. Open this file and replace the placeholders:

1. **`YOUR_FERNET_ENCRYPTION_KEY_HERE`**: Replace with your Fernet encryption key.
2. **`tskey-auth-YOUR_TAILSCALE_EPHEMERAL_KEY`**: Replace with your actual Tailscale Auth Key generated in Section 2.

---

## 🚀 4. Build and Deploy

Make sure you are logged in to the Google Cloud CLI and pointing to your hosting project:
```bash
gcloud auth login
gcloud config set project jeff-gcp-project
```

### Step A: Build & Push the PinSeeker App Image
Run this command from your project root to build and upload your container to the Google Container Registry:

```bash
gcloud builds submit --tag gcr.io/jeff-gcp-project/pinseeker:latest .
```

### Step B: Deploy the Multi-Container Service
Deploy both the PinSeeker app container and the Tailscale sidecar container using the `service.yaml` configuration file:

```bash
gcloud beta run services replace service.yaml
```

---

## ⏰ 5. Automated Cron Triggering (Cloud Scheduler)

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
