from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from .models import Meeting, Defense
from .serializers import (
    MeetingListSerializer,
    MeetingDetailSerializer,
    MeetingCreateUpdateSerializer,
    MeetingStatusUpdateSerializer,
    ProjectListSerializer,
    DefenseSerializer,
    DefenseDetailSerializer,
)
from .services import MeetingService
from users.models import Teacher
import logging
from rest_framework import serializers
from common.pagination import StaticPagination
from notifications.services import NotificationService
from themes.serializers import ThemeAssignmentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from themes.models import ThemeAssignment
from .filters import ProjectListFilter
from teams.permissions import IsTeamOwner
from .permissions import IsJuryPresident

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
        

from .models import Upload, ResourceComment
from .serializers import UploadSerializer, ResourceCommentSerializer
from users.permissions import IsTeacher
from teams.permissions import IsTeamMember
from rest_framework.exceptions import PermissionDenied
from teams.models import Team
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def get_supervisors_and_teachers(team_id):
    """Helper function to get all supervisors and proposed by teachers for a team"""
    try:
        team = Team.objects.get(id=team_id)
        recipients = []
        
        # Check if team has an assigned theme
        if hasattr(team, 'assigned_theme') and team.assigned_theme:
            theme = team.assigned_theme.theme
            
            # Add co-supervisors
            recipients.extend(list(theme.co_supervisors.all()))
            
            # Add the main supervisor (proposed_by)
            if theme.proposed_by:
                recipients.append(theme.proposed_by)
        
        return recipients
    except Team.DoesNotExist:
        return []


def notify_upload(user, team_id, upload_title):
    """Helper function to send notifications about new uploads"""
    recipients = get_supervisors_and_teachers(team_id)
    for recipient in recipients:
        NotificationService.create_and_send(
            recipient=recipient,
            content=f"New resource '{upload_title}' uploaded by {user.username}",
            notification_type="resource_upload",
            metadata={
                "profile_picture": user.profile_picture_url,
            },
        )


class UploadViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing file uploads.

    Provides CRUD operations for file uploads with team-based access control:
    - Students can only see uploads from their teams
    - Teachers can see all uploads or filter by team
    - Team members can upload files for their teams
    """
    serializer_class = UploadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['team']
    search_fields = ['title']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return uploads based on user's role:
        - Teachers: All uploads (can filter by team)
        - Students: Only uploads from teams they are members of
        """
        user = self.request.user
        
        # Check if user is a teacher
        is_teacher = hasattr(user, 'teacher')
        
        if is_teacher:
            # Teachers see all uploads, can filter by team using query params
            return Upload.objects.all().select_related('uploaded_by', 'team')
        else:
            # Students see only uploads from their teams
            user_team_ids = user.teams.values_list('id', flat=True)
            return Upload.objects.filter(team_id__in=user_team_ids).select_related('uploaded_by', 'team')

    @swagger_auto_schema(
        operation_description="""
        Get a list of uploads with filtering, searching, and ordering capabilities.
        
        **Access Control:**
        - Students: Only see uploads from their teams
        - Teachers: See all uploads, can filter by team
        
        **Permissions:**
        - Requires authentication
        - Students automatically filtered to their team uploads
        - Teachers can access all uploads
        
        **Filtering:**
        - Use 'team' parameter to filter by team ID
        - Teachers can filter by any team, students are automatically filtered to their teams
        
        **Searching:**
        - Search in upload titles using 'search' parameter
        
        **Ordering:**
        - Sort by 'created_at' or 'title' (use '-' prefix for descending order)
        """,
        manual_parameters=[
            openapi.Parameter(
                "team", 
                openapi.IN_QUERY, 
                description="Filter uploads by team ID. Students can only see their team uploads, teachers can filter by any team.", 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "search", 
                openapi.IN_QUERY, 
                description="Search uploads by title", 
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "ordering", 
                openapi.IN_QUERY, 
                description="Order results by field. Available: 'created_at', 'title', '-created_at', '-title'", 
                type=openapi.TYPE_STRING, 
                enum=["created_at", "-created_at", "title", "-title"]
            ),
            openapi.Parameter(
                "page", 
                openapi.IN_QUERY, 
                description="Page number for pagination", 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "page_size", 
                openapi.IN_QUERY, 
                description="Number of results per page (default: 20)", 
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of uploads with pagination",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of uploads'),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, description='Next page URL'),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, description='Previous page URL'),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            400: "Bad Request - Invalid parameters",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Access denied"
        }
    )
    def list(self, request, *args, **kwargs):
        """List uploads with team-based filtering, searching, and ordering."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        Create a new upload. Only team members can upload files for their teams.
        
        **Permissions:**
        - Requires authentication
        - User should be a member of the specified team (documented requirement)
        
        **Requirements:**
        - File and team ID are required
        - Notifications will be sent to supervisors and teachers
        """,
        request_body=UploadSerializer,
        responses={
            201: openapi.Response(
                description="Upload created successfully",
                schema=UploadSerializer()
            ),
            400: "Bad Request - Invalid data or missing required fields",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Not a team member or access denied",
            413: "Payload Too Large - File size exceeds limit"
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new upload for a team."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        Retrieve details of a specific upload including all comments.
        
        **Access Control:**
        - Students: Can only access uploads from their teams
        - Teachers: Can access any upload
        
        **Permissions:**
        - Requires authentication
        - Access automatically filtered based on user role
        """,
        responses={
            200: UploadSerializer(),
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Access denied",
            404: "Upload not found",
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve upload details with comments."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        Update an existing upload. Only the uploader or teachers can modify uploads.
        
        **Permissions:**
        - Requires authentication
        - Upload owner can update their own uploads (documented requirement)
        - Teachers can update any upload (documented requirement)
        """,
        request_body=UploadSerializer,
        responses={
            200: UploadSerializer(),
            400: "Bad Request - Invalid data",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Not the uploader or teacher",
            404: "Upload not found",
        }
    )
    def update(self, request, *args, **kwargs):
        """Update an upload."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        Partially update an existing upload. Only the uploader or teachers can modify uploads.
        
        **Permissions:**
        - Requires authentication
        - Upload owner can update their own uploads (documented requirement)
        - Teachers can update any upload (documented requirement)
        """,
        request_body=UploadSerializer,
        responses={
            200: UploadSerializer(),
            400: "Bad Request - Invalid data",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Not the uploader or teacher",
            404: "Upload not found",
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update an upload."""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        Delete an upload. Only the uploader or teachers can delete uploads.
        
        **Permissions:**
        - Requires authentication
        - Upload owner can delete their own uploads (documented requirement)
        - Teachers can delete any upload (documented requirement)
        """,
        responses={
            204: "Upload deleted successfully",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Not the uploader or teacher",
            404: "Upload not found",
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an upload."""
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Handle upload creation with team validation and notifications."""
        team = serializer.validated_data.get('team')
        user = self.request.user
        
        upload = serializer.save(
            uploaded_by=user,
            metadata={
                "uploaded_by": user.id,
                "team": team.id,
                "updated_by": user.id
            }
        )
        notify_upload(user, team.id, upload.title)

    def perform_update(self, serializer):
        """Handle upload updates with permission validation."""
        user = self.request.user
        upload = self.get_object()
        
        # Get existing metadata or empty dict if None
        existing_metadata = upload.metadata or {}
        
        serializer.save(
            metadata={
                **existing_metadata,
                "updated_by": user.id,
            }
        )

    def perform_destroy(self, instance):
        """Handle upload deletion with permission validation."""
        super().perform_destroy(instance)

    @swagger_auto_schema(
        operation_description="""
        Add a comment to an upload.
        
        **Access Control:**
        - Students: Can comment on uploads from their teams
        - Teachers: Can comment on any upload
        
        **Permissions:**
        - Requires authentication
        - Access automatically filtered based on user role
        
        **Notifications:**
        - Upload owner will be notified of new comments (unless they are the commenter)
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Comment text content',
                    min_length=1,
                    max_length=1000
                )
            },
            example={'content': 'Great work on this document!'}
        ),
        responses={
            201: openapi.Response(
                description="Comment created successfully",
                schema=ResourceCommentSerializer()
            ),
            400: 'Bad Request - Content is required or invalid',
            401: "Unauthorized - Authentication required",
            403: 'Forbidden - Access denied',
            404: 'Upload not found'
        }
    )
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Add a comment to an upload."""
        upload = self.get_object()
        content = request.data.get('content')
        
        if not content or not content.strip():
            return Response(
                {'error': 'Comment content is required and cannot be empty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = ResourceComment.objects.create(
            upload=upload,
            author=request.user,
            content=content.strip()
        )

        # Notify the upload owner if they're not the commenter
        if upload.uploaded_by != request.user:
            NotificationService.create_and_send(
                recipient=upload.uploaded_by,
                content=f"New comment on your upload '{upload.title}' by {request.user.username}",
                notification_type="resource_comment",
                metadata={
                    "profile_picture": request.user.profile_picture_url,
                    "upload_id": upload.id,
                    "comment_id": comment.id
                }
            )
        
        serializer = ResourceCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
    permission_classes = [AllowAny]
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
        
class DefenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling defense-related operations.
    """
    queryset = Defense.objects.all()
    serializer_class = DefenseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StaticPagination

    def get_queryset(self):
        """
        Filter defenses based on user role:
        - Students see defenses for their teams
        - Teachers/jury members see defenses they're part of
        """
        user = self.request.user
        
        # Return all defenses for admin users
        if user.is_staff or user.is_superuser:
            return Defense.objects.all()
        
        # For normal users, filter based on their relation to defenses
        return Defense.objects.filter(
            # User is part of the team being evaluated
            Q(theme_assignment__team__members=user) |
            # User is part of the jury
            Q(jury=user)
        ).distinct()
        
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return DefenseSerializer
        elif self.action == 'update_documents':
            return DefenseSerializer
        elif self.action == 'update_results':
            return DefenseSerializer
        else:
            # For retrieve, create, update, partial_update
            return DefenseDetailSerializer

    @action(detail=True, methods=['patch'], permission_classes=[IsTeamOwner])
    def update_documents(self, request, pk=None):
        """
        Custom action for team owners to update document URIs.
        """
        defense = self.get_object()
        
        # Only allow updating specific fields
        allowed_fields = ['defense_uri', 'report_uri', 'specifications_document_uri']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(defense, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsJuryPresident])
    def update_results(self, request, pk=None):
        """
        Custom action for jury presidents to update results and grades.
        """
        defense = self.get_object()
        
        # Only allow updating specific fields
        allowed_fields = ['result', 'grade', 'status']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(defense, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Override update method to enforce field-level permissions
        """
        instance = self.get_object()
        user = request.user
        data = request.data.copy()
        
        # Check what fields are being updated and enforce permissions
        document_fields = ['defense_uri', 'report_uri', 'specifications_document_uri']
        result_fields = ['result', 'grade']
        
        has_document_fields = any(field in data for field in document_fields)
        has_result_fields = any(field in data for field in result_fields)
        
        # Check if user is team owner when updating document fields
        if has_document_fields and not IsTeamOwner().has_object_permission(request, self, instance):
            return Response(
                {"detail": "Only team owners can update document URIs."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is jury president when updating result fields
        if has_result_fields and not IsJuryPresident().has_object_permission(request, self, instance):
            return Response(
                {"detail": "Only jury presidents can update results and grades."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If all permission checks pass, proceed with update
        return super().update(request, *args, **kwargs)
