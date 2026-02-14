
from rest_framework import serializers
from .models import BookingRequest, GolfCourse, UserCredential

class GolfCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfCourse
        fields = ['id', 'name', 'url']

class BookingRequestSerializer(serializers.ModelSerializer):
    course_name = serializers.ReadOnlyField(source='course.name')
    
    class Meta:
        model = BookingRequest
        fields = '__all__'
        read_only_fields = ['user', 'status', 'result_log', 'created_at']
