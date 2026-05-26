# ☁️ GCP Cloud Run Deployment Guide (Tailscale Userspace Exit Node)

This guide covers deploying the PinSeeker application to **Google Cloud Run** inside your hosting project (**`jeff-gcp-project`**), securely connecting to your database/auth in your Firebase project (**`pinseeker-app`**), and routing all automation traffic through your private home Raspberry Pi SOCKS5 proxy using **Tailscale Userspace Networking**.

Because Cloud Run does not support custom security capabilities (like `NET_ADMIN` needed to create tun/tap devices), **Tailscale runs directly inside your PinSeeker container in userspace mode**, exposing a local SOCKS5 proxy on `localhost:1055`. It then tunnels all traffic going into that proxy to your home Raspberry Pi.

---

## 🛠️ GCP Infrastructure Requirements

Headless browser automation (Playwright/Chromium) is resource-intensive. If the memory or CPU allocation is too low, Chromium will crash with Out Of Memory (OOM) errors or run too slowly, causing the booking bot to miss the highly competitive tee time slots.

### Recommended Container Sizing
* **Memory**: 🔲 **2 GiB** (Minimum required for single Playwright executions). Set to **4 GiB** if scheduling multiple parallel snipes.
* **CPU**: ⚡ **2 vCPUs** (Ensures pages load quickly, JavaScript evaluates dynamically, and interactions are snappy).
* **Scaling**: 📉 **Min Instances: 0** (Scales down to absolute zero when idle, costing $0.00). **Max Instances: 5** (Limits concurrency to protect your database).

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

## 🔑 2. Configure Your Tailscale Exit Node (Raspberry Pi)

To route all Cloud Run automation requests through your home residential IP, your Raspberry Pi must act as a **Tailscale Exit Node**.

1. **Advertise the Pi as an Exit Node**:
   Log into your Raspberry Pi terminal (SSH) and run:
   ```bash
   sudo tailscale up --advertise-exit-node
   ```
2. **Approve the Exit Node in the Console**:
   - Go to your [Tailscale Admin Machines Console](https://login.tailscale.com/admin/machines).
   - Find your Raspberry Pi in the list, click the **Three Dots (...)** -> **Edit Route Settings**.
   - Check the box under **Use as exit node** and click Save.

---

## 🔑 3. Generate a Tailscale Auth Key

To let your Cloud Run container connect to your private Tailscale network automatically:
1. Open the [Tailscale Admin Keys Console](https://login.tailscale.com/admin/settings/keys).
2. Click **Generate Auth Key**.
3. Configure the key:
   - Check **Ephemeral** (automatically deletes the temporary container from your device list when it scales down to 0).
   - Check **Reusable** (so multiple containers can scale up using it).
4. Click **Generate** and copy the printed key (it starts with `tskey-auth-...`).

---

## 🚀 4. Build and Deploy

Make sure you are logged in to the Google Cloud CLI and pointing to your hosting project:
```bash
gcloud auth login
gcloud config set project jeff-gcp-project
```

### Step A: Build & Push the PinSeeker App Image
Run this command from your project root to build and upload your container (which now automatically installs Tailscale and packages `start.sh`):

```bash
gcloud builds submit --tag gcr.io/jeff-gcp-project/pinseeker:latest .
```

### Step B: Deploy to Cloud Run
Deploy using the standard `gcloud run deploy` command, injecting your credentials and Tailscale keys. Because Tailscale runs inside the container, **no special YAML or beta features are required!**

```bash
gcloud run deploy pinseeker \
  --image gcr.io/jeff-gcp-project/pinseeker:latest \
  --platform managed \
  --region us-east1 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 5 \
  --allow-unauthenticated \
  --update-secrets="/secrets/service-account.json=pinseeker-sa-key:latest" \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/secrets/service-account.json" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=pinseeker-app" \
  --set-env-vars="ENCRYPTION_KEY=YOUR_FERNET_ENCRYPTION_KEY_HERE" \
  --set-env-vars="TAILSCALE_AUTHKEY=tskey-auth-YOUR_TAILSCALE_EPHEMERAL_KEY" \
  --set-env-vars="TAILSCALE_EXIT_NODE=100.113.62.1" \
  --set-env-vars="PLAYWRIGHT_PROXY_SERVER=socks5://localhost:1055" \
  --set-env-vars="VITE_FIREBASE_API_KEY=AIzaSyDCJMf7UZUZhUbCfquUlsGL52koBAbwh68" \
  --set-env-vars="VITE_FIREBASE_AUTH_DOMAIN=pinseeker-app.firebaseapp.com" \
  --set-env-vars="VITE_FIREBASE_PROJECT_ID=pinseeker-app" \
  --set-env-vars="VITE_FIREBASE_STORAGE_BUCKET=pinseeker-app.firebasestorage.app" \
  --set-env-vars="VITE_FIREBASE_MESSAGING_SENDER_ID=1073365021484" \
  --set-env-vars="VITE_FIREBASE_APP_ID=1:1073365021484:web:c962517364394539af3289"
```

*Note: In this setup, we set `PLAYWRIGHT_PROXY_SERVER=socks5://localhost:1055`. All of Playwright's proxy requests go to Tailscale, which automatically tunnels them to your Pi and exits through your home IP. No credentials or ports need to be configured for Playwright!*

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
