from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from users.serializers.user import CustomUserSerializer
from common.pagination import StaticPagination
from .filters import StudentFilter, TeacherFilter

User = get_user_model()

class BaseUserListView(generics.ListAPIView):
    """
    Base view for user listing with common configurations
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get_queryset(self):
        """
        Abstract method to be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_queryset")
    
    def get_filterset_context(self):
        """
        Pass the request to the filterset for user-context aware filtering
        """
        context = super().get_filterset_context()
        context['request'] = self.request
        return context


class StudentListView(BaseUserListView):
    """
    API endpoint to retrieve all students.
    Supports filtering, searching, and ordering.
    """
    filterset_class = StudentFilter
    search_fields = ['first_name', 'last_name', 'email', 'username', 'student__matricule']
    ordering_fields = ['last_name', 'first_name', 'student__enrollment_year', 'student__current_year']
    
    def get_queryset(self):
        return User.objects.filter(user_type='student').select_related('student')
    
class TeacherListView(BaseUserListView):
    """
    API endpoint to retrieve all teachers.
    Supports filtering, searching, and ordering.
    """
    filterset_class = TeacherFilter
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['last_name', 'first_name', 'email']
    
    def get_queryset(self):
        return User.objects.filter(user_type='teacher').select_related('teacher')