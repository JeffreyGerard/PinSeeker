# Tech Stack

## Backend
- **Runtime**: Python 3.11
- **Web Framework**: FastAPI + Uvicorn
- **Browser Automation**: Playwright (Chromium) + playwright-stealth (anti-detection)
- **Database**: Google Cloud Firestore
- **Job Scheduling**: Google Cloud Tasks
- **Auth**: Firebase Admin SDK (token verification server-side)
- **Infra**: Google Cloud Run (containerized), Tailscale (exit node routing for bot traffic)

## Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Icons**: lucide-react
- **Auth/DB**: Firebase JS SDK (Auth + Firestore direct reads)

## Deployment
- Single Docker image (multi-stage): Vite builds the React app, output is copied into the FastAPI image as `dist/`
- FastAPI serves the React SPA from `dist/` and handles API routes under `/api/`
- CI/CD: Google Cloud Build (`cloudbuild.yaml`) builds and pushes to Container Registry
- Startup: `start.sh` — launches `tailscaled`, connects to Tailscale exit node, then starts Uvicorn

## Environment Variables
Key env vars consumed by the backend:
- `GOOGLE_CLOUD_PROJECT` — GCP project ID
- `BASE_URL` — Public Cloud Run URL (used for Cloud Tasks callbacks)
- `CLOUD_TASKS_QUEUE`, `CLOUD_TASKS_LOCATION` — Task queue config
- `TASK_SERVICE_ACCOUNT_EMAIL` — SA used for OIDC-authenticated task delivery
- `TAILSCALE_AUTHKEY`, `TAILSCALE_EXIT_NODE` — Tailscale routing config

Frontend Firebase config is injected at build time via `VITE_FIREBASE_*` build args.

## Common Commands

### Backend (run from `backend/`)
```bash
# Install dependencies
pip install -r requirements-fastapi.txt

# Install Playwright browsers
playwright install chromium

# Run dev server
uvicorn main:app --reload --port 8080

# Run the worker directly (check for imminent jobs)
python worker.py

# Debug a specific job (bypasses the wait timer)
python worker.py --debug-job <JOB_ID>

# Dry-run a specific job (full automation, skips final click)
python worker.py --debug-job <JOB_ID> --dry-run
```

### Frontend (run from `frontend/`)
```bash
npm install
npm run dev        # Dev server (Vite)
npm run build      # Production build → outputs to frontend/dist/
npm run preview    # Preview production build locally
```

### Docker (run from repo root)
```bash
docker build -t pinseeker .
docker run -p 8080:8080 pinseeker
```
