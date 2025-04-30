from django_filters import rest_framework as filters
from django.db.models import Q
from themes.models import ThemeAssignment

class ProjectListFilter(filters.FilterSet):
    """
    Filter class for ThemeAssignment (Project) listings.
    Provides filtering capabilities for projects/theme assignments based on various criteria.
    """
    academic_year = filters.CharFilter(field_name='team__academic_year')
    theme_id = filters.NumberFilter(field_name='theme__id')
    supervisor_id = filters.NumberFilter(method='filter_by_supervisor')
    team_id = filters.NumberFilter(field_name='team__id')
    member_id = filters.NumberFilter(method='filter_by_team_member')
    date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = ThemeAssignment
        fields = [
            'academic_year', 
            'theme_id', 
            'supervisor_id',
            'team_id',
            'member_id',
            'date_from',
            'date_to',
            'status'
        ]
    
    def filter_by_supervisor(self, queryset, name, value):
        """
        Filter projects by supervisor ID.
        Includes both main supervisors (theme proposers) and co-supervisors.
        """
        return queryset.filter(
            Q(theme__proposed_by__id=value) | 
            Q(theme__co_supervisors__id=value)
        ).distinct()
    
    def filter_by_team_member(self, queryset, name, value):
        """
        Filter projects by team member ID.
        Returns projects where the specified user is a member of the team.
        """
        return queryset.filter(
            team__teammembership_set__user__id=value
        ).distinct()