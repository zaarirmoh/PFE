from rest_framework import generics, filters, status
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from users.serializers.user import CustomUserSerializer
from common.pagination import StaticPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .filters import StudentFilter, TeacherFilter, ExternalUserFilter
from .serializers import CustomUserSerializer
from documents.models import DocumentType
from documents.serializers import DocumentSerializer
from .models import StudentSkill, Student
from .permissions import IsStudent
from .serializers import StudentSkillSerializer

User = get_user_model()

class BaseUserListView(generics.ListAPIView):
    """
    Base view for user listing with common configurations.
    
    Provides core functionality for user listing endpoints including:
    - Authentication requirements
    - Pagination
    - Filtering
    - Search capabilities
    - Ordering options
    
    All user list views should inherit from this base class to ensure
    consistent implementation and behavior.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get_queryset(self):
        """
        Abstract method to be implemented by subclasses.
        
        Each subclass must define its own queryset based on
        the specific user type it represents.
        """
        raise NotImplementedError("Subclasses must implement get_queryset")
    
    def get_filterset_context(self):
        """
        Pass the request to the filterset for user-context aware filtering.
        
        This allows filters to access the current user's information
        when applying user-relative filters (e.g., 'show only my peers').
        """
        context = super().get_filterset_context()
        context['request'] = self.request
        return context

class StudentListView(BaseUserListView):
    """
    API endpoint to retrieve and filter student users.
    
    ## Endpoint
    GET /api/users/students/ - List students with comprehensive filtering options
    
    ## Query Parameters
    - Student-specific filters:
        - `enrollment_year` - Filter by year of admission (e.g., 2014)
        - `current_year` - Filter by current year in program ('2', '3', '4siw', '4isi', etc.)
        - `academic_status` - Filter by status ('active', 'on_leave', 'graduated')
        - `has_team` - Filter by team membership status (true/false)
        - `show_peers_only` - Show only students in same year as current user (true/false)
    
    - Searching:
        - `search` - Search in first name, last name, email, username, and matricule
    
    - Sorting:
        - `ordering` - Sort by field (prefix with - for descending)
          Examples: ordering=last_name, ordering=-student__enrollment_year
          Available fields: last_name, first_name, student__enrollment_year, student__current_year
    
    - Pagination:
        - `page` - Page number
        - `page_size` - Number of results per page
    
    ## Authentication
    - User must be authenticated to access this endpoint
    """
    filterset_class = StudentFilter
    search_fields = ['first_name', 'last_name', 'email', 'username', 'student__matricule',
        'student__skills__name']
    ordering_fields = ['last_name', 'first_name', 'student__enrollment_year', 'student__current_year']
    
    def get_queryset(self):
        """
        Return queryset of all student users with their student profile loaded.
        
        Uses select_related to optimize database queries by fetching
        the related student profile in the same query.
        """
        return User.objects.filter(user_type='student').select_related('student')

class TeacherListView(BaseUserListView):
    """
    API endpoint to retrieve and filter teacher users.
    
    ## Endpoint
    GET /api/users/teachers/ - List teachers with filtering options
    
    ## Query Parameters
    - Teacher-specific filters:
        - `department` - Filter by academic department
        - `grade` - Filter by teacher grade (e.g., 'professeur', 'maitre_assistant_a')
    
    - Searching:
        - `search` - Search in first name, last name, email, and username
    
    - Sorting:
        - `ordering` - Sort by field (prefix with - for descending)
          Examples: ordering=last_name, ordering=-email
          Available fields: last_name, first_name, email
    
    - Pagination:
        - `page` - Page number
        - `page_size` - Number of results per page
    
    ## Authentication
    - User must be authenticated to access this endpoint
    """
    filterset_class = TeacherFilter
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['last_name', 'first_name', 'email', 'teacher__grade']
    
    def get_queryset(self):
        """
        Return queryset of all teacher users with their teacher profile loaded.
        
        Uses select_related to optimize database queries by fetching
        the related teacher profile in the same query.
        """
        return User.objects.filter(user_type='teacher').select_related('teacher')
    
class ExternalUserListView(BaseUserListView):
    """
    API endpoint to retrieve and filter external users.
    
    ## Endpoint
    GET /api/users/external_users/ - List external users with filtering options
    
    ## Query Parameters
    - ExternalUser-specific filters:
        - `external_user_type` - Filter by teacher grade (e.g., 'professeur', 'maitre_assistant_a')
    
    - Searching:
        - `search` - Search in first name, last name, email, and username
    
    - Sorting:
        - `ordering` - Sort by field (prefix with - for descending)
          Examples: ordering=last_name, ordering=-email
          Available fields: last_name, first_name, email
    
    - Pagination:
        - `page` - Page number
        - `page_size` - Number of results per page
    
    ## Authentication
    - User must be authenticated to access this endpoint
    """
    filterset_class = ExternalUserFilter
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['last_name', 'first_name', 'email', 'external_user__external_user_type']
    
    def get_queryset(self):
        """
        Return queryset of all teacher users with their teacher profile loaded.
        
        Uses select_related to optimize database queries by fetching
        the related teacher profile in the same query.
        """
        return User.objects.filter(user_type='external_user').select_related('external_user')
    
class ProfilePictureUpdateView(generics.CreateAPIView):
    """
    API endpoint to update a user's profile picture.

    ## Endpoint
    POST /api/users/profile-picture/

    ## Request
    - Requires authentication
    - Supports multipart/form-data file upload
    - File field should be named 'file'

    ## Responses
    - 201 Created: Profile picture successfully uploaded
    - 400 Bad Request: Invalid input
    """
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = DocumentSerializer

    def create(self, request, *args, **kwargs):
        # Check if file is present in the request
        if 'file' not in request.FILES:
            return Response(
                {"error": "No profile picture file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare data for serializer
        data = {
            'document_type': DocumentType.PROFILE_PICTURE,
            'title': f"Profile Picture for {request.user.username}",
            'file': request.FILES['file']
        }
        
        # Use serializer for validation and creation
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Save the document and set the creator
        document = serializer.save(created_by=request.user)
        
        # Update user's profile picture URL if needed
        request.user.profile_picture_url = document.file.url
        request.user.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProfileListView(generics.ListAPIView):
    """
    API view that lists all user profiles.
    
    Only authenticated users can access this endpoint.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['last_name', 'first_name', 'email']
    ordering = ['last_name']
    permission_classes = [IsAuthenticated]


class UserProfileRetrieveView(generics.RetrieveAPIView):
    """
    API view that retrieves a specific user profile by ID.
    
    Only authenticated users can access this endpoint.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
class StudentSkillCreateView(generics.CreateAPIView):
    """
    View for creating a new skill for a student
    """
    serializer_class = StudentSkillSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get_student(self):
        student_id = self.kwargs.get('id')
        try:
            return Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise NotFound("Student not found")
    
    def check_object_permissions(self, request, student):
        # Check if user is adding skills to their own profile
        if request.user != student.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to add skills to this student")
        return super().check_object_permissions(request, student)
    
    def perform_create(self, serializer):
        student = self.get_student()
        self.check_object_permissions(self.request, student)
        serializer.save(student=student)


class StudentSkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating, and deleting a student's skill
    """
    serializer_class = StudentSkillSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    lookup_url_kwarg = 'skill_id'

    def get_queryset(self):
        student_id = self.kwargs.get('id')
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise NotFound("Student not found")
        
        # Check if user is allowed
        if self.request.user != student.user and not self.request.user.is_staff:
            raise PermissionDenied("You don't have permission to modify skills for this student")
        
        return StudentSkill.objects.filter(student=student)
    