from django_filters import rest_framework as filters
from django.db.models import Q
from themes.models import Theme, ThemeAssignment
from teams.models import Team

class ThemeFilter(filters.FilterSet):
    """
    Comprehensive filter for Theme objects.
    
    Provides filtering capabilities for all relevant Theme attributes and 
    additional computed properties like supervision status and team assignments.
    """
    # Basic filters
    title = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    academic_year = filters.CharFilter()
    
    # Proposer and supervisor filters
    proposed_by = filters.NumberFilter(field_name='proposed_by__id')
    co_supervised_by = filters.NumberFilter(field_name='co_supervisors__id', distinct=True)
    
    # Team filters
    team_id = filters.NumberFilter(method='filter_by_team')
    
    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Boolean filters
    is_member = filters.BooleanFilter(method='filter_by_team_membership')
    is_supervisor = filters.BooleanFilter(method='filter_by_supervision')
    is_assigned = filters.BooleanFilter(method='filter_is_assigned')
    is_verified = filters.BooleanFilter(field_name='is_verified')
    
    class Meta:
        model = Theme
        fields = [
            'title', 'description', 'academic_year', 'proposed_by', 'co_supervised_by',
            'team_id', 'created_after', 'created_before', 'updated_after', 'updated_before',
            'is_member', 'is_supervisor', 'is_assigned', 'is_verified'
        ]
    
    def filter_by_team(self, queryset, name, value):
        """Filter themes by a specific team ID"""
        try:
            team = Team.objects.get(id=value)
            # Get theme assigned to this team through ThemeAssignment
            theme_ids = ThemeAssignment.objects.filter(team=team).values_list('theme_id', flat=True)
            return queryset.filter(id__in=theme_ids)
        except Team.DoesNotExist:
            return queryset.none()
    
    # def filter_by_team_membership(self, queryset, name, value):
    #     user = self.request.user
    
    # # Find teams where this user is a member through TeamMembership
    #     teams = Team.objects.filter(teammembership__user=user)
    
    # # Return themes that are assigned to these teams
    #     return queryset.filter(assigned_teams__in=teams).distinct()
    def filter_by_team_membership(self, queryset, name, value):
        user = self.request.user
    
    # Find teams where this user is a member through TeamMembership
        teams = Team.objects.filter(teammembership__user=user)
    
    # Get team IDs
        team_ids = teams.values_list('id', flat=True)
    
    # Filter themes that are assigned to any of these teams through ThemeAssignment
        return queryset.filter(assigned_teams__team__id__in=team_ids)
    
    def filter_by_supervision(self, queryset, name, value):
        """Filter themes that the current user (teacher) proposes or co-supervises"""
        user = self.request.user
        if not user.is_authenticated or user.user_type != "teacher":
            return queryset.none()
            
        if value:
            # Get themes where the teacher is proposer or co-supervisor
            return queryset.filter(
                Q(proposed_by=user) | Q(co_supervisors=user)
            ).distinct()
        
        # If is_supervisor=false, return themes NOT supervised by the user
        return queryset.exclude(
            Q(proposed_by=user) | Q(co_supervisors=user)
        )
    
    def filter_is_assigned(self, queryset, name, value):
        """Filter themes based on whether they are assigned to any team"""
        assigned_theme_ids = ThemeAssignment.objects.values_list('theme_id', flat=True)
        
        if value:
            return queryset.filter(id__in=assigned_theme_ids)
        
        return queryset.exclude(id__in=assigned_theme_ids)