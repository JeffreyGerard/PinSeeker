import os
import json
import logging
from google.cloud import run_v2
from utils import decrypt_password

logger = logging.getLogger(__name__)

def trigger_booking_job(booking_request, task_type='booking', dry_run=False):
    """
    Triggers a Cloud Run Job to perform the booking/health check.
    """
    project_id = os.getenv('GCP_PROJECT_ID')
    location = os.getenv('GCP_LOCATION', 'us-east1')
    job_name = os.getenv('GCP_CLOUD_RUN_JOB_NAME', 'pinseeker-worker')
    webhook_url = os.getenv('WEBHOOK_URL')
    webhook_secret = os.getenv('WEBHOOK_SECRET')

    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot trigger job.")
        return False

    client = run_v2.JobsClient()

    # Prepare payload
    try:
        from .models import UserCredential
        cred = UserCredential.objects.get(user=booking_request.user, course=booking_request.course)
        password = decrypt_password(cred.encrypted_password)
        email = cred.course_email
    except Exception as e:
        logger.error(f"Failed to prepare credentials for job: {e}")
        return False

    payload = {
        "booking_id": booking_request.id,
        "task_type": task_type,
        "logic_type": booking_request.course.logic_type,
        "url": booking_request.course.url,
        "course_name": booking_request.course.name,
        "email": email,
        "password": password,
        "desired_date": booking_request.desired_date.isoformat(),
        "earliest_time": booking_request.earliest_time.isoformat(),
        "latest_time": booking_request.latest_time.isoformat(),
        "players": booking_request.players,
        "dry_run": dry_run
    }

    # Execute Job
    try:
        job_path = client.job_path(project_id, location, job_name)
        
        # Override environment variables for this specific execution
        overrides = {
            "container_overrides": [
                {
                    "env": [
                        {"name": "JOB_PAYLOAD", "value": json.dumps(payload)},
                        {"name": "WEBHOOK_URL", "value": webhook_url},
                        {"name": "WEBHOOK_SECRET", "value": webhook_secret},
                    ]
                }
            ]
        }

        request = run_v2.RunJobRequest(
            name=job_path,
            overrides=overrides
        )

        operation = client.run_job(request=request)
        logger.info(f"Triggered Cloud Run Job: {operation.operation.name}")
        
        booking_request.status = 'RUNNING'
        booking_request.save()
        return True

    except Exception as e:
        logger.error(f"Failed to trigger Cloud Run Job: {e}")
        booking_request.status = 'FAILED'
        booking_request.result_log = f"Trigger Error: {str(e)}"
        booking_request.save()
        return False
