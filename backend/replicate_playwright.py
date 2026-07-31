"""
PinSeeker Local Test Harness

Test scraper logic locally without Firestore or Cloud Tasks.
Reads credentials from .env file instead of hardcoding them.

Usage:
    # List available courses
    python replicate_playwright.py --list

    # Test a course (dry run, visible browser)
    python replicate_playwright.py --course "orchard creek" --date 2026-07-25 --headless false

    # Test with specific time window and players
    python replicate_playwright.py --course "fairways" --date 2026-07-25 --earliest 07:00 --latest 11:00 --players 2

    # Live run (actually attempts to book)
    python replicate_playwright.py --course "stadium" --date 2026-07-25 --live
"""
from datetime import datetime, date, timedelta
import traceback
import asyncio
import argparse
import os
import sys

# Load .env for credentials
from dotenv import load_dotenv
load_dotenv()

# Import the shared course config
from course_config import COURSE_CONFIG, get_handler, list_courses


class MockBooking:
    """Wraps data to act like the object expected by playwright_logic"""
    def __init__(self, desired_date, earliest, latest, players, release_time=None):
        self.desired_date = desired_date
        self.earliest_time = datetime.strptime(earliest, '%H:%M').time()
        self.latest_time = datetime.strptime(latest, '%H:%M').time()
        self.players = players
        self.release_time = release_time


def run_replication(course_name, target_date, earliest, latest, players, dry_run, headless, email, password):
    """Runs the replication using the configured settings."""
    handler = get_handler(course_name)
    if not handler:
        print(f"\n❌ ERROR: Unknown course '{course_name}'.")
        print(f"Available courses: {', '.join(list_courses())}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  PinSeeker Local Test")
    print(f"{'='*50}")
    print(f"  Course:    {course_name}")
    print(f"  Date:      {target_date}")
    print(f"  Window:    {earliest} - {latest}")
    print(f"  Players:   {players}")
    print(f"  Dry Run:   {dry_run}")
    print(f"  Headless:  {headless}")
    print(f"  Email:     {email}")
    print(f"  Function:  {handler['func'].__name__}")
    print(f"{'='*50}\n")

    booking = MockBooking(target_date, earliest, latest, players)
    url = handler["url"]
    book_func = handler["func"]

    try:
        result = asyncio.run(book_func(url, booking, email, password, dry_run=dry_run, headless=headless))
        print(f"\n✅ [SUCCESS] Result: {result}")
    except Exception:
        print(f"\n❌ [FAILED] An error occurred:")
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="PinSeeker Local Test Harness — test scraper logic without Firestore",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python replicate_playwright.py --list
  python replicate_playwright.py --course "orchard creek" --date 2026-07-25
  python replicate_playwright.py --course "fairways" --date 2026-07-25 --headless false --live
        """
    )
    parser.add_argument('--list', action='store_true', help='List all available courses')
    parser.add_argument('--course', type=str, help='Course name (e.g., "orchard creek", "fairways")')
    parser.add_argument('--date', type=str, help='Target play date (YYYY-MM-DD). Defaults to tomorrow.')
    parser.add_argument('--earliest', type=str, default='07:00', help='Earliest tee time (HH:MM). Default: 07:00')
    parser.add_argument('--latest', type=str, default='20:00', help='Latest tee time (HH:MM). Default: 20:00')
    parser.add_argument('--players', type=int, default=4, help='Number of players. Default: 4')
    parser.add_argument('--live', action='store_true', help='Actually attempt the booking (disables dry run)')
    parser.add_argument('--headless', type=str, default='true', help='Run browser headless (true/false). Default: true')
    parser.add_argument('--email', type=str, help='Course login email (overrides .env COURSE_EMAIL)')
    parser.add_argument('--password', type=str, help='Course login password (overrides .env COURSE_PASSWORD)')

    args = parser.parse_args()

    # List mode
    if args.list:
        print("\nAvailable courses:")
        for name in list_courses():
            print(f"  • {name}")
        print()
        return

    # Validate required args
    if not args.course:
        parser.error("--course is required (or use --list to see available courses)")

    # Parse date
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today() + timedelta(days=1)
        print(f"No --date specified. Defaulting to tomorrow: {target_date}")

    # Parse headless
    headless = args.headless.lower() in ('true', '1', 'yes')

    # Resolve credentials: CLI args > .env > error
    email = args.email or os.getenv('COURSE_EMAIL', '')
    password = args.password or os.getenv('COURSE_PASSWORD', '')

    if not email or not password:
        print("\n⚠️  No credentials provided.")
        print("   Set COURSE_EMAIL and COURSE_PASSWORD in backend/.env,")
        print("   or pass --email and --password on the command line.")
        sys.exit(1)

    dry_run = not args.live

    run_replication(
        course_name=args.course,
        target_date=target_date,
        earliest=args.earliest,
        latest=args.latest,
        players=args.players,
        dry_run=dry_run,
        headless=headless,
        email=email,
        password=password,
    )


if __name__ == "__main__":
    main()
