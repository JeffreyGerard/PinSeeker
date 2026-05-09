from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google.cloud import firestore
import datetime
import os
import uuid

# Initialize FastAPI
app = FastAPI(title="PinSeeker API")

# Initialize Firestore
# Note: Cloud Run automatically handles authentication if the service account is configured correctly.
# If running locally for testing, ensure GOOGLE_APPLICATION_CREDENTIALS is set.
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

@app.get("/api/bookings")
async def list_bookings(passcode: str = ""):
    EXPECTED_PASSCODE = os.getenv("APP_PASSCODE", "golf2026")
    if passcode != EXPECTED_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
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
async def create_booking(request: BookingRequest):
    # Simple stateless authentication
    EXPECTED_PASSCODE = os.getenv("APP_PASSCODE", "golf2026")
    if request.passcode != EXPECTED_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Passcode")

    if not db:
        raise HTTPException(status_code=500, detail="Database connection not available")

    # Generate a unique ID for the job
    job_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    job_data = {
        "id": job_id,
        "status": "PENDING",
        "course": request.course,
        "course_name": request.course_name,
        "desired_date": request.desired_date,
        "earliest_time": request.earliest_time,
        "latest_time": request.latest_time,
        "players": request.players,
        "release_time": request.release_time,
        "course_email": request.course_email,
        "course_password": request.course_password,
        "created_at": now,
        "updated_at": now
    }

    try:
        # Write to Firestore collection 'tee_time_jobs'
        doc_ref = db.collection('tee_time_jobs').document(job_id)
        doc_ref.set(job_data)
        return {"status": "success", "job_id": job_id, "message": "Booking request queued."}
    except Exception as e:
        print(f"Firestore error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save booking request")

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

