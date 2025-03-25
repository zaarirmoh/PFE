from django_filters import rest_framework as filters
from django.db.models import Q, F
from users.models import User

class StudentFilter(filters.FilterSet):
    enrollment_year = filters.NumberFilter(field_name="student__enrollment_year")
    academic_program = filters.CharFilter(field_name="student__academic_program")
    current_year = filters.NumberFilter(field_name="student__current_year")
    academic_status = filters.CharFilter(field_name="student__academic_status")
    speciality = filters.CharFilter(field_name="student__speciality")
    has_team = filters.BooleanFilter(method='filter_has_team')
    show_peers_only = filters.BooleanFilter(method='filter_peers_only')

    class Meta:
        model = User
        fields = ['enrollment_year', 'academic_program', 'current_year', 
                 'academic_status', 'speciality', 'has_team', 'show_peers_only']
    
    def filter_has_team(self, queryset, name, value):
        if value:
            return queryset.filter(
                teams__academic_year=F('student__current_year'),
                teams__academic_program=F('student__academic_program')
            ).distinct()
        else:
            return queryset.exclude(
                teams__academic_year=F('student__current_year'),
                teams__academic_program=F('student__academic_program')
            ).distinct()
        
    def filter_peers_only(self, queryset, name, value):
        # Only apply peer filtering if value is True
        if not value:
            return queryset
            
        request = self.request
        if not request or not request.user or request.user.user_type != 'student':
            return queryset
            
        # Get the student profile of the requesting user
        try:
            student = request.user.student
            # Filter to only show peers (same year and program)
            filtered_queryset = queryset.filter(
                student__current_year=student.current_year,
                student__academic_program=student.academic_program
            )
            # Exclude the requesting student
            filtered_queryset = filtered_queryset.exclude(id=request.user.id)
            return filtered_queryset
        except AttributeError:
            # If user doesn't have a student profile, return unfiltered
            return queryset


class TeacherFilter(filters.FilterSet):
    department = filters.CharFilter(field_name="teacher__department")
    grade = filters.CharFilter(field_name="teacher__grade")
    class Meta:
        model = User
        fields = ['department', 'grade']
