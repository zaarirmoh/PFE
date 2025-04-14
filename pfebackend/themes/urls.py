from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.theme_creation_viewsets import ThemeViewSet
from .views.theme_assignment_viewsets import ThemeChoiceViewSet, ThemeAssignmentViewSet
from .views.theme_supervision_views import (
    TeamSupervisionRequestListView,
    UserSupervisionRequestListView,
    CreateSupervisionRequestView,
    CancelSupervisionRequestView,
    SupervisionRequestResponseView,
)


router = DefaultRouter()
router.register(r'themes', ThemeViewSet, basename="theme")
# router.register(r'choices', ThemeChoiceViewSet, basename="theme-choice")
# router.register(r'assignments', ThemeAssignmentViewSet, basename="theme-assignment")
urlpatterns = [
    path('', include(router.urls)),
    path('teams/<int:team_id>/supervision-requests/', 
         TeamSupervisionRequestListView.as_view(), 
         name='team-supervision-requests'),
    
    # User supervision requests (as supervisor)
     path('supervision-requests/', 
         UserSupervisionRequestListView.as_view(), 
         name='user-supervision-requests'),
    
    # Create supervision request
    path('supervision-requests/create/', 
         CreateSupervisionRequestView.as_view(), 
         name='create-supervision-request'),
    
    path('supervision-requests/<int:id>/', 
         SupervisionRequestResponseView.as_view(), 
         name='supervision-request-response'),

    
    # Cancel supervision request
    path('supervision-requests/<int:request_id>/cancel/', 
         CancelSupervisionRequestView.as_view(), 
         name='cancel-supervision-request'),

]