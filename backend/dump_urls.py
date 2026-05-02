import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinseeker.settings')
django.setup()

from bookings.models import GolfCourse

with open("urls.txt", "w") as f:
    for c in GolfCourse.objects.all():
        f.write(f"{c.logic_type}|{c.name}|{c.url}\n")
