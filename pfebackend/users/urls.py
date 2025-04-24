from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    StudentListView,
    TeacherListView,
    ProfilePictureUpdateView,
    ExternalUserListView,
    ProfileListView,
    UserProfileRetrieveView,
    StudentSkillCreateView,
    )

urlpatterns = [
    
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
    
    
    path('students/', StudentListView.as_view(), name='student-list'),
    path('students/<int:id>/skills/', StudentSkillCreateView.as_view(), name='student-skill-create'),
    path('teachers/', TeacherListView.as_view(), name='teacher-list'),
    path('external-users/', ExternalUserListView.as_view(), name='external-user-list'),
    
    path('auth/reset-profile-picture/', ProfilePictureUpdateView.as_view(), name='profile-picture-update'),
    
    path('profiles/', ProfileListView.as_view(), name='profile-list'),
    path('profiles/<int:id>/', UserProfileRetrieveView.as_view(), name='user-profile'),
    
    
]