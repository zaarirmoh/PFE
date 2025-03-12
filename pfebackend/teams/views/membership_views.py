from rest_framework import permissions, status
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView
)
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from teams.models import Team, TeamMembership
from teams.serializers import TeamMembershipSerializer
from teams.permissions import IsTeamMember, IsTeamOwner
from notifications.services import NotificationService
from teams.services import TeamService


class TeamMembershipListView(ListAPIView):
    """
    List members of a team
    
    GET /api/teams/{team_id}/members/
    """
    serializer_class = TeamMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    
    def get_queryset(self):
        """Return memberships for the specified team"""
        team_id = self.kwargs.get('team_id')
        try:
            team = Team.objects.get(id=team_id)
            self.check_object_permissions(self.request, team)
            # Use TeamService to get team members
            return TeamService.get_team_members(team)
        except Team.DoesNotExist:
            return TeamMembership.objects.none()


class TeamMembershipCreateView(CreateAPIView):
    """
    Add a member to a team (owners only)
    
    POST /api/teams/{team_id}/members/
    Required data:
    - username: Username of user to add
    - role: Role to assign (default: 'member')
    """
    serializer_class = TeamMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamOwner]
    
    def get_serializer_context(self):
        """Add additional context to serializer"""
        context = super().get_serializer_context()
        context['team_id'] = self.kwargs.get('team_id')
        return context
        
    def perform_create(self, serializer):
        """Add user to team"""
        team_id = self.kwargs.get('team_id')
        try:
            team = Team.objects.get(id=team_id)
            self.check_object_permissions(self.request, team)
            
            # Create membership
            membership = serializer.save(team=team)
            
            # Notify new member using NotificationService
            NotificationService.create_and_send(
                recipient=membership.user,
                title="Team Membership",
                content=f"You were added to team '{team.name}' by {self.request.user.get_full_name() or self.request.user.username}",
                notification_type='team_membership',
                related_object=team,
                priority='medium',
                action_url=f"/teams/{team.id}/",
                metadata={
                    'team_id': team.id,
                    'team_name': team.name,
                    'role': membership.role,
                    'event_type': 'added_to_team'
                }
            )
            
        except Team.DoesNotExist:
            raise PermissionDenied("Team does not exist")


class TeamMembershipDetailView(RetrieveUpdateDestroyAPIView):
    """
    Manage a team membership (owners only)
    
    GET /api/teams/{team_id}/members/{id}/
    PATCH /api/teams/{team_id}/members/{id}/ - Update role
    DELETE /api/teams/{team_id}/members/{id}/ - Remove member
    """
    serializer_class = TeamMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamOwner]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Return memberships for the specified team"""
        team_id = self.kwargs.get('team_id')
        return TeamMembership.objects.filter(team_id=team_id)
        
    def perform_update(self, serializer):
        """Update membership and notify user"""
        membership = self.get_object()
        old_role = membership.get_role_display()
        updated = serializer.save()
        
        # Only notify if role has changed
        if old_role != updated.get_role_display():
            NotificationService.create_and_send(
                recipient=updated.user,
                title="Role Changed",
                content=f"Your role in team '{updated.team.name}' was changed to {updated.get_role_display()}",
                notification_type='team_membership',
                related_object=updated.team,
                priority='medium',
                metadata={
                    'team_id': updated.team.id,
                    'team_name': updated.team.name,
                    'old_role': old_role,
                    'new_role': updated.get_role_display(),
                    'event_type': 'role_changed'
                }
            )
    
    def perform_destroy(self, instance):
        """Remove member from team and notify them"""
        team = instance.team
        user = instance.user
        
        # Prevent removing the last owner
        if instance.role == TeamMembership.ROLE_OWNER:
            owner_count = TeamMembership.objects.filter(
                team=team, 
                role=TeamMembership.ROLE_OWNER
            ).count()
            
            if owner_count <= 1:
                raise PermissionDenied("Cannot remove the last owner of the team")
        
        # Delete membership
        instance.delete()
        
        # Notify removed member using NotificationService
        NotificationService.create_and_send(
            recipient=user,
            title="Removed from Team",
            content=f"You were removed from team '{team.name}' by {self.request.user.get_full_name() or self.request.user.username}",
            notification_type='team_membership',
            related_object=team,
            priority='medium',
            metadata={
                'team_id': team.id,
                'team_name': team.name,
                'event_type': 'removed_from_team'
            }
        )





# from rest_framework import permissions, status
# from rest_framework.generics import (
#     ListAPIView,
#     RetrieveUpdateDestroyAPIView,
#     CreateAPIView
# )
# from rest_framework.response import Response
# from rest_framework.exceptions import PermissionDenied

# from teams.models import Team, TeamMembership
# from teams.serializers import TeamMembershipSerializer
# from teams.permissions import IsTeamMember, IsTeamOwner
# from notifications.services import create_notification


# class TeamMembershipListView(ListAPIView):
#     """
#     List members of a team
    
#     GET /api/teams/{team_id}/members/
#     """
#     serializer_class = TeamMembershipSerializer
#     permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    
#     def get_queryset(self):
#         """Return memberships for the specified team"""
#         team_id = self.kwargs.get('team_id')
#         try:
#             team = Team.objects.get(id=team_id)
#             self.check_object_permissions(self.request, team)
#             return TeamMembership.objects.filter(team=team)
#         except Team.DoesNotExist:
#             return TeamMembership.objects.none()


# class TeamMembershipCreateView(CreateAPIView):
#     """
#     Add a member to a team (owners only)
    
#     POST /api/teams/{team_id}/members/
#     Required data:
#     - username: Username of user to add
#     - role: Role to assign (default: 'member')
#     """
#     serializer_class = TeamMembershipSerializer
#     permission_classes = [permissions.IsAuthenticated, IsTeamOwner]
    
#     def get_serializer_context(self):
#         """Add team to serializer context"""
#         context = super().get_serializer_context()
#         context['team_id'] = self.kwargs.get('team_id')
#         return context
        
#     def perform_create(self, serializer):
#         """Add user to team"""
#         team_id = self.kwargs.get('team_id')
#         try:
#             team = Team.objects.get(id=team_id)
#             self.check_object_permissions(self.request, team)
            
#             # Create membership
#             membership = serializer.save(team=team)
            
#             # Notify new member
#             create_notification(
#                 recipient=membership.user,
#                 content=f"You were added to team '{team.name}' by {self.request.user.username}",
#                 notification_type='system',
#                 related_object=team,
#                 priority='medium'
#             )
            
#         except Team.DoesNotExist:
#             raise PermissionDenied("Team does not exist")


# class TeamMembershipDetailView(RetrieveUpdateDestroyAPIView):
#     """
#     Manage a team membership (owners only)
    
#     GET /api/teams/{team_id}/members/{id}/
#     PATCH /api/teams/{team_id}/members/{id}/ - Update role
#     DELETE /api/teams/{team_id}/members/{id}/ - Remove member
#     """
#     serializer_class = TeamMembershipSerializer
#     permission_classes = [permissions.IsAuthenticated, IsTeamOwner]
#     lookup_field = 'id'
    
#     def get_queryset(self):
#         """Return memberships for the specified team"""
#         team_id = self.kwargs.get('team_id')
#         return TeamMembership.objects.filter(team_id=team_id)
        
#     def perform_update(self, serializer):
#         """Update membership and notify user"""
#         membership = self.get_object()
#         old_role = membership.get_role_display()
#         updated = serializer.save()
        
#         if old_role != updated.get_role_display():
#             create_notification(
#                 recipient=updated.user,
#                 content=f"Your role in team '{updated.team.name}' was changed to {updated.get_role_display()}",
#                 notification_type='system',
#                 related_object=updated.team,
#                 priority='medium'
#             )
    
#     def perform_destroy(self, instance):
#         """Remove member from team and notify them"""
#         team = instance.team
#         user = instance.user
        
#         # Prevent removing the last owner
#         if instance.role == TeamMembership.ROLE_OWNER:
#             owner_count = TeamMembership.objects.filter(
#                 team=team, 
#                 role=TeamMembership.ROLE_OWNER
#             ).count()
            
#             if owner_count <= 1:
#                 raise PermissionDenied("Cannot remove the last owner of the team")
        
#         # Delete membership
#         instance.delete()
        
#         # Notify removed member
#         create_notification(
#             recipient=user,
#             content=f"You were removed from team '{team.name}' by {self.request.user.username}",
#             notification_type='system',
#             related_object=team,
#             priority='medium'
#         )