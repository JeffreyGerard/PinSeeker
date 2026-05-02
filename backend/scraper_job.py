import os
import sys
import json
import requests
import logging
from playwright_logic import (
    book_via_foreup_software,
    book_cps_golf,
    book_cps_old_post,
    book_via_eagleclub,
    book_orchard_creek,
    book_schenectady_muni,
    book_fairways_halfmoon,
    book_stadium,
    book_van_patten
)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_job():
    payload_str = os.environ.get('JOB_PAYLOAD')
    webhook_url = os.environ.get('WEBHOOK_URL')
    webhook_secret = os.environ.get('WEBHOOK_SECRET')

    if not payload_str:
        logger.error("No JOB_PAYLOAD found in environment.")
        sys.exit(1)

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("Failed to decode JOB_PAYLOAD JSON.")
        sys.exit(1)

    task_type = payload.get('task_type', 'booking')
    booking_id = payload.get('booking_id')
    
    # Extract data for logic
    logic = payload.get('logic_type')
    url = payload.get('url')
    email = payload.get('email')
    password = payload.get('password')
    course_name = payload.get('course_name', '')
    
    # Create a mock booking object for the playwright logic
    from datetime import datetime
    class MockBooking:
        def __init__(self, data):
            self.id = data.get('booking_id')
            self.desired_date = datetime.strptime(data['desired_date'], '%Y-%m-%d').date()
            self.earliest_time = datetime.strptime(data['earliest_time'], '%H:%M:%S').time()
            self.latest_time = datetime.strptime(data['latest_time'], '%H:%M:%S').time()
            self.players = data.get('players', 4)
            self.status = 'RUNNING'
            self.result_log = ""
        def save(self): pass # Mock save

    booking_obj = MockBooking(payload)
    dry_run = payload.get('dry_run', False)

    result = ""
    status = "SUCCESS"

    try:
        logger.info(f"Starting {task_type} for ID {booking_id} using logic {logic}")
        
        if logic == 'foreup':
            if "Orchard" in course_name:
                result = book_orchard_creek(url, booking_obj, email, password, dry_run=dry_run)
            elif "Van Patten" in course_name:
                result = book_van_patten(url, booking_obj, email, password, dry_run=dry_run)
            else:
                result = book_via_foreup_software(url, booking_obj, email, password, dry_run=dry_run)
        elif logic == 'foreup_new':
            if "Stadium" in course_name:
                result = book_stadium(url, booking_obj, email, password, dry_run=dry_run)
            elif "Fairways" in course_name:
                result = book_fairways_halfmoon(url, booking_obj, email, password, dry_run=dry_run)
            else:
                result = book_via_foreup_software(url, booking_obj, email, password, dry_run=dry_run)
        elif logic == 'cps':
            result = book_cps_golf(url, booking_obj, email, password, dry_run=dry_run)
        elif logic == 'cps_old_post':
            result = book_cps_old_post(url, booking_obj, email, password, dry_run=dry_run)
        elif logic == 'schenectady':
            result = book_schenectady_muni(url, booking_obj, email, password, dry_run=dry_run)
        elif logic == 'eagleclub':
            result = book_via_eagleclub(url, booking_obj, email, password, dry_run=dry_run)
        else:
            result = f"Unknown logic type: {logic}"
            status = "FAILED"

    except Exception as e:
        import traceback
        result = f"Error: {str(e)}\n\n{traceback.format_exc()}"
        status = "FAILED"
        logger.error(f"Job failed: {result}")

    # Report back via Webhook
    if webhook_url:
        logger.info(f"Reporting result to webhook: {webhook_url}")
        try:
            response = requests.post(
                webhook_url,
                json={
                    "booking_id": booking_id,
                    "status": status,
                    "result_log": result,
                    "task_type": task_type
                },
                headers={"X-Webhook-Secret": webhook_secret},
                timeout=30
            )
            response.raise_for_status()
            logger.info("Webhook delivered successfully.")
        except Exception as e:
            logger.error(f"Failed to deliver webhook: {e}")

if __name__ == "__main__":
    run_job()
