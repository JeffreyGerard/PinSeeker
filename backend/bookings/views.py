from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .models import BookingRequest, GolfCourse, UserCredential
from .serializers import BookingRequestSerializer, GolfCourseSerializer, UserSerializer, UserCredentialSerializer
from .job_trigger import trigger_booking_job
import os
import logging

logger = logging.getLogger(__name__)

class JobWebhookView(APIView):
    """
    Webhook endpoint for Cloud Run Jobs to report completion.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        secret = request.headers.get('X-Webhook-Secret')
        expected_secret = os.getenv('WEBHOOK_SECRET')
        
        if not secret or secret != expected_secret:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        booking_id = request.data.get('booking_id')
        job_status = request.data.get('status')
        result_log = request.data.get('result_log')

        try:
            booking = BookingRequest.objects.get(id=booking_id)
            booking.status = job_status
            booking.result_log = result_log
            booking.save()
            logger.info(f"Updated booking {booking_id} via webhook. Status: {job_status}")
            return Response({"status": "updated"}, status=status.HTTP_200_OK)
        except BookingRequest.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

class UserMeViewSet(viewsets.ViewSet):
    """
    API endpoint to retrieve the current user's details.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def retrieve_me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        new_password = request.data.get('new_password')
        
        if not new_password or len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        # Update profile flag
        if hasattr(user, 'profile'):
            user.profile.force_password_change = False
            user.profile.save()
            
        return Response({'status': 'Password updated successfully'})

class GolfCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows courses to be viewed.
    """
    queryset = GolfCourse.objects.all().order_by('name')
    serializer_class = GolfCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserCredentialViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to manage their OWN course credentials.
    """
    serializer_class = UserCredentialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserCredential.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        password = serializer.validated_data.pop('password', None)
        if not password:
             from rest_framework import serializers
             raise serializers.ValidationError({"password": "Password is required."})

        from .utils import encrypt_password
        encrypted = encrypt_password(password)
        serializer.save(user=self.request.user, encrypted_password=encrypted)

    def perform_update(self, serializer):
        password = serializer.validated_data.pop('password', None)
        if password:
            from utils import encrypt_password
            encrypted = encrypt_password(password)
            serializer.save(encrypted_password=encrypted)
        else:
            serializer.save()

class BookingRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and listing booking requests.
    """
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BookingRequest.objects.all().order_by('-created_at')
        return BookingRequest.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        # 1. Save to DB
        booking = serializer.save(user=self.request.user)
        
        # 2. Trigger Cloud Run Job immediately
        # Note: In a production environment with execution_time in the future, 
        # you would create a Cloud Scheduler job here. 
        # For this refactor, we trigger the Job immediately.
        trigger_booking_job(booking)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Manually trigger the Cloud Run Job for an existing booking."""
        booking = self.get_object()
        success = trigger_booking_job(booking)
        if success:
            return Response({'status': 'Job triggered'})
        return Response({'status': 'Failed to trigger job'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Set a PENDING booking's status to CANCELLED."""
        booking = self.get_object()
        if booking.status != 'PENDING':
            return Response(
                {'error': f'Cannot cancel a booking with status {booking.status}. Only PENDING bookings can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = 'CANCELLED'
        booking.result_log = 'Cancelled by user.'
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear_history(self, request):
        """Delete all SUCCESS, FAILED, and CANCELLED bookings for the authenticated user."""
        qs = BookingRequest.objects.filter(
            user=request.user,
            status__in=['SUCCESS', 'FAILED', 'CANCELLED']
        )
        count = qs.count()
        qs.delete()
        return Response({'deleted': count, 'message': f'Cleared {count} history records.'})
