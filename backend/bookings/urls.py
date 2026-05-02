from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingRequestViewSet, GolfCourseViewSet, UserMeViewSet, UserCredentialViewSet, JobWebhookView

router = DefaultRouter()
router.register(r'requests', BookingRequestViewSet, basename='bookingrequest')
router.register(r'courses', GolfCourseViewSet, basename='golfcourse')
router.register(r'credentials', UserCredentialViewSet, basename='usercredential')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserMeViewSet.as_view({
        'get': 'retrieve_me'
    }), name='user-me'),
    path('me/change_password/', UserMeViewSet.as_view({
        'post': 'change_password'
    }), name='user-me-change-password'),
    path('webhook/job-completion/', JobWebhookView.as_view(), name='job-webhook'),
]
