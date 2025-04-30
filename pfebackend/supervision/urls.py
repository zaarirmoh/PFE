# meetings/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeetingViewSet,UploadViewSet, ProjectListView

router = DefaultRouter()
router.register(r'meetings', MeetingViewSet, basename='meeting')
# router.register(r'meeting-attendances', MeetingAttendanceViewSet, basename='meeting-attendance')
router.register(r'uploads', UploadViewSet, basename='upload')


urlpatterns = [
    path('', include(router.urls)),
    path('projects/', ProjectListView.as_view(), name='project-list'),
]


