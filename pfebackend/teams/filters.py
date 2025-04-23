from django_filters import rest_framework as filters
from django.db.models import Count, F, Q
from teams.models import Team, TeamMembership

class TeamFilter(filters.FilterSet):
    """
    Comprehensive filter for Team objects.
    
    Provides filtering capabilities for all relevant Team attributes and 
    additional computed properties like membership status and capacity.
    """
    # Basic filters
    # name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    academic_year = filters.CharFilter()  # Changed from NumberFilter to CharFilter to match model field
    is_verified = filters.BooleanFilter()
    
    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Boolean filters
    is_member = filters.BooleanFilter(method='filter_is_member')
    has_capacity = filters.BooleanFilter(method='filter_has_capacity')
    is_owner = filters.BooleanFilter(method='filter_is_owner')
    match_student_profile = filters.BooleanFilter(method='filter_match_student_profile')
    
    # Member count filters
    min_members = filters.NumberFilter(method='filter_min_members')
    max_members = filters.NumberFilter(method='filter_max_members')
    maximum_size = filters.NumberFilter(field_name='maximum_members')
    
    class Meta:
        model = Team
        fields = [
            'name', 'description', 'academic_year', 'is_verified', 
            'created_after', 'created_before', 'updated_after', 'updated_before', 
            'is_member', 'has_capacity', 'is_owner', 'match_student_profile', 
            'min_members', 'max_members', 'maximum_size'
        ]
    
    def filter_is_member(self, queryset, name, value):
        """Filter for teams where the current user is a member"""
        user = self.request.user
        if value:
            return queryset.filter(members=user)
        return queryset.exclude(members=user)
    
    def filter_has_capacity(self, queryset, name, value):
        """Filter for teams with available capacity"""
        queryset = queryset.annotate(member_count=Count('members'))
        if value:
            return queryset.filter(member_count__lt=F('maximum_members'))
        return queryset.filter(member_count__gte=F('maximum_members'))
    
    def filter_is_owner(self, queryset, name, value):
        """Filter for teams where the current user is the owner"""
        user = self.request.user
        if value:
            return queryset.filter(
                teammembership__user=user, 
                teammembership__role=TeamMembership.ROLE_OWNER
            )
        return queryset.exclude(
            teammembership__user=user, 
            teammembership__role=TeamMembership.ROLE_OWNER
        )
        
    def filter_match_student_profile(self, queryset, name, value):
        """Filter for teams matching the user's student profile"""
        user = self.request.user
        if value and hasattr(user, 'student'):
            student = user.student
            # Only filtering by academic_year since academic_program was removed from Team model
            return queryset.filter(academic_year=student.current_year)
        return queryset
    
    
    
    def filter_min_members(self, queryset, name, value):
        """Filter for teams with at least this many members"""
        return queryset.annotate(member_count=Count('members')).filter(member_count__gte=value)
    
    def filter_max_members(self, queryset, name, value):
        """Filter for teams with at most this many members"""
        return queryset.annotate(member_count=Count('members')).filter(member_count__lte=value)