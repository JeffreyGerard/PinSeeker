import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinseeker.settings')
django.setup()

from bookings.models import BookingRequest
from bookings.playwright_logic import book_orchard_creek

# Get the booking
booking = BookingRequest.objects.get(id=13)

# Run booking
try:
    print(f"Running {booking.course.name} booking...")
    email = 'jeff.gerard05@gmail.com'
    password = 'Password101'
    result = book_orchard_creek(booking.course.url, booking, email, password, dry_run=False)
    print(f"Result: {result}")
except Exception as e:
    print(f"Failed: {e}")
