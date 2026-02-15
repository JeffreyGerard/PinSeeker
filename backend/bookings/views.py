
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import BookingRequest, GolfCourse, UserCredential
from .serializers import BookingRequestSerializer, GolfCourseSerializer, UserSerializer, UserCredentialSerializer
from .tasks import execute_booking

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
    queryset = GolfCourse.objects.all()
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
        # Handle password encryption manually
        password = serializer.validated_data.pop('password', None)
        instance = serializer.save(user=self.request.user)
        if password:
            instance.set_password(password)
            instance.save()

    def perform_update(self, serializer):
        password = serializer.validated_data.pop('password', None)
        instance = serializer.save()
        if password:
            instance.set_password(password)
            instance.save()

class BookingRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and listing booking requests.
    """
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # If user is Admin (is_staff), return ALL bookings.
        if user.is_staff:
            return BookingRequest.objects.all().order_by('-created_at')
        # Otherwise, return only THEIR bookings.
        return BookingRequest.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        # 1. Save to DB
        booking = serializer.save(user=self.request.user)
        
        # 2. Schedule Task immediately
        execute_booking.apply_async(
            args=[booking.id],
            eta=booking.execution_time
        )
