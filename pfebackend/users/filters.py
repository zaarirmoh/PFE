from django_filters import rest_framework as filters
from django.db.models import Q, F
from users.models import User, StudentSkill


class StudentSkillFilter(filters.FilterSet):
    skill_name = filters.CharFilter(field_name='name')
    proficiency_level = filters.CharFilter(field_name='proficiency_level')

    class Meta:
        model = StudentSkill
        fields = ['skill_name', 'proficiency_level']
        
class StudentFilter(filters.FilterSet):
    enrollment_year = filters.NumberFilter(field_name="student__enrollment_year")
    current_year = filters.CharFilter(field_name="student__current_year")
    academic_status = filters.CharFilter(field_name="student__academic_status")
    has_team = filters.BooleanFilter(method='filter_has_team')
    show_peers_only = filters.BooleanFilter(method='filter_peers_only')
    
    # skill_name = filters.CharFilter(method='filter_by_skill_name')
    # skill_proficiency = filters.CharFilter(method='filter_by_skill_proficiency')

    class Meta:
        model = User
        fields = ['enrollment_year', 'current_year', 
                 'academic_status', 'has_team', 'show_peers_only']
        
    # def filter_by_skill_name(self, queryset, name, value):
    #     return queryset.filter(skills__name__icontains=value)
    
    # def filter_by_skill_proficiency(self, queryset, name, value):
    #     return queryset.filter(skills__proficiency_level=value)
    
    def filter_has_team(self, queryset, name, value):
        if value:
            return queryset.filter(
                teams__academic_year=F('student__current_year')
            ).distinct()
        else:
            return queryset.exclude(
                teams__academic_year=F('student__current_year')
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
            # Filter to only show peers (same year)
            filtered_queryset = queryset.filter(
                student__current_year=student.current_year
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
        
class ExternalUserFilter(filters.FilterSet):
    external_user_type = filters.CharFilter(field_name="external_user__external_user_type")
    class Meta:
        model = User
        fields = ['external_user_type']
