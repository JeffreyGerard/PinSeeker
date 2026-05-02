import os
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from bookings.models import GolfCourse, BookingRequest, UserCredential
from utils import decrypt_password
from playwright_logic import (
    book_via_foreup_software, 
    book_via_foreup_new, 
    book_cps_golf,
    book_cps_old_post,
    book_frear_park,
    book_schenectady_muni,
    book_via_eagleclub
)

class Command(BaseCommand):
    help = 'Verifies playwright scripts for all configured golf courses using a dry run'

    def handle(self, *args, **kwargs):
        courses = GolfCourse.objects.all()
        if not courses:
            self.stdout.write(self.style.WARNING("No golf courses found in the database."))
            return

        # Target a date 2 days from today
        target_date = date.today() + timedelta(days=2)

        success_count = 0
        failure_count = 0

        self.stdout.write(self.style.NOTICE(f"Starting verification for {courses.count()} courses..."))
        self.stdout.write(self.style.NOTICE(f"Using test date: {target_date}"))
        self.stdout.write("=" * 50)

        for course in courses:
            self.stdout.write(f"\nTesting Course: {course.name} ({course.logic_type})")
            cred = UserCredential.objects.filter(course=course).first()
            if not cred:
                self.stdout.write(self.style.WARNING(f"  -> SKIPPED: No user credentials found for this course."))
                continue

            # Create a mock booking request (not saved to DB)
            booking = BookingRequest(
                course=course,
                desired_date=target_date,
                earliest_time=time(14, 0),  # 2:00 PM
                latest_time=time(16, 0),    # 4:00 PM
                players=2
            )

            try:
                password = decrypt_password(cred.encrypted_password)
                result = ""
                
                if course.logic_type == 'foreup':
                    result = book_via_foreup_software(course.url, course.public_btn_xpath, booking, cred.course_email, password, dry_run=True)
                elif course.logic_type == 'foreup_new':
                    result = book_via_foreup_new(course.url, course.public_btn_xpath, booking, cred.course_email, password, dry_run=True)
                elif course.logic_type == 'cps':
                    result = book_cps_golf(course.url, booking, cred.course_email, password, dry_run=True)
                elif course.logic_type == 'cps_old_post':
                    result = book_cps_old_post(course.url, booking, cred.course_email, password, dry_run=True)
                elif course.logic_type == 'frear':
                    result = book_frear_park(course.url, booking, cred.course_email, password, dry_run=True)
                elif course.logic_type == 'schenectady':
                    result = book_schenectady_muni(course.url, course.public_btn_xpath, booking, cred.course_email, password, dry_run=True)
                elif course.logic_type == 'eagleclub':
                    result = book_via_eagleclub(course.url, booking, cred.course_email, password, dry_run=True)
                else:
                    self.stdout.write(self.style.WARNING(f"  -> SKIPPED: Unknown logic type '{course.logic_type}'."))
                    continue

                self.stdout.write(self.style.SUCCESS(f"  -> SUCCESS: {result}"))
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> FAILED: {str(e)}"))
                failure_count += 1

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.NOTICE("Verification Summary:"))
        self.stdout.write(self.style.SUCCESS(f"  Successful: {success_count}"))
        if failure_count > 0:
            self.stdout.write(self.style.ERROR(f"  Failed:     {failure_count}"))
        else:
            self.stdout.write(self.style.NOTICE(f"  Failed:     {failure_count}"))
