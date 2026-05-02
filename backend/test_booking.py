import os
import django
import sys
from datetime import date, time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinseeker.settings')
django.setup()

from bookings.models import GolfCourse, BookingRequest, UserCredential
from bookings.playwright_logic import book_cps_golf, book_via_foreup_new, book_via_foreup_software
from bookings.utils import decrypt_password

def test_booking():
    try:
        course = GolfCourse.objects.get(name="Orchard Creek")
    except GolfCourse.DoesNotExist:
        print("Course not found in database.")
        sys.exit(1)

    cred = UserCredential.objects.filter(course=course).first()
    if not cred:
        print(f"No credentials found for {course.name}")
        sys.exit(1)

    # Real booking for April 24, 2026 (matching successful UI session)
    target_date = date(2026, 4, 24)
    
    booking = BookingRequest(
        course=course,
        desired_date=target_date,
        earliest_time=time(8, 0),  # Broad window to ensure we find a slot
        latest_time=time(18, 0), 
        players=4
    )

    print(f"==================================================")
    print(f"ACTUAL BOOKING TEST (dry_run=False):")
    print(f"Course: {course.name}")
    print(f"Date: {booking.desired_date}")
    print(f"Time Window: {booking.earliest_time.strftime('%I:%M %p')} to {booking.latest_time.strftime('%I:%M %p')}")
    print(f"Players: {booking.players}")
    print(f"==================================================")

    try:
        res = book_via_foreup_software(
            course.url, 
            course.public_btn_xpath, 
            booking, 
            cred.course_email, 
            decrypt_password(cred.encrypted_password), 
            dry_run=False
        )
        print(f"\nBOOKING RESULT: {res}")
    except Exception as e:
        print(f"\nBOOKING FAILED: {str(e)}")

if __name__ == "__main__":
    test_booking()
