from rest_framework import permissions, status
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
)
from rest_framework.response import Response

from teams.models import Team
from teams.serializers import TeamSerializer
from teams.permissions import IsTeamMember, IsTeamOwner
from teams.services import TeamService
from notifications.services import NotificationService
from common.pagination import StaticPagination
from users.permissions import IsStudent

class TeamListCreateView(ListCreateAPIView):
    """
    Create a new team or list teams
    
    GET /api/teams/ - List teams the current user is a member of
    POST /api/teams/ - Create a new team (automatically makes creator the owner)
    """
    serializer_class = TeamSerializer
    pagination_class = StaticPagination
    queryset = Team.objects.all()
    
    def get_permissions(self):
        """
        Apply IsStudent permission only for POST requests.
        """
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]
    
    # def get_queryset(self):
    #     """Return teams the current user is a member of"""
    #     return TeamService.get_user_teams(self.request.user)
    
    def perform_create(self, serializer):
        """Create a new team with the current user as owner"""
        # Use TeamService to create the team
        team = TeamService.create_team(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            owner=self.request.user
        )
        
        # Set serializer instance for proper response
        serializer.instance = team
        
        # Send notification to owner using NotificationService
        NotificationService.create_and_send(
            recipient=self.request.user,
            title="Team Created",
            content=f"You created the team '{team.name}'",
            notification_type='team_update',
            related_object=team,
            priority='low',
            metadata={
                'team_id': team.id,
                'event_type': 'team_created'
            }
        )


class TeamDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a team
    
    GET /api/teams/{id}/ - View team details (members only)
    PUT/PATCH /api/teams/{id}/ - Update team (owners only)
    DELETE /api/teams/{id}/ - Delete team (owners only)
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    lookup_field = 'id'

    def get_permissions(self):
        """Use different permission classes based on the request method"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsTeamOwner()]
        return super().get_permissions()

    def perform_update(self, serializer):
        """Update team and create notification if name changed"""
        team = self.get_object()
        old_name = team.name
        updated_team = serializer.save(updated_by=self.request.user)
        
        # Only send notification if the team name has changed
        if old_name != updated_team.name:
            NotificationService.create_and_send(
                recipient=self.request.user,
                title="Team Updated",
                content=f"Team name changed from '{old_name}' to '{updated_team.name}'",
                notification_type='team_update',
                related_object=updated_team,
                priority='medium',
                metadata={
                    'team_id': updated_team.id,
                    'old_name': old_name,
                    'new_name': updated_team.name,
                    'event_type': 'team_renamed'
                }
            )

    def perform_destroy(self, instance):
        """Delete team and create notification"""
        team_name = instance.name
        team_id = instance.id
        instance.delete()
        
        # Send notification about team deletion
        NotificationService.create_and_send(
            recipient=self.request.user,
            title="Team Deleted",
            content=f"Team '{team_name}' was deleted",
            notification_type='team_update',
            priority='medium',
            metadata={
                'team_name': team_name,
                'event_type': 'team_deleted'
            }
        )
