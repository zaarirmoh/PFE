# meetings/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from .models import Meeting
from .serializers import (
    MeetingListSerializer,
    MeetingDetailSerializer,
    MeetingCreateUpdateSerializer,
    MeetingStatusUpdateSerializer,
    ProjectListSerializer,
)
from .services import MeetingService
# from .permissions import IsTeacherOrReadOnly, IsMeetingCreatorOrReadOnly
from users.models import Teacher
import logging
from rest_framework import serializers
from common.pagination import StaticPagination
from themes.serializers import ThemeAssignmentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from themes.models import ThemeAssignment
from .filters import ProjectListFilter


logger = logging.getLogger(__name__)


class MeetingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing meetings
    """
    # permission_classes = [IsAuthenticated, IsTeacherOrReadOnly]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'team__name']
    ordering_fields = ['scheduled_at', 'created_at', 'team__name']
    ordering = ['scheduled_at']
    pagination_class = StaticPagination
    
    def get_queryset(self):
        """
        Return meetings based on user's role:
        - Teachers: All meetings they created
        - Students: All meetings for teams they are members of
        """
        user = self.request.user
        
        # Check if user is a teacher
        is_teacher = hasattr(user, 'teacher')
        
        if is_teacher:
            # Teachers see all meetings they created
            return Meeting.objects.filter(scheduled_by=user).select_related(
                'scheduled_by', 'team'
            )
        else:
            # Students see meetings for teams they belong to
            return Meeting.objects.filter(team__members=user).select_related(
                'scheduled_by', 'team'
            )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MeetingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MeetingCreateUpdateSerializer
        elif self.action == 'update_status':
            return MeetingStatusUpdateSerializer
        else:
            return MeetingDetailSerializer
    
    def perform_create(self, serializer):
        """Create a meeting using the MeetingService"""
        user = self.request.user
        team_id = serializer.validated_data.get('team').id
        
        try:
            # Check if user is a teacher
            Teacher.objects.get(user=user)
            
            # Use the service to create the meeting
            meeting_data = {key: value for key, value in serializer.validated_data.items() 
                           if key != 'team'}
            
            meeting = MeetingService.create_meeting(
                teacher_user=user,
                team_id=team_id,
                # team_id=team_id,
                meeting_data=meeting_data
            )
            
            # Set the created instance for the serializer
            serializer.instance = meeting
            
        except Teacher.DoesNotExist:
            raise PermissionDenied("Only teachers can create meetings.")
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def perform_update(self, serializer):
        """Update a meeting using the MeetingService"""
        user = self.request.user
        meeting_id = self.get_object().id
        
        try:
            # Use the service to update the meeting
            meeting_data = {key: value for key, value in serializer.validated_data.items() 
                           if key != 'team'}  # Team cannot be changed
            
            meeting = MeetingService.update_meeting(
                meeting_id=meeting_id,
                teacher_user=user,
                meeting_data=meeting_data
            )
            
            # Set the updated instance for the serializer
            serializer.instance = meeting
            
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        except PermissionDenied as e:
            raise PermissionDenied(str(e))
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a meeting"""
        user = self.request.user
        meeting = self.get_object()
        
        try:
            cancelled_meeting = MeetingService.cancel_meeting(
                meeting_id=meeting.id,
                teacher_user=user
            )
            
            serializer = self.get_serializer(cancelled_meeting)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a meeting as completed"""
        user = self.request.user
        meeting = self.get_object()
        
        try:
            # Check if user is the meeting creator
            if meeting.scheduled_by != user:
                raise PermissionDenied("Only the meeting creator can mark it as completed.")
                
            meeting.mark_as_completed(completed_by=user)
            serializer = self.get_serializer(meeting)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        

from .models import Upload
from .serializers import UploadSerializer
from users.permissions import IsTeacher
from teams.permissions import IsTeamMember
from rest_framework.exceptions import PermissionDenied

class UploadViewSet(viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [IsTeamMember()]
        if self.action in ['list', 'retrieve']:
            return [IsTeamMember() | IsTeacher()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        if not IsTeamMember().has_permission(self.request, self):
            raise PermissionDenied("Only team members can upload resources.")
        serializer.save(uploaded_by=self.request.user)

    
    # @action(detail=True, methods=['get'])
    # def attendances(self, request, pk=None):
    #     """Get all attendance records for a meeting"""
    #     meeting = self.get_object()
        
    #     # Check if user has access to view attendances
    #     user = self.request.user
    #     if meeting.scheduled_by != user and user not in meeting.team.members.all():
    #         return Response(
    #             {'error': 'You do not have permission to view this meeting\'s attendances'},
    #             status=status.HTTP_403_FORBIDDEN
    #         )
        
    #     attendances = MeetingAttendance.objects.filter(meeting=meeting).select_related('attendee')
    #     serializer = MeetingAttendanceSerializer(attendances, many=True)
    #     return Response(serializer.data)
    
    # @action(detail=True, methods=['get'])
    # def my_attendance(self, request, pk=None):
    #     """Get the attendance record for the current user"""
    #     meeting = self.get_object()
    #     user = self.request.user
        
    #     try:
    #         # Find the user's attendance record
    #         attendance = MeetingAttendance.objects.get(meeting=meeting, attendee=user)
    #         serializer = MeetingAttendanceSerializer(attendance)
    #         return Response(serializer.data)
            
    #     except MeetingAttendance.DoesNotExist:
    #         return Response(
    #             {'error': 'You do not have an attendance record for this meeting'},
    #             status=status.HTTP_404_NOT_FOUND
    #         )


# class MeetingAttendanceViewSet(viewsets.GenericViewSet):
#     """
#     API endpoint for managing meeting attendance
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = MeetingAttendanceSerializer
    
#     def get_queryset(self):
#         """Return all attendance records for the authenticated user"""
#         return MeetingAttendance.objects.filter(
#             attendee=self.request.user
#         ).select_related('meeting', 'meeting__team')
    
#     @action(detail=True, methods=['patch'])
#     def update_status(self, request, pk=None):
#         """Update the status of an attendance record"""
#         user = self.request.user
        
#         serializer = MeetingAttendanceUpdateSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         status_value = serializer.validated_data.get('status')
#         notes = serializer.validated_data.get('response_notes', '')
        
#         try:
#             # Use the service to update attendance status
#             attendance = MeetingService.update_attendance_status(
#                 attendance_id=pk,
#                 user=user,
#                 status=status_value,
#                 notes=notes
#             )
            
#             result_serializer = MeetingAttendanceSerializer(attendance)
#             return Response(result_serializer.data)
            
#         except ValidationError as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except PermissionDenied as e:
#             return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
    
#     @action(detail=False, methods=['get'])
#     def pending(self, request):
#         """Get all pending attendance records for the user"""
#         user = self.request.user
        
#         pending = MeetingAttendance.objects.filter(
#             attendee=user,
#             status=MeetingAttendance.STATUS_PENDING,
#             meeting__status=Meeting.STATUS_SCHEDULED
#         ).select_related('meeting', 'meeting__team', 'meeting__scheduled_by')
        
#         serializer = MeetingAttendanceSerializer(pending, many=True)
#         return Response(serializer.data)


class ProjectListView(ListAPIView):
    """
    List projects (theme assignments) with comprehensive filtering options.
    
    ## Endpoints
    GET /api/projects/ - List all projects with filtering options
    
    ## Query Parameters
    - Basic filters:
        - `academic_year` - Filter by academic year (e.g., '5siw', '4isi')
        - `theme_id` - Filter by specific theme ID
        - `supervisor_id` - Filter by supervisor ID (includes both main and co-supervisors)
        - `team_id` - Filter by specific team ID
        - `member_id` - Filter by team member ID
        - `status` - Filter by assignment status
    
    - Date filters:
        - `date_from` - Projects created on or after specified date (YYYY-MM-DD)
        - `date_to` - Projects created on or before specified date (YYYY-MM-DD)
    
    - Searching:
        - `search` - Search in theme titles and team names
    
    - Sorting:
        - `ordering` - Sort by field (prefix with - for descending)
          Examples: ordering=theme__title, ordering=-created_at
          Available fields: created_at, team__name, theme__title, academic_year, status
    
    - Pagination:
        - `page` - Page number
        - `page_size` - Number of results per page
    
    ## Response
    Returns a paginated list of projects with detailed information including:
    - Theme details
    - Team information
    - Team members with roles
    - Team owner
    - Supervisors (proposer and co-supervisors)
    - Associated uploads
    - Scheduled meetings
    """
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectListFilter
    search_fields = ['theme__title', 'team__name']
    ordering_fields = ['created_at', 'team__name', 'theme__title', 'academic_year', 'status']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """
        Get all theme assignments with prefetched related data for performance
        """
        return ThemeAssignment.objects.select_related(
            'theme', 'team', 'assigned_by'
        ).prefetch_related(
            'theme__co_supervisors',
            'team__members',
            'team__uploads',
            'team__meetings',
            'team__teammembership_set',
            'team__teammembership_set__user'
        ).all()
