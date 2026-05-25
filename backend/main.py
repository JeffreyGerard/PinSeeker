from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google.cloud import firestore
import datetime
import os
import uuid
import firebase_admin
from firebase_admin import credentials, auth
import threading
import subprocess
import sys

# Initialize FastAPI
app = FastAPI(title="PinSeeker API")

# Load local service account key if it exists for local testing, otherwise use default credentials
sa_path = os.path.join(os.getcwd(), "service-account.json")
if os.path.exists(sa_path):
    print(f"Using local service account credentials from {sa_path}")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path
    try:
        import json
        with open(sa_path, "r") as f:
            sa_data = json.load(f)
            project_id = sa_data.get("project_id")
            if project_id:
                print(f"Auto-configured GOOGLE_CLOUD_PROJECT to: {project_id}")
                os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    except Exception as e:
        print(f"Warning: Failed to parse service-account.json project ID: {e}")
else:
    print("service-account.json not found. Relying on default GCP credentials.")

# Initialize Firebase Admin for authenticating user tokens
try:
    firebase_admin.get_app()
except ValueError:
    # Uses default credentials automatically on Cloud Run or via environment variables locally
    firebase_admin.initialize_app()

# Initialize Firestore
try:
    db = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT', 'jeff-gcp-project'))
except Exception as e:
    print(f"Warning: Failed to initialize Firestore. {e}")
    db = None

# Pydantic Model for incoming booking requests
class BookingRequest(BaseModel):
    course: int
    course_name: str
    desired_date: str
    earliest_time: str
    latest_time: str
    players: int
    release_time: str = Field(..., description="ISO 8601 string, e.g., '2026-05-10T07:00:00+00:00'")
    passcode: str = Field(default="", description="Simple authentication passcode")
    course_email: str = Field(default="", description="Optional course login email")
    course_password: str = Field(default="", description="Optional course login password")

def verify_firebase_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = auth_header.split("Bearer ")[-1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {e}")

@app.get("/api/bookings")
async def list_bookings(request: Request):
    verify_firebase_token(request)
    
    if not db:
        return []
    
    try:
        # Get last 20 jobs, ordered by creation time
        jobs_ref = db.collection('tee_time_jobs').order_by('created_at', direction=firestore.Query.DESCENDING).limit(20)
        docs = jobs_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Fetch error: {e}")
        return []

@app.post("/api/bookings", status_code=201)
async def create_booking(booking_request: BookingRequest, request: Request):
    user = verify_firebase_token(request)

    if not db:
        raise HTTPException(status_code=500, detail="Database connection not available")

    # Generate a unique ID for the job
    job_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    job_data = {
        "id": job_id,
        "status": "PENDING",
        "course": booking_request.course,
        "course_name": booking_request.course_name,
        "desired_date": booking_request.desired_date,
        "earliest_time": booking_request.earliest_time,
        "latest_time": booking_request.latest_time,
        "players": booking_request.players,
        "release_time": booking_request.release_time,
        "course_email": booking_request.course_email,
        "course_password": booking_request.course_password,
        "created_at": now,
        "updated_at": now,
        "uid": user["uid"]
    }

    try:
        # Write to Firestore collection 'tee_time_jobs'
        doc_ref = db.collection('tee_time_jobs').document(job_id)
        doc_ref.set(job_data)
        return {"status": "success", "job_id": job_id, "message": "Booking request queued."}
    except Exception as e:
        print(f"Firestore error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save booking request")

def run_worker_in_background(job_id):
    """Run the worker.py script inside a background thread to prevent blocking FastAPI request."""
    try:
        import sys
        subprocess.run([sys.executable, "worker.py", "--debug-job", job_id], check=True)
    except Exception as e:
        print(f"Background worker execution error: {e}")

@app.get("/api/cron")
async def trigger_cron():
    """Scan Firestore for PENDING bookings that need to release soon (in the next 75 seconds)

    and trigger them in the background.
    """
    if not db:
        return {"status": "error", "message": "Database not initialized"}
        
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    triggered_jobs = []
    
    try:
        # Check PENDING jobs
        jobs_ref = db.collection('tee_time_jobs').where('status', '==', 'PENDING')
        docs = jobs_ref.stream()
        
        for doc in docs:
            job_data = doc.to_dict()
            release_time_str = job_data.get('release_time')
            if not release_time_str:
                continue
                
            release_time = datetime.datetime.fromisoformat(release_time_str)
            time_until_release = (release_time - now_utc).total_seconds()
            
            # If the job releases in the next 75 seconds and has not started, trigger it
            if 0 < time_until_release <= 75:
                job_id = doc.id
                print(f"Cron detected imminent job {job_id} releasing in {time_until_release:.2f} seconds. Triggering...")
                
                # Run worker.py in a background thread to let FastAPI respond immediately
                t = threading.Thread(target=run_worker_in_background, args=(job_id,))
                t.start()
                triggered_jobs.append(job_id)
                
            # Clean up stale jobs that were missed (more than 2 minutes in the past)
            elif time_until_release <= -120:
                print(f"Cron marking stale job {doc.id} as FAILED (Missed release window).")
                db.collection('tee_time_jobs').document(doc.id).update({
                    "status": "FAILED",
                    "result_log": "Missed release window (bot was not running or scheduler failed)",
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
                
        return {"status": "success", "triggered_jobs": triggered_jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Exception handler for serving the React SPA (catch-all for frontend routing)
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    # If the user is requesting an API route that doesn't exist, return 404 JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"message": "Not Found"})
    
    # Otherwise, assume it's a frontend route and let React handle it
    # We serve the index.html from the dist folder
    try:
        with open("dist/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content, status_code=200)
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"message": "Frontend build not found. Run 'npm run build' in the frontend directory."})

# Mount the static 'dist' directory (contains assets like CSS/JS from Vite build)
# This must come AFTER the API routes so it doesn't intercept them.
if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
else:
    print("Warning: 'dist' directory not found. Ensure React frontend is built.")

