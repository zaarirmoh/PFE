# api/views/team_invitations.py
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import get_user_model
from teams.models import Team, TeamInvitation, TeamMembership
from notifications.services import send_team_invitation
from .serializers import TeamInvitationSerializer
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from teams.models import Team, TeamMembership
from notifications.services import create_notification
from .serializers import TeamSerializer

User = get_user_model()

class TeamInvitationCreateView(CreateAPIView):
    """
    API endpoint for creating team invitations
    Required POST data:
    - team_id: ID of the team to invite to
    - invitee_username: Username of the user to invite
    """
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        team = serializer.validated_data['team']
        invitee = serializer.validated_data['invitee']
        inviter = self.request.user

        # Check if inviter is part of the team
        if not TeamMembership.objects.filter(team=team, user=inviter).exists():
            raise PermissionDenied("You must be a member of the team to invite others")

        # Check if invitee is already a member
        if TeamMembership.objects.filter(team=team, user=invitee).exists():
            raise ValidationError("This user is already a team member")

        # Check for existing pending invitation
        if TeamInvitation.objects.filter(
            team=team, 
            invitee=invitee, 
            status='pending'
        ).exists():
            raise ValidationError("A pending invitation already exists for this user")

        # Create invitation using service
        invitation = send_team_invitation(
            team=team,
            inviter=inviter,
            invitee=invitee
        )

        serializer.instance = invitation

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except (ValidationError, PermissionDenied) as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError) 
                else status.HTTP_403_FORBIDDEN
            )
            
class TeamCreateView(CreateAPIView):
    """
    Create a new team (automatically makes creator the owner)
    POST /api/teams/
    Required fields: name, description(optional)
    """
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        team = serializer.save()
        team.members.add(self.request.user)

        # Create owner membership
        TeamMembership.objects.create(
            user=self.request.user,
            team=team,
            role='owner'
        )
        
        # Send notification to owner
        create_notification(
            recipient=self.request.user,
            content=f"You created the team '{team.name}'",
            notification_type='activity',
            related_object=team,
            priority='low'
        )

class TeamDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a team (only for owners)
    GET /api/teams/{id}/
    PUT /api/teams/{id}/
    DELETE /api/teams/{id}/
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [permissions.IsAuthenticated(), IsTeamOwner()]
        return super().get_permissions()

    def perform_update(self, serializer):
        team = self.get_object()
        old_name = team.name
        updated_team = serializer.save()
        
        if old_name != updated_team.name:
            create_notification(
                recipient=updated_team.owner,
                content=f"Team name changed from '{old_name}' to '{updated_team.name}'",
                notification_type='system',
                related_object=updated_team,
                priority='medium'
            )

    def perform_destroy(self, instance):
        # Archive instead of delete if you want to preserve data
        instance.delete()
        create_notification(
            recipient=self.request.user,
            content=f"Team '{instance.name}' was deleted",
            notification_type='system',
            priority='high'
        )

# Permissions.py
class IsTeamOwner(permissions.BasePermission):
    """
    Custom permission to only allow team owners to modify
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user