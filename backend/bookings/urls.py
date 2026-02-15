
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingRequestViewSet, GolfCourseViewSet, UserMeViewSet, UserCredentialViewSet

router = DefaultRouter()
router.register(r'requests', BookingRequestViewSet, basename='bookingrequest')
router.register(r'courses', GolfCourseViewSet, basename='golfcourse')
router.register(r'credentials', UserCredentialViewSet, basename='usercredential')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserMeViewSet.as_view({
        'get': 'retrieve_me',
        'post': 'change_password'
    }), name='user-me'),
]
