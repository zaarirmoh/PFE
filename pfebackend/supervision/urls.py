# meetings/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeetingViewSet

router = DefaultRouter()
router.register(r'meetings', MeetingViewSet, basename='meeting')
# router.register(r'meeting-attendances', MeetingAttendanceViewSet, basename='meeting-attendance')

urlpatterns = [
    path('', include(router.urls)),
]