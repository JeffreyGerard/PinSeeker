
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import BookingRequest, GolfCourse, UserCredential
from .serializers import BookingRequestSerializer, GolfCourseSerializer
from .tasks import execute_booking

class GolfCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows courses to be viewed.
    """
    queryset = GolfCourse.objects.all()
    serializer_class = GolfCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

class BookingRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and listing booking requests.
    """
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users only see their own requests
        return BookingRequest.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # 1. Save to DB
        booking = serializer.save(user=self.request.user)
        
        # 2. Schedule Task immediately
        # Note: In a real app, you might validate that credentials exist before scheduling
        execute_booking.apply_async(
            args=[booking.id],
            eta=booking.execution_time
        )
