import os
import sys
import time
from datetime import datetime, date, timedelta

# Import the logic we want to debug
import playwright_logic

# ---------------------------------------------------------------------------
# MOCK DATA - EDIT THESE FOR YOUR TEST
# ---------------------------------------------------------------------------
COURSE_TO_TEST = "orchard_creek"  # Options: capital_hills, old_post, orchard_creek, schenectady, fairways, stadium, van_patten, eagle_crest
TARGET_DATE = date.today() + timedelta(days=2)  # Default: 7 days from now
EARLIEST_TIME = "07:00:00"
LATEST_TIME = "11:00:00"
PLAYERS = 4
DRY_RUN = False  # Set to False to actually attempt booking

# Credentials (Use .env or hardcode for local debug only)
EMAIL = "jeff.gerard05@gmail.com"
PASSWORD = "Password101"

# URLs for reference (copied from worker.py)
URLS = {
    "capital_hills": "https://capitalhillsny.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
    "eagle_crest": "https://player.eagleclubsystems.online/#/tee-slot?dbname=eaglecrest20260101",
    "fairways": "https://foreupsoftware.com/index.php/booking/22948/12410#/welcome",
    "old_post": "https://oldepostroad.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
    "orchard_creek": "https://foreupsoftware.com/index.php/booking/19530/1791?_gl=1*yg2s5f*_ga*OTc1NDk3MjU5LjE3Nzc3Mjc1NDE.*_ga_WQPLP348DP*czE3NzgzMjYwMTEkbzIkZzAkdDE3NzgzMjYwMTEkajYwJGwwJGgw#teetimes",
    "schenectady": "https://foreupsoftware.com/index.php/booking/20480/4739?_gl=1*is3gta*_ga*MzM4MjY1MTE4LjE3NzgzMjYxMzA.*_ga_WQPLP348DP*czE3NzgzMjYxMzAkbzEkZzAkdDE3NzgzMjYxMzMkajU3JGwwJGgw#/teetimes",
    "stadium": "https://foreupsoftware.com/index.php/booking/index/3332#teetimes",
    "van_patten": "https://foreupsoftware.com/index.php/booking/19765/2544"
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
