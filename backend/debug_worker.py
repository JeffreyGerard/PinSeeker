import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

# Ensure we can import Django models and playwright logic
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinseeker.settings')
import django
django.setup()

from bookings.models import GolfCourse, UserCredential
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
from utils import decrypt_password

# Mock booking object mirroring the Cloud Run payload parsing
class MockBooking:
    def __init__(self, desired_date, earliest_time_str, latest_time_str, players=4):
        self.id = 999
        self.desired_date = desired_date
        self.earliest_time = datetime.strptime(earliest_time_str, '%H:%M:%S').time()
        self.latest_time = datetime.strptime(latest_time_str, '%H:%M:%S').time()
        self.players = players
        self.status = 'RUNNING'
        self.result_log = ""
    def save(self): pass # Mock save

def run_debug(course_name, target_date_str=None, earliest="07:00:00", latest="11:00:00", players=4, dry_run=True):
    # Find the course
    course = GolfCourse.objects.filter(name__icontains=course_name).first()
    if not course:
        print(f"ERROR: Could not find a course matching '{course_name}'")
        available = ", ".join([c.name for c in GolfCourse.objects.all()])
        print(f"Available courses: {available}")
        sys.exit(1)

    print(f"Found Course: {course.name} ({course.logic_type})")

    # Find credentials
    cred = UserCredential.objects.filter(course=course).first()
    if not cred:
        print(f"WARNING: No credentials found for {course.name} in the database.")
        print("Using dummy credentials 'test@example.com' / 'password'. The script will likely fail at login.")
        email = "test@example.com"
        password = "password"
    else:
        email = cred.course_email
        password = decrypt_password(cred.encrypted_password)
        print(f"Using credentials for: {email}")

    # Parse dates
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            print("ERROR: Date must be in YYYY-MM-DD format.")
            sys.exit(1)
    else:
        # Default to 7 days from now
        target_date = date.today() + timedelta(days=7)

    booking_obj = MockBooking(target_date, earliest, latest, players)

    print(f"\n--- Starting Debug Run ---")
    print(f"Target Date: {target_date.strftime('%Y-%m-%d')}")
    print(f"Time Window: {earliest} - {latest}")
    print(f"Players:     {players}")
    print(f"Dry Run:     {dry_run}")
    print(f"--------------------------\n")

    result = ""
    logic = course.logic_type
    url = course.url

    try:
        if logic == 'foreup':
            if "Orchard" in course.name:
                result = book_orchard_creek(url, booking_obj, email, password, dry_run=dry_run)
            elif "Van Patten" in course.name:
                result = book_van_patten(url, booking_obj, email, password, dry_run=dry_run)
            else:
                result = book_via_foreup_software(url, booking_obj, email, password, dry_run=dry_run)
        elif logic == 'foreup_new':
            if "Stadium" in course.name:
                result = book_stadium(url, booking_obj, email, password, dry_run=dry_run)
            elif "Fairways" in course.name:
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

        print(f"\n[SUCCESS] Result:\n{result}")

    except Exception as e:
        import traceback
        print(f"\n[FAILED] Error Details:")
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug Playwright scripts for specific golf courses.")
    parser.add_argument("course", help="Part of the course name to test (e.g., 'Orchard', 'Capital')")
    parser.add_argument("-d", "--date", help="Target date in YYYY-MM-DD format (defaults to 7 days from today)")
    parser.add_argument("-e", "--earliest", default="07:00:00", help="Earliest time (HH:MM:SS), default 07:00:00")
    parser.add_argument("-l", "--latest", default="11:00:00", help="Latest time (HH:MM:SS), default 11:00:00")
    parser.add_argument("-p", "--players", type=int, default=4, help="Number of players, default 4")
    parser.add_argument("--book", action="store_true", help="Turn off dry_run and ACTUALLY BOOK the tee time")

    args = parser.parse_args()

    # If --book is passed, dry_run is False
    is_dry_run = not args.book

    run_debug(
        course_name=args.course,
        target_date_str=args.date,
        earliest=args.earliest,
        latest=args.latest,
        players=args.players,
        dry_run=is_dry_run
    )
