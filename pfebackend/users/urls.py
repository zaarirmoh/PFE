from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentListView, TeacherListView

urlpatterns = [
    path('students/', StudentListView.as_view(), name='student-list'),
    path('teachers/', TeacherListView.as_view(), name='teacher-list'),

]