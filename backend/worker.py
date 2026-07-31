import asyncio
import datetime
import os
import logging
import argparse
import sys
from google.cloud import firestore

# Import the user's Playwright logic
import playwright_logic

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load local service account key if it exists for local testing, otherwise use default credentials
sa_path = os.path.join(os.getcwd(), "service-account.json")
if os.path.exists(sa_path):
    logging.info(f"Using local service account credentials from {sa_path}")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path
    try:
        import json
        with open(sa_path, "r") as f:
            sa_data = json.load(f)
            project_id = sa_data.get("project_id")
            if project_id:
                logging.info(f"Auto-configured GOOGLE_CLOUD_PROJECT to: {project_id}")
                os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    except Exception as e:
        logging.warning(f"Failed to parse service-account.json project ID: {e}")
else:
    logging.info("service-account.json not found. Relying on default GCP credentials.")

# Initialize Firestore
try:
    db = firestore.Client()
except Exception as e:
    logging.error(f"Failed to connect to Firestore: {e}")
    exit(1)

# Compatibility Wrapper
class BookingWrapper:
    """Wraps Firestore dictionary data to act like the object expected by playwright_logic"""
    def __init__(self, data):
        self.desired_date = datetime.date.fromisoformat(data['desired_date'])
        self.earliest_time = datetime.time.fromisoformat(data['earliest_time'])
        self.latest_time = datetime.time.fromisoformat(data['latest_time'])
        self.players = int(data['players'])
        self.course_name = data.get('course_name')
        self.release_time = data.get('release_time')

# Course Configuration - Single source of truth
from course_config import COURSE_CONFIG, get_handler

async def execute_booking(job_id, job_data, dry_run=False):
    logging.info(f"Executing Snipe for Job {job_id} at {job_data['course_name']} (Dry Run: {dry_run})")
    
    if db is None:
        raise ValueError("Firestore client is not initialized.")
        
    doc_ref = db.collection('tee_time_jobs').document(job_id)

    @firestore.transactional
    def claim_job_transaction(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        if not snapshot.exists:
            return False, "Not found"
        
        current_status = snapshot.get('status')
        if current_status != 'PENDING':
            return False, f"Status is '{current_status}'"
            
        transaction.update(ref, {"status": "RUNNING"})
        return True, "Claimed"

    transaction = db.transaction()
    success, reason = claim_job_transaction(transaction, doc_ref)
    
    if not success:
        logging.info(f"Job {job_id} could not be claimed. Reason: {reason}. Skipping execution.")
        return

    # 2. Prepare the data wrapper
    booking = BookingWrapper(job_data)
    course_query = job_data.get('course_name', '').lower()
    
    email = job_data.get('course_email', 'user@example.com')
    password = job_data.get('course_password', 'password123')

    # Decrypt the password if it was encrypted at storage time
    if job_data.get('password_encrypted') and password:
        try:
            from utils import decrypt_password
            password = decrypt_password(password)
        except Exception as e:
            logging.error(f"Failed to decrypt course_password for job {job_id}: {e}")
            raise Exception(f"Password decryption failed: {e}")

    try:
        # 3. The Course Router
        handler = None
        for key, config in COURSE_CONFIG.items():
            if key in course_query:
                handler = config
                break
        
        if not handler:
            raise Exception(f"No routing logic found for course: {course_query}")

        logging.info(f"Routing to {handler['func'].__name__} with URL: {handler['url']}")
        result_message = await handler["func"](handler["url"], booking, email, password, dry_run=dry_run)

        # 4. If successful:
        logging.info(f"Booking Automation Successful! Result: {result_message}")
        doc_ref.update({
            "status": "SUCCESS", 
            "result_log": result_message,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    except Exception as e:
        logging.error(f"Automation failed: {e}")
        doc_ref.update({
            "status": "FAILED", 
            "result_log": str(e),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        # Try to capture and upload error screenshot from screenshots/ folder
        try:
            import base64
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            if os.path.exists(screenshot_dir):
                files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
                if files:
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(screenshot_dir, x)), reverse=True)
                    newest_file = files[0]
                    full_path = os.path.join(screenshot_dir, newest_file)
                    with open(full_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    doc_ref.update({
                        "error_screenshot": f"data:image/png;base64,{encoded_string}"
                    })
                    logging.info(f"Successfully uploaded error screenshot {newest_file} to Firestore.")
                    os.remove(full_path)
        except Exception as se:
            logging.warning(f"Failed to capture and upload error screenshot: {se}")


async def find_and_wait_for_job():
    logging.info("Windows Sniper started. Checking for imminent jobs...")
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    if db is None:
        logging.error("Firestore client is not initialized.")
        return
        
    try:
        jobs_ref = db.collection('tee_time_jobs').where('status', '==', 'PENDING')
        docs = jobs_ref.stream()

        for doc in docs:
            job_data = doc.to_dict()
            release_time_str = job_data.get('release_time')
            
            if not release_time_str:
                continue

            release_time = datetime.datetime.fromisoformat(release_time_str)
            time_until_release = release_time - now_utc
            seconds_until_release = time_until_release.total_seconds()

            if 0 < seconds_until_release <= (6 * 60):
                logging.info(f"Found imminent job {doc.id}. Target Time: {release_time_str}")
                logging.info(f"Waiting exactly {seconds_until_release:.2f} seconds...")
                
                # The crucial simple wait:
                await asyncio.sleep(seconds_until_release)
                
                # Time is up! Execute!
                await execute_booking(doc.id, job_data)
                
                # We only process one job per wake
                return
            
            elif seconds_until_release <= -60:
                # If the job is more than 1 minute in the past, mark it as failed/stale
                logging.warning(f"Marking stale job {doc.id} as FAILED (Missed window).")
                db.collection('tee_time_jobs').document(doc.id).update({
                    "status": "FAILED",
                    "result_log": "Missed release window (bot was not running or PC was asleep)",
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })

        logging.info("No imminent jobs found.")

    except Exception as e:
        logging.error(f"Error querying Firestore: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="PinSeeker Windows Worker")
    parser.add_argument('--debug-job', type=str, help="Instantly execute a specific job ID (bypasses wait timer)")
    parser.add_argument('--dry-run', action='store_true', help="Run the automation but don't click the final book button")
    args = parser.parse_args()

    if args.debug_job:
        logging.info(f"--- DEBUG MODE --- Forcing execution of job: {args.debug_job}")
        if db is None:
            logging.error("Firestore client is not initialized.")
            sys.exit(1)
        doc_ref = db.collection('tee_time_jobs').document(args.debug_job)
        doc = doc_ref.get()
        if doc.exists:
            asyncio.run(execute_booking(doc.id, doc.to_dict(), dry_run=args.dry_run))
        else:
            logging.error("Job ID not found in Firestore.")
    else:
        # Normal production flow
        asyncio.run(find_and_wait_for_job())
