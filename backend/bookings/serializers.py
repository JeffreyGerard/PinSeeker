
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BookingRequest, GolfCourse, UserCredential

class UserSerializer(serializers.ModelSerializer):
    force_password_change = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'force_password_change']

    def get_force_password_change(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.force_password_change
        return False

class GolfCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfCourse
        fields = ['id', 'name', 'url']

class UserCredentialSerializer(serializers.ModelSerializer):
    course_name = serializers.ReadOnlyField(source='course.name')
    # Write-only password field for input
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserCredential
        fields = ['id', 'course', 'course_name', 'course_email', 'password']
        read_only_fields = ['id', 'course_name']

class BookingRequestSerializer(serializers.ModelSerializer):
    course_name = serializers.ReadOnlyField(source='course.name')
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = BookingRequest
        fields = '__all__'
        read_only_fields = ['user', 'status', 'result_log', 'created_at']
