from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from themes.models import Theme, ThemeSupervisionRequest
from teams.models import Team, TeamMembership
from themes.services.theme_supervision_service import ThemeSupervisionService
from themes.serializers import (
    ThemeSupervisionRequestSerializer,
    CreateThemeSupervisionRequestSerializer,
    ProcessSupervisionRequestSerializer
)
from teams.permissions import IsTeamOwner, IsTeamMember
from themes.permissions import IsThemeSupervisor
from common.pagination import StaticPagination
from themes.filters import ThemeSupervisionRequestFilter
from django_filters.rest_framework import DjangoFilterBackend


class TeamSupervisionRequestListView(generics.ListAPIView):
    """
    View to get supervision requests made by a team
    
    Filter parameters:
    - status: Filter by exact status (PENDING, ACCEPTED, DECLINED)
    - status_in: Filter by multiple statuses (comma-separated)
    - theme: Filter by theme ID
    - invitee: Filter by invitee user ID
    - created_after: Filter by creation date (greater than or equal)
    - created_before: Filter by creation date (less than or equal)
    """
    serializer_class = ThemeSupervisionRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ThemeSupervisionRequestFilter
    
    def get_queryset(self):
        team_id = self.kwargs.get('team_id')
        team = get_object_or_404(Team, id=team_id)
        
        # Verify user is a team member
        if not team.members.filter(id=self.request.user.id).exists():
            return ThemeSupervisionRequest.objects.none()
        
        return ThemeSupervisionService.get_team_supervision_requests(team)


class UserSupervisionRequestListView(generics.ListAPIView):
    """
    View to get supervision requests for a user (as supervisor)
    
    Filter parameters:
    - status: Filter by exact status (PENDING, ACCEPTED, DECLINED)
    - status_in: Filter by multiple statuses (comma-separated)
    - team: Filter by team ID
    - theme: Filter by theme ID
    - requester: Filter by requester user ID
    - academic_year: Filter by theme's academic year
    - created_after: Filter by creation date (greater than or equal)
    - created_before: Filter by creation date (less than or equal)
    """
    serializer_class = ThemeSupervisionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ThemeSupervisionRequestFilter

    
    # def get_queryset(self):
    #     return ThemeSupervisionService.get_user_pending_supervision_requests(self.request.user.student)
    def get_queryset(self):
        user = self.request.user
        
        # Handle different user types
        if user.user_type == 'teacher':
            # For teachers, get requests for themes they supervise
            return ThemeSupervisionService.get_user_pending_supervision_requests(user)
        
        elif user.user_type == 'student':
            try:
                # Get teams where student is an owner
                teams = Team.objects.filter(
                    members=user,
                    teammembership__role=TeamMembership.ROLE_OWNER
                )
                
                # Get all requests for these teams
                all_requests = []
                for team in teams:
                    team_requests = ThemeSupervisionService.get_team_supervision_requests(team)
                    all_requests.extend(team_requests)
                
                return ThemeSupervisionRequest.objects.filter(id__in=[req.id for req in all_requests])
            except:
                return ThemeSupervisionRequest.objects.none()
        else:
            return ThemeSupervisionRequest.objects.none()


# class CreateSupervisionRequestView(generics.CreateAPIView):
#     """
#     View to create a new supervision request
#     """
#     serializer_class = CreateThemeSupervisionRequestSerializer
#     permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         # Get validated data
#         theme = serializer.validated_data['theme']
#         team = serializer.validated_data['team']
#         invitee = serializer.validated_data['invitee']
#         message = serializer.validated_data.get('message', '')
        
#         try:
#             # Create the supervision request using the service
#             supervision_request = ThemeSupervisionService.create_supervision_request(
#                 theme=theme,
#                 team=team,
#                 requester=request.user.student,
#                 invitee=invitee,  # Pass the invitee to the service
#                 message=message
#             )
            
#             # Serialize the created request
#             response_serializer = ThemeSupervisionRequestSerializer(supervision_request)
            
#             return Response({
#                 'supervision_request': response_serializer.data,
#                 'message': f'Supervision request sent to {invitee.get_full_name() or invitee.username}'
#             }, status=status.HTTP_201_CREATED)
            
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
class CreateSupervisionRequestView(generics.CreateAPIView):
    """
    View to create a new supervision request
    """
    serializer_class = CreateThemeSupervisionRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeamMember]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get validated data
        theme = serializer.validated_data['theme']
        team = serializer.validated_data['team']
        invitee = serializer.validated_data['invitee']
        message = serializer.validated_data.get('message', '')
        
        try:
            # Ensure the user is a student
            if request.user.user_type != 'student':
                return Response({'error': 'Only students can request theme supervision'}, 
                                status=status.HTTP_403_FORBIDDEN)
            
            # Get the student instance if possible
            try:
                student_instance = request.user.student
            except:
                return Response({'error': 'Student profile not found'}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Create the supervision request using the service
            supervision_request = ThemeSupervisionService.create_supervision_request(
                theme=theme,
                team=team,
                requester=request.user,  # Pass student instance
                invitee=invitee,
                message=message
            )
            
            # Serialize the created request
            response_serializer = ThemeSupervisionRequestSerializer(supervision_request)
            
            return Response({
                'supervision_request': response_serializer.data,
                'message': f'Supervision request sent to {invitee.get_full_name() or invitee.username}'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelSupervisionRequestView(APIView):
    """
    View to cancel a supervision request
    """
    permission_classes = [permissions.IsAuthenticated, IsTeamOwner]
    
    def post(self, request, request_id):
        # Cancel the request using the service
        success = ThemeSupervisionService.cancel_supervision_request(
            request_id=request_id,
            user=request.user
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Supervision request cancelled successfully'
            })
        else:
            return Response({
                'error': 'Unable to cancel supervision request'
            }, status=status.HTTP_400_BAD_REQUEST)
            
            
            
            
class SupervisionRequestResponseView(generics.RetrieveUpdateAPIView):
    """
    Accept or decline a theme supervision request
    
    GET /api/supervision-requests/{id}/
    PATCH /api/supervision-requests/{id}/
    Required data for PATCH:
    - action: 'accept' or 'decline'
    - message: Optional response message
    """
    queryset = ThemeSupervisionRequest.objects.filter(status=ThemeSupervisionRequest.STATUS_PENDING)
    serializer_class = ThemeSupervisionRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsThemeSupervisor]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use different serializers for GET and PATCH"""
        if self.request.method in ['PATCH', 'PUT']:
            return ProcessSupervisionRequestSerializer
        return ThemeSupervisionRequestSerializer
        
    def update(self, request, *args, **kwargs):
        """Handle supervision request response (accept/decline)"""
        request_id = self.kwargs.get('id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response = serializer.validated_data['response']
        message = serializer.validated_data.get('message', '')
        
        # Process supervision response using service
        success, result = ThemeSupervisionService.process_supervision_request_response(
            user=request.user,
            request_id=request_id,
            response=response,
            message=message
        )
        
        if not success:
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': 'Failed to process supervision request response'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return appropriate success response
        if response == 'accept':
            return Response({
                'status': 'accepted',
                'message': f"You are now supervising the theme '{result['theme_title']}' for team '{result['team_name']}'",
                'theme_id': result['theme_id'],
                'team_id': result['team_id']
            })
            
        elif response == 'decline':
            return Response({
                'status': 'declined',
                'message': f"You have declined to supervise the theme '{result['theme_title']}' for team '{result['team_name']}'"
            })