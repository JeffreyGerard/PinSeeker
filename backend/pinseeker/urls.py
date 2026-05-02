
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "message": "Welcome to PinSeeker API",
        "status": "running",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/"
        }
    })

urlpatterns = [
    path('', api_root),
    path('admin/', admin.site.urls),
    path('api/', include('bookings.urls')), # Connects the API
]
