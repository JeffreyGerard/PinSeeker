
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingRequestViewSet, GolfCourseViewSet

router = DefaultRouter()
router.register(r'requests', BookingRequestViewSet, basename='bookingrequest')
router.register(r'courses', GolfCourseViewSet, basename='golfcourse')

urlpatterns = [
    path('', include(router.urls)),
]
