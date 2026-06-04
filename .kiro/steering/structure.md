# Project Structure

```
PinSeeker/
├── backend/                    # Python FastAPI application
│   ├── main.py                 # FastAPI app, all API routes (/api/*), SPA fallback handler
│   ├── worker.py               # Job executor — polls Firestore, runs bookings, CLI debug tool
│   ├── playwright_logic.py     # All Playwright booking automations (one function per course/platform)
│   ├── scraper_job.py          # Legacy job runner (env-var based, webhook reporting)
│   ├── utils.py                # Shared utilities
│   ├── requirements-fastapi.txt # Production dependencies (use this one)
│   ├── requirements.txt        # Minimal deps for standalone scraper use
│   ├── service-account.json    # GCP service account (local dev only, gitignored in prod)
│   ├── .env                    # Local environment variables (not committed)
│   └── screenshots/            # Debug screenshots captured during automation failures
│
├── frontend/                   # React + TypeScript SPA
│   ├── src/
│   │   ├── App.tsx             # Entire frontend UI — auth screens, dashboard, booking form
│   │   ├── firebase.ts         # Firebase SDK initialization (auth + firestore exports)
│   │   └── vite-env.d.ts       # Vite env type declarations
│   ├── index.html              # SPA entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── Dockerfile                  # Multi-stage: Node (Vite build) → Python (FastAPI + Playwright)
├── start.sh                    # Container entrypoint: tailscaled → tailscale up → uvicorn
├── cloudbuild.yaml             # GCP Cloud Build CI/CD pipeline
└── .kiro/steering/             # AI steering rules for this project
```

## Key Architectural Patterns

### Backend
- **Single-file API**: All routes live in `main.py`. Keep new endpoints there unless the file becomes unmanageable.
- **Course router pattern**: `worker.py` maintains `COURSE_CONFIG` — a dict mapping lowercase course name substrings to `{url, func}`. Adding a new course means adding an entry here and a corresponding function in `playwright_logic.py`.
- **Booking function signature**: All booking functions in `playwright_logic.py` follow the same signature: `book_*(url, booking, email, password, dry_run=False, headless=True)`. The `booking` object exposes `.desired_date` (date), `.earliest_time` (time), `.latest_time` (time), `.players` (int), `.course_name` (str).
- **Job status lifecycle**: `PENDING → RUNNING → SUCCESS | FAILED | CANCELLED`. Status is written to Firestore collection `tee_time_jobs`. Never skip the RUNNING update — it signals the job is active.
- **Auth**: All user-facing API routes call `verify_firebase_token(request)` first. The `/api/execute-job` route is internal (called by Cloud Tasks) and does not require user auth.
- **Firestore queries**: Avoid compound queries requiring composite indexes. Filter in memory when a simple `.where()` suffices (see `/api/bookings` sort/limit pattern).

### Frontend
- **Single-file UI**: All components and pages are in `App.tsx`. Keep new UI additions there.
- **API calls**: Use `API_URL = '/api'` constant — never hardcode the host. Auth header pattern: `Authorization: Bearer <firebase_id_token>`.
- **Firebase env vars**: Must be prefixed `VITE_FIREBASE_*` to be accessible in Vite builds. Injected as Docker build args in `cloudbuild.yaml`.
- **Course list**: `AVAILABLE_COURSES` in `App.tsx` is hardcoded. When adding a course to the backend, add it here too with the correct `advance_booking_days`.

### Playwright Automation
- Always create browser contexts via `_new_stealth_context(p)` — this applies playwright-stealth and standard anti-detection headers.
- Use `dry_run=True` during all development/testing. The guard is typically a single `if not dry_run: page.click(confirm_button)` before the final submit.
- Screenshots on failure are saved to `backend/screenshots/` for debugging.
- The `wait_for_release(release_time_str)` helper busy-waits until the booking window opens — use it before the main automation sequence in time-sensitive flows.
