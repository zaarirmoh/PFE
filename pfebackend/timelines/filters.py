from django_filters import rest_framework as filters
from django.utils.timezone import now
from django.db.models import Q
from timelines.models import Timeline

class TimelineFilter(filters.FilterSet):
    """
    Filter class for Timeline model with comprehensive filtering options.
    
    Includes filters for all relevant Timeline fields and computed properties,
    with special filters for matching student profiles and timeline status.
    """
    # Basic field filters
    name = filters.CharFilter(lookup_expr='icontains')
    slug = filters.CharFilter(lookup_expr='iexact')
    description = filters.CharFilter(lookup_expr='icontains')
    academic_year = filters.NumberFilter()
    academic_program = filters.CharFilter(lookup_expr='iexact')
    timeline_type = filters.CharFilter(lookup_expr='iexact')
    
    # Date range filters
    start_date_after = filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = filters.DateTimeFilter(field_name='start_date', lookup_expr='lte')
    end_date_after = filters.DateTimeFilter(field_name='end_date', lookup_expr='gte')
    end_date_before = filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
    
    # Boolean filters
    is_active = filters.BooleanFilter()
    is_current = filters.BooleanFilter(method='filter_is_current')
    
    # Status filter (computed property)
    status = filters.CharFilter(method='filter_by_status')
    
    # Student profile matching filter
    match_student = filters.BooleanFilter(method='filter_match_student')

    class Meta:
        model = Timeline
        fields = [
            'name', 'slug', 'description', 'academic_year', 'academic_program', 
            'timeline_type', 'is_active', 'is_current', 'status',
            'start_date_after', 'start_date_before', 
            'end_date_after', 'end_date_before',
            'match_student'
        ]

    def filter_is_current(self, queryset, name, value):
        """
        Filter timelines based on whether they are currently active by date.
        
        Args:
            queryset: The initial queryset
            name: The filter name
            value: Boolean value indicating desired filter state
            
        Returns:
            Filtered queryset
        """
        current_time = now()
        
        # For timelines with both start and end dates
        with_dates_q = (
            Q(start_date__lte=current_time) & 
            Q(end_date__gte=current_time)
        )
        
        # For timelines with only start date (open-ended)
        start_only_q = (
            Q(start_date__lte=current_time) & 
            Q(end_date__isnull=True)
        )
        
        if value:
            return queryset.filter(is_active=True).filter(with_dates_q | start_only_q)
        else:
            return queryset.exclude(is_active=True).exclude(with_dates_q | start_only_q)

    def filter_by_status(self, queryset, name, value):
        """
        Filter timelines by status (upcoming, active, expired, inactive).
        
        Args:
            queryset: The initial queryset
            name: The filter name
            value: The status to filter by
            
        Returns:
            Filtered queryset
        """
        current_time = now()
        
        if value == 'upcoming':
            return queryset.filter(is_active=True, start_date__gt=current_time)
        elif value == 'active':
            return queryset.filter(
                is_active=True,
                start_date__lte=current_time
            ).filter(
                Q(end_date__gte=current_time) | 
                Q(end_date__isnull=True)
            )
        elif value == 'expired':
            return queryset.filter(is_active=True, end_date__lt=current_time)
        elif value == 'inactive':
            return queryset.filter(is_active=False)
        
        return queryset

    def filter_match_student(self, queryset, name, value):
        """
        Filter timelines to match the authenticated student's profile.
        
        Args:
            queryset: The initial queryset
            name: The filter name
            value: Boolean value indicating whether to apply the filter
            
        Returns:
            Filtered queryset matching student's academic profile
        """
        if not value:
            return queryset
            
        user = getattr(self.request, 'user', None)
        
        # If not authenticated or not a student, return empty queryset
        if not user or not user.is_authenticated or not hasattr(user, 'student'):
            return queryset.none()
            
        student = user.student
        
        # Filter by student's academic program and current year
        return queryset.filter(
            academic_program=student.academic_program,
            academic_year=student.current_year
        )