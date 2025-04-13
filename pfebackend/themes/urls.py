from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.theme_creation_viewsets import ThemeViewSet
from .views.theme_assignment_viewsets import ThemeChoiceViewSet, ThemeAssignmentViewSet

router = DefaultRouter()
router.register(r'themes', ThemeViewSet, basename="theme")
router.register(r'choices', ThemeChoiceViewSet, basename="theme-choice")
router.register(r'assignments', ThemeAssignmentViewSet, basename="theme-assignment")
urlpatterns = [
    path('', include(router.urls)),
]