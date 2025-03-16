from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from users.models import Student
from users.serializers.user import CustomUserSerializer
from common.pagination import StaticPagination
from django.db.models import Q


User = get_user_model()

class StudentListView(generics.ListAPIView):
    """
    API endpoint to retrieve all students.
    Supports filtering, searching, and ordering.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username', 'student__matricule']
    ordering_fields = ['last_name', 'first_name', 'student__enrollment_year', 'student__current_year']
    
    def get_queryset(self):
        queryset = User.objects.filter(user_type='student').select_related('student')
        
        filters = Q()
        
        filter_mapping = {
            'enrollment_year': 'student__enrollment_year',
            'academic_program': 'student__academic_program',
            'current_year': 'student__current_year',
            'academic_status': 'student__academic_status',
            'speciality': 'student__speciality',
        }
        
        # Dynamically build the Q object
        for param, field in filter_mapping.items():
            value = self.request.query_params.get(param)
            if value:
                filters &= Q(**{field: value})
        
        # Apply the filters to the queryset
        queryset = queryset.filter(filters)
        
        has_no_team = self.request.query_params.get('has_no_team')
        if has_no_team and has_no_team.lower() in ['true', '1', 'yes']:
            queryset = queryset.exclude(teams__isnull=False)

            
        return queryset
    
class TeacherListView(generics.ListAPIView):
    """
    API endpoint to retrieve all teachers.
    Supports filtering, searching, and ordering.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['last_name', 'first_name', 'email']
    
    def get_queryset(self):
        queryset = User.objects.filter(user_type='teacher').select_related('teacher')
        
        # Filter by department if provided
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(teacher__department=department)
            
        return queryset
