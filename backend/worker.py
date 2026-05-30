import time
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
    db = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT', 'pinseeker-app'))
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

# Course Configuration Map - Synchronized with replicate_playwright.py
COURSE_CONFIG = {
    "capital hills": {
        "url": "https://capitalhillsny.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_cps_golf,
    },
    "eagle crest": {
        "url": "https://player.eagleclubsystems.online/#/tee-slot?dbname=eaglecrest20260101",
        "func": playwright_logic.book_via_eagleclub,
    },
    "fairways": {
        "url": "https://foreupsoftware.com/index.php/booking/22948/12410#/welcome",
        "func": playwright_logic.book_fairways_halfmoon,
    },
    "post road": {
        "url": "https://oldepostroad.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_cps_old_post,
    },
    "orchard creek": {
        "url": "https://foreupsoftware.com/index.php/booking/19530/1791?_gl=1*yg2s5f*_ga*OTc1NDk3MjU5LjE3Nzc3Mjc1NDE.*_ga_WQPLP348DP*czE3NzgzMjYwMTEkbzIkZzAkdDE3NzgzMjYwMTEkajYwJGwwJGgw#teetimes",
        "func": playwright_logic.book_orchard_creek,
    },
    "schenectady": {
        "url": "https://foreupsoftware.com/index.php/booking/20480/4739?_gl=1*is3gta*_ga*MzM4MjY1MTE4LjE3NzgzMjYxMzA.*_ga_WQPLP348DP*czE3NzgzMjYxMzAkbzEkZzAkdDE3NzgzMjYxMzMkajU3JGwwJGgw#/teetimes",
        "func": playwright_logic.book_schenectady_muni,
    },
    "stadium": {
        "url": "https://foreupsoftware.com/index.php/booking/index/3332#teetimes",
        "func": playwright_logic.book_stadium,
    },
    "colonie": {
        "url": "https://www.townofcolonie.gov/departments/parksandrec/golfcourse/book-teetime",
        "func": playwright_logic.book_town_of_colonie,
    },
    "van patten": {
        "url": "https://foreupsoftware.com/index.php/booking/19765/2544",
        "func": playwright_logic.book_van_patten,
    },
    "saratoga spa": {
        "url": "https://foreupsoftware.com/index.php/booking/21684/8618#/teetimes",
        "func": playwright_logic.book_saratoga_spa,
    }
}

def execute_booking(job_id, job_data, dry_run=False):
    logging.info(f"Executing Snipe for Job {job_id} at {job_data['course_name']} (Dry Run: {dry_run})")
    
    if db is None:
        raise ValueError("Firestore client is not initialized.")
        
    # 1. Update status to RUNNING
    doc_ref = db.collection('tee_time_jobs').document(job_id)
    doc_ref.update({"status": "RUNNING"})

    # 2. Prepare the data wrapper
    booking = BookingWrapper(job_data)
    course_query = job_data.get('course_name', '').lower()
    
    email = job_data.get('course_email', 'user@example.com')
    password = job_data.get('course_password', 'password123')

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
        result_message = handler["func"](handler["url"], booking, email, password, dry_run=dry_run)

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


def find_and_wait_for_job():
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
                time.sleep(seconds_until_release)
                
                # Time is up! Execute!
                execute_booking(doc.id, job_data)
                
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
            execute_booking(doc.id, doc.to_dict(), dry_run=args.dry_run)
        else:
            logging.error("Job ID not found in Firestore.")
    else:
        # Normal production flow
        find_and_wait_for_job()
