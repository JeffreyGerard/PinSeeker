from django.contrib.auth.models import User
from bookings.models import BookingRequest

print("All Orchard Bookings:")
for b in BookingRequest.objects.filter(course__name__icontains='Orchard').order_by('-created_at')[:10]:
    print(f' - ID: {b.id}, Status: {b.status}, execution_time: {b.execution_time}, created: {b.created_at}')

print("All Pending Bookings:")
for b in BookingRequest.objects.filter(status__iexact='pending'):
    print(f' - ID: {b.id}, Course: {b.course.name}, Status: {b.status}')
