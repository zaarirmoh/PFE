from django.urls import path
from .views import TeamInvitationCreateView, TeamCreateView, TeamDetailView

urlpatterns = [
    path('invitations/', TeamInvitationCreateView.as_view(), name='team-invitations-create'),
    path('teams/', TeamCreateView.as_view(), name='team-create'),
    path('teams/<int:id>/', TeamDetailView.as_view(), name='team-detail'),
]
