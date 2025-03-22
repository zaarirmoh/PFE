from django_filters import rest_framework as filters
from timeline.models import Timeline
from django.utils.timezone import now

class TimelineFilter(filters.FilterSet):
    academic_year = filters.NumberFilter()
    specialty = filters.CharFilter(lookup_expr="iexact")
    academic_program = filters.CharFilter(lookup_expr="iexact")
    is_active = filters.BooleanFilter(method="filter_is_active")
    status = filters.CharFilter(method="filter_by_status")

    class Meta:
        model = Timeline
        fields = ['academic_year', 'specialty', 'academic_program', 'status', 'is_active']

    def filter_is_active(self, queryset, name, value):
        """Filters active timelines (current date within start and end date)."""
        if value:
            return queryset.filter(start_date__lte=now(), end_date__gte=now())
        return queryset.exclude(start_date__lte=now(), end_date__gte=now())

    def filter_by_status(self, queryset, name, value):
        """Filter by the dynamically computed `status` field."""
        return queryset.filter(status=value)
