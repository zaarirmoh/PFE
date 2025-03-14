# Create join_request_views.py
from rest_framework import permissions, status
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    ListAPIView,
    DestroyAPIView
)
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from teams.models import Team, TeamJoinRequest, TeamMembership
from teams.serializers import TeamJoinRequestSerializer, JoinRequestResponseSerializer
from teams.permissions import (
    IsTeamMember, IsTeamOwner, IsJoinRequestRequester, IsTeamOwnerForJoinRequest
)
from teams.services import TeamJoinRequestService
from users.permissions import IsStudent


class JoinRequestCreateView(CreateAPIView):
    """
    API endpoint for creating team join requests
    
    POST /api/join-requests/
    Required data:
    - team_id: ID of the team to join
    - message: (Optional) message to team owners
    """
    serializer_class = TeamJoinRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def perform_create(self, serializer):
        """Create a team join request and send notification"""
        team = serializer.validated_data['team']
        message = serializer.validated_data.get('message', '')
        requester = self.request.user

        # Create join request using service
        try:
            join_request = TeamJoinRequestService.create_join_request(
                team=team,
                requester=requester,
                message=message
            )
            serializer.instance = join_request
        except ValueError as e:
            raise ValidationError(str(e))


class UserJoinRequestListView(ListAPIView):
    """
    List join requests created by the current user
    
    GET /api/join-requests/
    """
    serializer_class = TeamJoinRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return pending join requests for the current user"""
        return TeamJoinRequestService.get_user_pending_requests(self.request.user)


class TeamJoinRequestListView(ListAPIView):
    """
    List join requests for a specific team (team owners only)
    
    GET /api/teams/{team_id}/join-requests/
    """
    serializer_class = TeamJoinRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamOwner]
    
    def get_queryset(self):
        """Return pending join requests for the team"""
        team_id = self.kwargs.get('team_id')
        try:
            team = Team.objects.get(id=team_id)
            self.check_object_permissions(self.request, team)
            return TeamJoinRequestService.get_team_pending_requests(team)
        except Team.DoesNotExist:
            return TeamJoinRequest.objects.none()


class JoinRequestDetailView(RetrieveUpdateAPIView):
    """
    View or respond to a join request
    
    GET /api/join-requests/{id}/
    PATCH /api/join-requests/{id}/
    
    For GET:
    - Team owners or the requester can view
    
    For PATCH (team owners only):
    - action: 'accept' or 'decline'
    """
    queryset = TeamJoinRequest.objects.filter(status=TeamJoinRequest.STATUS_PENDING)
    lookup_field = 'id'
    
    def get_permissions(self):
        """Use different permission classes based on the request method"""
        if self.request.method in ['PATCH', 'PUT']:
            return [permissions.IsAuthenticated(), IsTeamOwnerForJoinRequest()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        """Use different serializers for GET and PATCH"""
        if self.request.method in ['PATCH', 'PUT']:
            return JoinRequestResponseSerializer
        return TeamJoinRequestSerializer
    
    def check_object_permissions(self, request, obj):
        """Custom permission check that allows team owners or the requester"""
        if request.method in ['PATCH', 'PUT']:
            # For updates, only team owners can respond
            super().check_object_permissions(request, obj)
        else:
            # For retrieval, either team owner or requester can view
            is_owner = TeamMembership.objects.filter(
                team=obj.team,
                user=request.user,
                role=TeamMembership.ROLE_OWNER
            ).exists()
            
            is_requester = obj.requester == request.user
            
            if not (is_owner or is_requester):
                self.permission_denied(
                    request,
                    message="You do not have permission to view this join request"
                )
    
    def update(self, request, *args, **kwargs):
        """Handle join request response (accept/decline)"""
        request_id = self.kwargs.get('id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        
        # Process join request response using service
        success, result = TeamJoinRequestService.process_join_request_response(
            user=request.user,
            request_id=request_id,
            response=action
        )
        
        if not success:
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': 'Failed to process join request response'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return appropriate success response
        if action == 'accept':
            return Response({
                'status': 'accepted',
                'message': f"You have accepted {result['requester_username']}'s request to join the team",
                'team_id': result['team_id'],
                'team_name': result['team_name']
            })
            
        elif action == 'decline':
            return Response({
                'status': 'declined',
                'message': f"You have declined {result['requester_username']}'s request to join the team"
            })


class JoinRequestCancelView(DestroyAPIView):
    """
    Cancel a pending join request
    
    DELETE /api/join-requests/{id}/cancel/
    
    Only the requester can cancel their own join request
    """
    queryset = TeamJoinRequest.objects.filter(status=TeamJoinRequest.STATUS_PENDING)
    serializer_class = TeamJoinRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsJoinRequestRequester]
    lookup_field = 'id'
    
    def perform_destroy(self, instance):
        """Cancel the join request"""
        success = TeamJoinRequestService.cancel_join_request(
            request_id=instance.id,
            user=self.request.user
        )
        
        if not success:
            raise PermissionDenied("You don't have permission to cancel this join request")