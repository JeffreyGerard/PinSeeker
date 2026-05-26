from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google.cloud import firestore, tasks_v2
from google.protobuf import timestamp_pb2
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

# Helper to create Cloud Task
def schedule_booking_task(job_id, release_time_iso):
    project = os.getenv('TASKS_PROJECT') or os.getenv('GOOGLE_CLOUD_PROJECT')
    queue = os.getenv('CLOUD_TASKS_QUEUE', 'pinseeker-queue')
    location = os.getenv('CLOUD_TASKS_LOCATION', 'us-east1')
    service_url = os.getenv('BASE_URL') # e.g. https://pinseeker-xxx.a.run.app
    
    if not all([project, service_url]):
        print("Skipping Cloud Task creation: GOOGLE_CLOUD_PROJECT/TASKS_PROJECT or BASE_URL not set.")
        return None

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)
    
    # Schedule for 60 seconds before release
    release_time = datetime.datetime.fromisoformat(release_time_iso)
    schedule_time = release_time - datetime.timedelta(seconds=60)
    
    # Cloud Tasks requires a timestamp in the future. 
    # If release is very soon, schedule for 'now'
    now = datetime.datetime.now(datetime.timezone.utc)
    if schedule_time < now:
        schedule_time = now + datetime.timedelta(seconds=5)

    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(schedule_time)
    
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{service_url.rstrip('/')}/api/execute-job",
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"job_id": "{job_id}"}}'.encode(),
            "oidc_token": {
                "service_account_email": os.getenv('TASK_SERVICE_ACCOUNT_EMAIL')
            }
        },
        "schedule_time": timestamp
    }
    
    try:
        response = client.create_task(parent=parent, task=task)
        print(f"Created Cloud Task: {response.name}")
        return response.name
    except Exception as e:
        print(f"Failed to create Cloud Task: {e}")
        return None

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

        # Schedule a Cloud Task for event-driven execution
        schedule_booking_task(job_id, booking_request.release_time)

        return {"status": "success", "job_id": job_id, "message": "Booking request queued."}
    except Exception as e:
        print(f"Firestore error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save booking request")

class ExecuteJobRequest(BaseModel):
    job_id: str

@app.post("/api/execute-job")
async def execute_job(req: ExecuteJobRequest):
    """Called by Cloud Tasks to execute a specific booking job."""
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    doc_ref = db.collection('tee_time_jobs').document(req.job_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_data = doc.to_dict()
    
    # Import execute_booking from worker.py
    # We do this inside the function to avoid circular imports or early initialization issues
    from worker import execute_booking
    
    # We run it synchronously here so Cloud Run stays active until it finishes.
    # Cloud Tasks will wait for the response.
    try:
        execute_booking(req.job_id, job_data)
        return {"status": "success", "job_id": req.job_id}
    except Exception as e:
        print(f"Execution error: {e}")
        # Returning a non-2xx would cause Cloud Tasks to retry. 
        # For now we return 200 but the job status in Firestore will be FAILED.
        return {"status": "failed", "error": str(e)}

@app.get("/api/cron")
async def trigger_cron():
    """Cleanup stale jobs (Missed release windows)."""
    if not db:
        return {"status": "error", "message": "Database not initialized"}
        
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    cleaned_jobs = []
    
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
            
            # Clean up stale jobs that were missed (more than 5 minutes in the past)
            if time_until_release <= -300:
                print(f"Cron marking stale job {doc.id} as FAILED (Missed release window).")
                db.collection('tee_time_jobs').document(doc.id).update({
                    "status": "FAILED",
                    "result_log": "Missed release window (bot was not running or scheduler failed)",
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
                cleaned_jobs.append(doc.id)
                
        return {"status": "success", "cleaned_jobs": cleaned_jobs}
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

