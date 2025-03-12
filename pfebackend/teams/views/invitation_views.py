from rest_framework import permissions, status
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    ListAPIView,
    DestroyAPIView
)
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from teams.models import Team, TeamInvitation, TeamMembership
from teams.serializers import TeamInvitationSerializer, InvitationResponseSerializer
from teams.permissions import IsTeamMember, IsInvitationRecipient, IsTeamOwnerOrInviter
from teams.services import TeamInvitationService


class TeamInvitationCreateView(CreateAPIView):
    """
    API endpoint for creating team invitations
    
    POST /api/team-invitations/
    Required data:
    - team_id: ID of the team to invite to
    - invitee_username: Username of the user to invite
    """
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Create a team invitation and send notification"""
        team = serializer.validated_data['team']
        invitee = serializer.validated_data['invitee']
        inviter = self.request.user

        # Check if inviter is part of the team
        if not TeamMembership.objects.filter(team=team, user=inviter).exists():
            raise PermissionDenied("You must be a member of the team to invite others")

        # Create invitation using service
        try:
            invitation = TeamInvitationService.create_invitation(
                team=team,
                inviter=inviter,
                invitee=invitee
            )
            serializer.instance = invitation
        except ValueError as e:
            raise ValidationError(str(e))


class InvitationListView(ListAPIView):
    """
    List invitations for the current user
    
    GET /api/invitations/
    """
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return pending invitations for the current user"""
        return TeamInvitationService.get_user_pending_invitations(self.request.user)


class InvitationResponseView(RetrieveUpdateAPIView):
    """
    Accept or decline a team invitation
    
    GET /api/invitations/{id}/
    PATCH /api/invitations/{id}/
    Required data for PATCH:
    - action: 'accept' or 'decline'
    """
    queryset = TeamInvitation.objects.filter(status=TeamInvitation.STATUS_PENDING)
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsInvitationRecipient]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for GET and PATCH"""
        if self.request.method in ['PATCH', 'PUT']:
            return InvitationResponseSerializer
        return TeamInvitationSerializer
        
    def update(self, request, *args, **kwargs):
        """Handle invitation response (accept/decline)"""
        invitation_id = self.kwargs.get('id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        
        # Process invitation response using service
        success, result = TeamInvitationService.process_invitation_response(
            user=request.user,
            invitation_id=invitation_id,
            response=action
        )
        
        if not success:
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': 'Failed to process invitation response'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return appropriate success response
        if action == 'accept':
            return Response({
                'status': 'accepted',
                'message': f"You have joined the team '{result['team_name']}'",
                'team_id': result['team_id'],
                'role': result.get('role', 'member')
            })
            
        elif action == 'decline':
            return Response({
                'status': 'declined',
                'message': f"You have declined the invitation to join '{result['team_name']}'"
            })
            

class InvitationCancelView(DestroyAPIView):
    """
    Cancel a pending invitation
    
    DELETE /api/invitations/{id}/cancel/
    
    Only the inviter or a team owner can cancel an invitation
    """
    queryset = TeamInvitation.objects.filter(status=TeamInvitation.STATUS_PENDING)
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamOwnerOrInviter]
    lookup_field = 'id'
    
    def perform_destroy(self, instance):
        """Cancel the invitation"""
        success = TeamInvitationService.cancel_invitation(
            invitation_id=instance.id,
            cancelling_user=self.request.user
        )
        
        if not success:
            raise PermissionDenied("You don't have permission to cancel this invitation")





# from rest_framework import permissions, status
# from rest_framework.generics import (
#     CreateAPIView,
#     RetrieveUpdateAPIView,
#     ListAPIView,
# )
# from rest_framework.response import Response
# from rest_framework.exceptions import PermissionDenied, ValidationError

# from teams.models import Team, TeamInvitation, TeamMembership
# from teams.serializers import TeamInvitationSerializer, InvitationResponseSerializer
# from teams.permissions import IsTeamMember, IsInvitationRecipient
# from teams.services import  accept_invitation, decline_invitation
# from teams.services import TeamService, TeamInvitationService
# from notifications.services import NotificationService

# class TeamInvitationCreateView(CreateAPIView):
#     """
#     API endpoint for creating team invitations
    
#     POST /api/team-invitations/
#     Required data:
#     - team_id: ID of the team to invite to
#     - invitee_username: Username of the user to invite
#     """
#     serializer_class = TeamInvitationSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         """Create a team invitation and send notification"""
#         team = serializer.validated_data['team']
#         invitee = serializer.validated_data['invitee']
#         inviter = self.request.user

#         # Check if inviter is part of the team
#         if not TeamMembership.objects.filter(team=team, user=inviter).exists():
#             raise PermissionDenied("You must be a member of the team to invite others")

#         # Create invitation using service
#         invitation = TeamInvitationService.create_invitation(
#             team=team,
#             inviter=inviter,
#             invitee=invitee
#         )
        
#         # Send notification to invitee
#         NotificationService.create_notification(
#             recipient=invitee,
#             content=f"{inviter.username} invited you to join team '{team.name}'",
#             notification_type='invitation',
#             related_object=invitation,
#             priority='medium'
#         )

#         serializer.instance = invitation


# class InvitationListView(ListAPIView):
#     """
#     List invitations for the current user
    
#     GET /api/invitations/
#     """
#     serializer_class = TeamInvitationSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         """Return pending invitations for the current user"""
#         return TeamInvitation.objects.filter(
#             invitee=self.request.user,
#             status=TeamInvitation.STATUS_PENDING
#         )


# class InvitationResponseView(RetrieveUpdateAPIView):
#     """
#     Accept or decline a team invitation
    
#     GET /api/invitations/{id}/
#     PATCH /api/invitations/{id}/
#     Required data for PATCH:
#     - action: 'accept' or 'decline'
#     """
#     queryset = TeamInvitation.objects.filter(status=TeamInvitation.STATUS_PENDING)
#     serializer_class = TeamInvitationSerializer
#     permission_classes = [permissions.IsAuthenticated, IsInvitationRecipient]
#     lookup_field = 'id'
    
#     def get_serializer_class(self):
#         """Use different serializers for GET and PATCH"""
#         if self.request.method in ['PATCH', 'PUT']:
#             return InvitationResponseSerializer
#         return TeamInvitationSerializer
        
#     def update(self, request, *args, **kwargs):
#         """Handle invitation response (accept/decline)"""
#         invitation = self.get_object()
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         action = serializer.validated_data['action']
#         team = invitation.team
        
#         if action == 'accept':
#             # Accept invitation and create membership
#             membership = accept_invitation(invitation)
            
#             # Notify team members
#             NotificationService.create_notification(
#                 recipient=invitation.inviter,
#                 content=f"{request.user.username} accepted your invitation to join '{team.name}'",
#                 notification_type='system',
#                 related_object=team,
#                 priority='medium'
#             )
            
#             return Response({
#                 'status': 'accepted',
#                 'message': f"You have joined the team '{team.name}'",
#                 'team_id': team.id
#             })
            
#         elif action == 'decline':
#             # Decline invitation
#             decline_invitation(invitation)
            
#             # Notify inviter
#             NotificationService.create_notification(
#                 recipient=invitation.inviter,
#                 content=f"{request.user.username} declined your invitation to join '{team.name}'",
#                 notification_type='system',
#                 related_object=team,
#                 priority='low'
#             )
            
#             return Response({
#                 'status': 'declined',
#                 'message': f"You have declined the invitation to join '{team.name}'"
#             })