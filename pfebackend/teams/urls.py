from django.urls import path
from .views import *


app_name = 'teams'


urlpatterns = [
    # Team endpoints
    path('teams/', TeamListCreateView.as_view(), name='team-list-create'),
    path('teams/<int:id>/', TeamDetailView.as_view(), name='team-detail'),
    
    # Team invitation endpoints
    path('invitations/', InvitationListView.as_view(), name='invitation-list'),
    path('invitations/create/', TeamInvitationCreateView.as_view(), name='invitation-create'),
    path('invitations/<int:id>/', InvitationResponseView.as_view(), name='invitation-response'),
    
    # Team membership endpoints
    path('teams/<int:team_id>/members/', TeamMembershipListView.as_view(), name='team-members-list'),
    path('teams/<int:team_id>/members/add/', TeamMembershipCreateView.as_view(), name='team-members-add'),
    path('teams/<int:team_id>/members/<int:id>/', TeamMembershipDetailView.as_view(), name='team-member-detail'),
    
    # Join request routes
    path('join-requests/', UserJoinRequestListView.as_view(), name='join_request_list'),
    path('join-requests/create/', JoinRequestCreateView.as_view(), name='join_request_create'),
    path('join-requests/<int:id>/', JoinRequestDetailView.as_view(), name='join_request_detail'),
    path('join-requests/<int:id>/cancel/', JoinRequestCancelView.as_view(), name='join_request_cancel'),
    path('teams/<int:team_id>/join-requests/', TeamJoinRequestListView.as_view(), name='team_join_request_list'),
]
