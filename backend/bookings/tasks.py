
from celery import shared_task
from .models import BookingRequest, UserCredential
from .utils import decrypt_password
from .playwright_logic import book_via_foreup_software, book_via_foreup_new, book_cps_golf
import traceback
import logging

logger = logging.getLogger(__name__)

@shared_task
def execute_booking(request_id):
    # 1. Load Request
    try:
        booking = BookingRequest.objects.get(id=request_id)
    except BookingRequest.DoesNotExist:
        return "Request not found"

    # 2. Load Credentials
    try:
        creds = UserCredential.objects.get(user=booking.user, course=booking.course)
        password = decrypt_password(creds.encrypted_password)
        email = creds.course_email
    except UserCredential.DoesNotExist:
        booking.status = 'FAILED'
        booking.result_log = "Missing credentials. Please configure them in the System Database (Admin Panel)."
        booking.save()
        return

    # 3. Execute Booking with Playwright
    try:
        booking.status = 'RUNNING'
        booking.save()
        
        logic = booking.course.logic_type
        url = booking.course.url
        xpath = booking.course.public_btn_xpath
        
        result = ""
        
        logger.info(f"Starting booking for {booking.id} using logic {logic}")

        if logic == 'foreup':
            result = book_via_foreup_software(url, xpath, booking, email, password)
        elif logic == 'foreup_new':
            result = book_via_foreup_new(url, xpath, booking, email, password)
        elif logic == 'cps':
            result = book_cps_golf(url, booking, email, password)
        elif logic == 'frear':
            # Placeholder for future logic
            result = "Simulation: Frear Park logic not yet implemented."
        elif logic == 'schenectady':
            # Placeholder for future logic
            result = "Simulation: Schenectady logic not yet implemented."
        else:
            result = f"Unknown logic type: {logic}"

        booking.status = 'SUCCESS'
        booking.result_log = result
        booking.save()
        return result

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Booking failed: {error_trace}")
        booking.status = 'FAILED'
        booking.result_log = f"Error: {str(e)}\n\n{error_trace}"
        booking.save()
        return f"Failed: {str(e)}"
