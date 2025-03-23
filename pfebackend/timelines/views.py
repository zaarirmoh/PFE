from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from timelines.models import Timeline
from timelines.serializers import TimelineSerializer
from timelines.filters import TimelineFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class TimelineListView(ListAPIView):
    """
    Retrieve a list of timelines with filtering options.

    Filters:
    - `academic_year` (int) → Filter by academic year
    - `specialty` (str) → Filter by specialty
    - `academic_program` (str) → Filter by program (e.g., "preparatory", "superior")
    - `status` (str) → Filter by status ("active", "expired", "upcoming")
    """
    queryset = Timeline.objects.all()
    serializer_class = TimelineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TimelineFilter
    search_fields = ["name", "description"]
    ordering_fields = ["start_date", "end_date"]
    ordering = ["start_date"]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('academic_year', openapi.IN_QUERY, description="Filter by academic year", type=openapi.TYPE_INTEGER),
            openapi.Parameter('specialty', openapi.IN_QUERY, description="Filter by specialty", type=openapi.TYPE_STRING),
            openapi.Parameter('academic_program', openapi.IN_QUERY, description="Filter by academic program (preparatory/superior)", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by timeline status (upcoming, active, expired)", type=openapi.TYPE_STRING),
        ],
        responses={200: TimelineSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """Retrieve timelines with optional filtering."""
        return super().get(request, *args, **kwargs)

