
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bookings.models import GolfCourse, UserCredential, BookingRequest
from bookings.utils import encrypt_password
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Seeds the database with initial users and golf course data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Seeding data...'))

        # 1. Create Superuser (Admin)
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com'}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created Admin: {admin_user.username} (Pass: admin123)'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin already exists: {admin_user.username}'))

        # 2. Create Regular Test User
        test_user, created = User.objects.get_or_create(
            username='golfer',
            defaults={'email': 'golfer@example.com'}
        )
        if created:
            test_user.set_password('golf123')
            test_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created User: {test_user.username} (Pass: golf123)'))
        else:
            self.stdout.write(self.style.WARNING(f'User already exists: {test_user.username}'))

        # 3. Create Sample Golf Course
        course, created = GolfCourse.objects.get_or_create(
            name='Cypress Point (Demo)',
            defaults={
                'url': 'https://foreupsoftware.com/index.php/booking/19777/2431',
                'logic_type': 'foreup',
                'public_btn_xpath': '//*[@id="wh-global-menu"]/div/div/div/div/div/a'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Course: {course.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Course already exists: {course.name}'))

        # 4. Create Credentials for the Test User
        # We need this so the bot knows what to "login" with when running automation
        cred, created = UserCredential.objects.get_or_create(
            user=test_user,
            course=course,
            defaults={
                'course_email': 'demo@example.com',
                'encrypted_password': encrypt_password('securepassword')
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Credentials for {test_user.username} at {course.name}'))

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS('SEEDING COMPLETE'))
        self.stdout.write(self.style.SUCCESS('Admin Login: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('User Login:  golfer / golf123'))
        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
