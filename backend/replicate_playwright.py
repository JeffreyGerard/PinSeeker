import os
import sys
import time
from datetime import datetime, date, timedelta

# Import the logic we want to debug
import playwright_logic

# ---------------------------------------------------------------------------
# MOCK DATA - EDIT THESE FOR YOUR TEST
# ---------------------------------------------------------------------------
COURSE_TO_TEST = "capital_hills"  # Options: capital_hills, old_post, orchard_creek, schenectady, fairways, stadium, van_patten, eagle_crest
TARGET_DATE = date.today() + timedelta(days=7)  # Default: 7 days from now
EARLIEST_TIME = "07:00:00"
LATEST_TIME = "11:00:00"
PLAYERS = 4
DRY_RUN = True  # Set to False to actually attempt booking

# Credentials (Use .env or hardcode for local debug only)
EMAIL = os.environ.get("GOLF_EMAIL", "your_email@example.com")
PASSWORD = os.environ.get("GOLF_PASSWORD", "your_password")

# URLs for reference (copied from worker.py)
URLS = {
    "capital_hills": "https://cps.com/capital",
    "old_post": "https://cps.com/post",
    "orchard_creek": "https://foreupsoftware.com/index.php/booking/20340/3565",
    "schenectady": "https://foreupsoftware.com/index.php/booking/19692/2163",
    "fairways": "https://foreupsoftware.com/index.php/booking/19714/2324",
    "stadium": "https://foreupsoftware.com/index.php/booking/19765/2544",
    "van_patten": "https://foreupsoftware.com/index.php/booking/19765/2544",
    "eagle_crest": "https://eaglecrest.com/book"
}

# ---------------------------------------------------------------------------
# MOCK OBJECTS
# ---------------------------------------------------------------------------

class MockBooking:
    """Wraps data to act like the object expected by playwright_logic"""
    def __init__(self, desired_date, earliest, latest, players):
        self.desired_date = desired_date
        self.earliest_time = datetime.strptime(earliest, '%H:%M:%S').time()
        self.latest_time = datetime.strptime(latest, '%H:%M:%S').time()
        self.players = players

def run_replication():
    print(f"--- REPLICATING JOB ---")
    print(f"Course:   {COURSE_TO_TEST}")
    print(f"Date:     {TARGET_DATE}")
    print(f"Window:   {EARLIEST_TIME} - {LATEST_TIME}")
    print(f"Players:  {PLAYERS}")
    print(f"Dry Run:  {DRY_RUN}")
    print(f"Email:    {EMAIL}")
    print(f"-----------------------\n")

    booking = MockBooking(TARGET_DATE, EARLIEST_TIME, LATEST_TIME, PLAYERS)
    url = URLS.get(COURSE_TO_TEST)
    
    if not url:
        print(f"ERROR: Unknown course '{COURSE_TO_TEST}'")
        return

    try:
        if COURSE_TO_TEST == "capital_hills":
            result = playwright_logic.book_cps_golf(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "old_post":
            result = playwright_logic.book_cps_old_post(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "orchard_creek":
            result = playwright_logic.book_orchard_creek(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "schenectady":
            result = playwright_logic.book_schenectady_muni(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "fairways":
            result = playwright_logic.book_fairways_halfmoon(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "stadium":
            result = playwright_logic.book_stadium(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "van_patten":
            result = playwright_logic.book_van_patten(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        elif COURSE_TO_TEST == "eagle_crest":
            result = playwright_logic.book_via_eagleclub(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN)
        else:
            print("Logic not implemented in this debug script yet.")
            return

        print(f"\n[SUCCESS] Result: {result}")

    except Exception as e:
        import traceback
        print(f"\n[FAILED] Error:")
        traceback.print_exc()

if __name__ == "__main__":
    run_replication()
