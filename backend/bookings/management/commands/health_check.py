from django.core.management.base import BaseCommand
from bookings.models import GolfCourse, BookingRequest, UserCredential
from bookings.playwright_logic import (
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
from bookings.utils import decrypt_password
from datetime import date, time, timedelta

class Command(BaseCommand):
    help = "Run a dry-run health check across all courses for a specific 2-hour window."

    def handle(self, *args, **kwargs):
        courses = GolfCourse.objects.all()
        self.stdout.write(f"Starting health check for {courses.count()} courses...")

        # Safe verification window: 4-22-26 at 2:00 PM
        target_date = date(2026, 4, 22)
        
        dummy_booking = BookingRequest(
            course=None,
            desired_date=target_date,
            earliest_time=time(14, 0), # 2:00 PM
            latest_time=time(18, 0),  # Broad window for health check
            players=4
        )

        for course in courses:
            self.stdout.write(f"Checking {course.name} ({course.logic_type})...")
            try:
                cred = UserCredential.objects.filter(course=course).first()
                email = cred.course_email if cred else "test@example.com"
                password = decrypt_password(cred.encrypted_password) if cred else "test"

                url = course.url
                logic = course.logic_type
                
                # We do not use the xpath from the DB anymore in the new unified flow.
                result = ""
                if logic == 'foreup':
                    if "Orchard" in course.name:
                        result = book_orchard_creek(url, dummy_booking, email, password, dry_run=True)
                    elif "Van Patten" in course.name:
                        result = book_van_patten(url, dummy_booking, email, password, dry_run=True)
                    else:
                        result = book_via_foreup_software(url, dummy_booking, email, password, dry_run=True)
                elif logic == 'foreup_new':
                    if "Stadium" in course.name:
                        result = book_stadium(url, dummy_booking, email, password, dry_run=True)
                    elif "Fairways" in course.name:
                        result = book_fairways_halfmoon(url, dummy_booking, email, password, dry_run=True)
                    else:
                        result = book_via_foreup_software(url, dummy_booking, email, password, dry_run=True)
                elif logic == 'cps':
                    result = book_cps_golf(url, dummy_booking, email, password, dry_run=True)
                elif logic == 'cps_old_post':
                    result = book_cps_old_post(url, dummy_booking, email, password, dry_run=True)
                elif logic == 'schenectady':
                    result = book_schenectady_muni(url, dummy_booking, email, password, dry_run=True)
                elif logic == 'eagleclub':
                    result = book_via_eagleclub(url, dummy_booking, email, password, dry_run=True)
                # Note: Frear Park was skipped in the AntiGravity mandate as requested.
                elif logic == 'frear':
                     self.stdout.write(self.style.WARNING(f"  {course.name} skipped (Frear Park logic omitted in recent update)."))
                     continue
                else:
                    result = f"Unknown logic type: {logic}"

                self.stdout.write(self.style.SUCCESS(f"  {course.name}: {result}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  {course.name} FAILED: {str(e)}"))
