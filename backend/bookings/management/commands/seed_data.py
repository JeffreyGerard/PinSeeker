from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bookings.models import GolfCourse, UserCredential
from bookings.utils import encrypt_password

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

        # 3. Create Golf Courses
        courses_data = [
            {
                'name': 'Capital Hills',
                'url': 'https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23',
                'logic_type': 'cps',
                'public_btn_xpath': '' # Not used for CPS
            },
            {
                'name': 'Eagle Crest',
                'url': 'https://foreupsoftware.com/index.php/booking/21756#/teetimes',
                'logic_type': 'foreup_new',
                'public_btn_xpath': '//*[@id="content"]/div/button[1]'
            },
            {
                'name': 'Fairways of Halfmoon',
                'url': 'https://foreupsoftware.com/index.php/booking/21756#/teetimes',
                'logic_type': 'foreup_new',
                'public_btn_xpath': '//*[@id="content"]/div/button'
            },
            {
                'name': 'Frear Park Municipal Golf Course',
                'url': 'https://secure.east.prophetservices.com/FrearParkV3/(S(13kebkre22enx3l3kh5xqh2p))/Home/nIndex?CourseId=1,2&Date=2024-6-28&Time=AnyTime&Player=4&Hole=18',
                'logic_type': 'frear',
                'public_btn_xpath': '' # Custom logic
            },
            {
                'name': 'Orchard Creek',
                'url': 'https://foreupsoftware.com/index.php/booking/19530/1791#teetimes',
                'logic_type': 'foreup',
                'public_btn_xpath': '//*[@id="content"]/div/button[5]'
            },
            {
                'name': 'Old Post',
                'url': 'https://oldepostroad.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23',
                'logic_type': 'cps_old_post',
                'public_btn_xpath': '' # Not used for CPS
            },
            {
                'name': 'Schenectady Muni Golf Course',
                'url': 'https://foreupsoftware.com/index.php/booking/20480/4739#/teetimes',
                'logic_type': 'schenectady',
                'public_btn_xpath': '//*[@id="content"]/div/button[1]'
            },
            {
                'name': 'Stadium Golf Course',
                'url': 'https://foreupsoftware.com/index.php/booking/index/3332#/teetimes',
                'logic_type': 'foreup_new',
                'public_btn_xpath': '//*[@id="content"]/div/button[1]'
            },
            {
                'name': 'Van Patten Golf Course',
                'url': 'https://foreupsoftware.com/index.php/booking/index/19324#/teetimes',
                'logic_type': 'foreup',
                'public_btn_xpath': '//*[@id="content"]/div/button[1]'
            }
        ]

        for course_data in courses_data:
            course, created = GolfCourse.objects.get_or_create(
                name=course_data['name'],
                defaults={
                    'url': course_data['url'],
                    'logic_type': course_data['logic_type'],
                    'public_btn_xpath': course_data['public_btn_xpath']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Course: {course.name}'))
            else:
                course.url = course_data['url']
                course.logic_type = course_data['logic_type']
                course.public_btn_xpath = course_data['public_btn_xpath']
                course.save()

            # Determine real credentials from Golf_API.py
            email = "jeff.gerard05@gmail.com"
            password = "Password101"
            
            if course.logic_type == 'schenectady':
                email = "frugalderek@gmail.com"
            elif course.logic_type == 'cps_old_post':
                password = "Password101$"

            # Create/Update credentials for the test user
            cred, cred_created = UserCredential.objects.get_or_create(
                user=test_user,
                course=course,
                defaults={
                    'course_email': email,
                    'encrypted_password': encrypt_password(password)
                }
            )
            if not cred_created:
                cred.course_email = email
                cred.encrypted_password = encrypt_password(password)
                cred.save()

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS('SEEDING COMPLETE'))
        self.stdout.write(self.style.SUCCESS('Admin Login: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('User Login:  golfer / golf123'))
        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
