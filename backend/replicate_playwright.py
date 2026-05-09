from datetime import datetime, date, timedelta
import traceback

# Import the logic we want to debug
import playwright_logic

# ---------------------------------------------------------------------------
# MOCK DATA - EDIT THESE FOR YOUR TEST
# ---------------------------------------------------------------------------
COURSE_TO_TEST = "orchard_creek"  # Options: capital_hills, old_post, orchard_creek, schenectady, fairways, stadium, van_patten, eagle_crest
TARGET_DATE = date.today() + timedelta(days=2)
EARLIEST_TIME = "07:00:00"
LATEST_TIME = "11:00:00"
PLAYERS = 4
DRY_RUN = False  # Set to False to actually attempt booking
HEADLESS = False  # Set to True for hidden browser, False to see what is happening

# Credentials (Use .env or hardcode for local debug only)
# IMPORTANT: For local debugging only. Do not commit credentials.
EMAIL = "jeff.gerard05@gmail.com"
PASSWORD = "Password101"

# ---------------------------------------------------------------------------
# HANDLER DISPATCH TABLE
# ---------------------------------------------------------------------------

COURSE_HANDLERS = {
    "capital_hills": {
        "url": "https://capitalhillsny.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_cps_golf,
    },
    "eagle_crest": {
        "url": "https://player.eagleclubsystems.online/#/tee-slot?dbname=eaglecrest20260101",
        "func": playwright_logic.book_via_eagleclub,
    },
    "fairways": {
        "url": "https://foreupsoftware.com/index.php/booking/22948/12410#/welcome",
        "func": playwright_logic.book_fairways_halfmoon,
    },
    "old_post": {
        "url": "https://oldepostroad.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_cps_old_post,
    },
    "orchard_creek": {
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
    "van_patten": {
        "url": "https://foreupsoftware.com/index.php/booking/19765/2544",
        "func": playwright_logic.book_van_patten,
    }
}

# ---------------------------------------------------------------------------
# MOCK OBJECTS & EXECUTION
# ---------------------------------------------------------------------------

class MockBooking:
    """Wraps data to act like the object expected by playwright_logic"""
    def __init__(self, desired_date, earliest, latest, players):
        self.desired_date = desired_date
        self.earliest_time = datetime.strptime(earliest, '%H:%M:%S').time()
        self.latest_time = datetime.strptime(latest, '%H:%M:%S').time()
        self.players = players

def run_replication():
    """Runs the replication using the configured settings and dispatch table."""
    print(f"--- REPLICATING JOB ---")
    print(f"Course:   {COURSE_TO_TEST}")
    print(f"Date:     {TARGET_DATE}")
    print(f"Window:   {EARLIEST_TIME} - {LATEST_TIME}")
    print(f"Players:  {PLAYERS}")
    print(f"Dry Run:  {DRY_RUN}")
    print(f"Headless: {HEADLESS}")
    print(f"-----------------------\n")

    booking = MockBooking(TARGET_DATE, EARLIEST_TIME, LATEST_TIME, PLAYERS)
    
    handler = COURSE_HANDLERS.get(COURSE_TO_TEST)
    if not handler:
        print(f"ERROR: Unknown course '{COURSE_TO_TEST}'. Check COURSE_HANDLERS dictionary.")
        return

    url = handler["url"]
    book_func = handler["func"]

    try:
        result = book_func(url, booking, EMAIL, PASSWORD, dry_run=DRY_RUN, headless=HEADLESS)
        print(f"[SUCCESS] Result: {result}")

    except Exception:
        print(f"[FAILED] An error occurred while running the script for {COURSE_TO_TEST}:")
        traceback.print_exc()

if __name__ == "__main__":
    run_replication()
