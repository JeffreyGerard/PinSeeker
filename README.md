# PinSeeker

**Automated tee time booking for Capital Region golf courses.**

PinSeeker watches for the exact moment a course's booking window opens and fires a Playwright automation bot to grab your tee time before anyone else. You set your course, date, time window, and player count — PinSeeker handles the rest.

> Private tool. Access is by invite only.

---

## How It Works

1. Log in and submit a booking request with your target course, desired date/time window, and the release time when tee times become available.
2. The backend schedules a Google Cloud Task to fire ~60 seconds before release.
3. At the moment the window opens, a headless Chromium bot (via Playwright + stealth mode) navigates the course's booking site and completes the reservation.
4. Job status updates in real time: `PENDING → RUNNING → SUCCESS / FAILED`.

---

## Supported Courses

| Course | Booking Platform |
|---|---|
| Capital Hills | CPS Golf |
| Old Post Road | CPS Golf |
| Eagle Crest | Eagle Club Systems |
| Fairways of Halfmoon | ForeUp |
| Orchard Creek | ForeUp |
| Saratoga Spa | ForeUp |
| Schenectady Muni | ForeUp |
| Stadium Golf Club | ForeUp |
| Van Patten | ForeUp |
| Town of Colonie | Custom |

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Automation**: Playwright (Chromium), playwright-stealth
- **Database**: Google Cloud Firestore
- **Job Queue**: Google Cloud Tasks
- **Auth**: Firebase Authentication + Firebase Admin SDK
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Infra**: Google Cloud Run, Docker, Tailscale (exit node routing)

---

## Project Structure

```
PinSeeker/
├── backend/
│   ├── main.py               # FastAPI app + all API routes
│   ├── worker.py             # Job executor + CLI debug tool
│   ├── playwright_logic.py   # Booking automations (one function per course)
│   └── requirements-fastapi.txt
├── frontend/
│   └── src/
│       ├── App.tsx           # Full UI (auth, dashboard, booking form)
│       └── firebase.ts       # Firebase SDK init
├── Dockerfile                # Multi-stage build (Vite → FastAPI image)
├── start.sh                  # Container entrypoint (Tailscale + Uvicorn)
└── cloudbuild.yaml           # GCP Cloud Build CI/CD
```

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- A GCP service account with Firestore + Cloud Tasks access
- Firebase project credentials

### Backend

```bash
cd backend
pip install -r requirements-fastapi.txt
playwright install chromium

# Copy and fill in environment variables
cp .env.example .env

# Run the dev server
uvicorn main:app --reload --port 8080
```

Place your GCP service account key at `backend/service-account.json` for local auth. The app will auto-detect and use it.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env.local` with your Firebase config:

```
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

### Docker (full stack)

```bash
docker build \
  --build-arg VITE_FIREBASE_API_KEY=... \
  --build-arg VITE_FIREBASE_AUTH_DOMAIN=... \
  --build-arg VITE_FIREBASE_PROJECT_ID=... \
  --build-arg VITE_FIREBASE_STORAGE_BUCKET=... \
  --build-arg VITE_FIREBASE_MESSAGING_SENDER_ID=... \
  --build-arg VITE_FIREBASE_APP_ID=... \
  -t pinseeker .

docker run -p 8080:8080 pinseeker
```

---

## Debugging Bookings

Test a specific job without waiting for its release timer:

```bash
# Execute immediately (live run)
python worker.py --debug-job <JOB_ID>

# Dry run — full automation but skips the final confirm click
python worker.py --debug-job <JOB_ID> --dry-run
```

Failed automations save a screenshot to `backend/screenshots/` for inspection.

---

## Deployment

Deployments are handled via Google Cloud Build. Pushing a new build:

```bash
gcloud builds submit --config cloudbuild.yaml .
```

The Cloud Run service requires these environment variables set:
- `GOOGLE_CLOUD_PROJECT`
- `BASE_URL` — the public Cloud Run service URL
- `CLOUD_TASKS_QUEUE` / `CLOUD_TASKS_LOCATION`
- `TASK_SERVICE_ACCOUNT_EMAIL`
- `TAILSCALE_AUTHKEY` / `TAILSCALE_EXIT_NODE` (optional, for IP routing)
