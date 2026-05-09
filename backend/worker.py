import time
import datetime
import os
import logging
from google.cloud import firestore

# Import the user's Playwright logic
import playwright_logic

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the service account key is loaded
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "service-account.json")

# Initialize Firestore
try:
    db = firestore.Client(project='jeff-gcp-project')
except Exception as e:
    logging.error(f"Failed to connect to Firestore: {e}")
    exit(1)

# Compatibility Wrapper
class BookingWrapper:
    """Wraps Firestore dictionary data to act like the Django model expected by playwright_logic"""
    def __init__(self, data):
        self.desired_date = datetime.date.fromisoformat(data['desired_date'])
        
        # playwright_logic parse_time expects string times in %H:%M:%S format to convert to objects later, 
        # or it expects time objects. The logic uses datetime.combine(date_obj, time_obj)
        # So we convert the string '07:00:00' to a datetime.time object
        self.earliest_time = datetime.time.fromisoformat(data['earliest_time'])
        self.latest_time = datetime.time.fromisoformat(data['latest_time'])
        
        self.players = int(data['players'])
        self.course_name = data.get('course_name')

import argparse

def execute_booking(job_id, job_data, dry_run=False):
    logging.info(f"Executing Snipe for Job {job_id} at {job_data['course_name']} (Dry Run: {dry_run})")
    
    # 1. Update status to RUNNING
    doc_ref = db.collection('tee_time_jobs').document(job_id)
    doc_ref.update({"status": "RUNNING"})

    # 2. Prepare the data wrapper
    booking = BookingWrapper(job_data)
    course_name = job_data.get('course_name', '').lower()


    
    email = job_data.get('course_email', 'user@example.com')
    password = job_data.get('course_password', 'password123')

    try:
        logging.info(f"Routing to correct booking function for: {course_name}")
        result_message = ""

        # 3. The Course Router
        if "capital hills" in course_name:
            result_message = playwright_logic.book_cps_golf("https://cps.com/capital", booking, email, password, dry_run=dry_run)
        elif "post road" in course_name:
            result_message = playwright_logic.book_cps_old_post("https://cps.com/post", booking, email, password, dry_run=dry_run)
        elif "orchard creek" in course_name:
            result_message = playwright_logic.book_orchard_creek("https://foreupsoftware.com/index.php/booking/20340/3565", booking, email, password, dry_run=dry_run)
        elif "schenectady" in course_name:
            result_message = playwright_logic.book_schenectady_muni("https://foreupsoftware.com/index.php/booking/19692/2163", booking, email, password, dry_run=dry_run)
        elif "fairways" in course_name:
            result_message = playwright_logic.book_fairways_halfmoon("https://foreupsoftware.com/index.php/booking/19714/2324", booking, email, password, dry_run=dry_run)
        elif "stadium" in course_name:
            result_message = playwright_logic.book_stadium("https://foreupsoftware.com/index.php/booking/19765/2544", booking, email, password, dry_run=dry_run)
        elif "van patten" in course_name:
            result_message = playwright_logic.book_van_patten("https://foreupsoftware.com/index.php/booking/19765/2544", booking, email, password, dry_run=dry_run)
        elif "eagle crest" in course_name:
            # Requires CC info, passing None for now as per function defaults
            result_message = playwright_logic.book_via_eagleclub("https://eaglecrest.com/book", booking, email, password, dry_run=dry_run)
        else:
            raise Exception(f"No routing logic found for course: {course_name}")

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
        doc_ref = db.collection('tee_time_jobs').document(args.debug_job)
        doc = doc_ref.get()
        if doc.exists:
            execute_booking(doc.id, doc.to_dict(), dry_run=args.dry_run)
        else:
            logging.error("Job ID not found in Firestore.")
    else:
        # Normal production flow
        find_and_wait_for_job()
