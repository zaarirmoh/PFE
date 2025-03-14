from rest_framework import permissions
from teams.models import Team, TeamMembership, TeamInvitation


class IsTeamMember(permissions.BasePermission):
    """
    Permission check for team membership.
    """
    def has_object_permission(self, request, view, obj):
        # Determine if obj is a Team or has a team attribute
        if isinstance(obj, Team):
            team = obj
        elif hasattr(obj, 'team'):
            team = obj.team
        else:
            return False
            
        # Check if user is a member of the team
        return TeamMembership.objects.filter(
            team=team,
            user=request.user
        ).exists()


class IsTeamOwner(permissions.BasePermission):
    """
    Permission check for team ownership.
    """
    def has_object_permission(self, request, view, obj):
        # Determine if obj is a Team or has a team attribute
        if isinstance(obj, Team):
            team = obj
        elif hasattr(obj, 'team'):
            team = obj.team
        else:
            return False
            
        # Check if user is an owner of the team
        return TeamMembership.objects.filter(
            team=team,
            user=request.user,
            role=TeamMembership.ROLE_OWNER
        ).exists()


class IsInvitationRecipient(permissions.BasePermission):
    """
    Permission check for invitation recipient.
    """
    def has_object_permission(self, request, view, obj):
        # Make sure the user is the invitee
        return obj.invitee == request.user


class IsTeamOwnerOrInviter(permissions.BasePermission):
    """
    Permission check for team owner or the person who sent the invitation.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is the inviter
        if obj.inviter == request.user:
            return True
            
        # Check if user is an owner of the team
        return TeamMembership.objects.filter(
            team=obj.team,
            user=request.user,
            role=TeamMembership.ROLE_OWNER
        ).exists()

class IsJoinRequestRequester(permissions.BasePermission):
    """
    Permission check for join request requester.
    """
    def has_object_permission(self, request, view, obj):
        # Make sure the user is the requester
        return obj.requester == request.user


class IsTeamOwnerForJoinRequest(permissions.BasePermission):
    """
    Permission check for team owners related to join requests.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is an owner of the team
        return TeamMembership.objects.filter(
            team=obj.team,
            user=request.user,
            role=TeamMembership.ROLE_OWNER
        ).exists()