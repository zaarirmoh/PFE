from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import StudentListView, TeacherListView, ProfilePictureUpdateView

urlpatterns = [
    
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
    
    
    path('students/', StudentListView.as_view(), name='student-list'),
    path('teachers/', TeacherListView.as_view(), name='teacher-list'),
    
    path('auth/reset-profile-picture/', ProfilePictureUpdateView.as_view(), name='profile-picture-update'),
]