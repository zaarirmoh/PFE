from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from users.permissions import IsStudent
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from timelines.models import Timeline
from timelines.serializers import TimelineSerializer
from timelines.filters import TimelineFilter

class TimelineListView(ListAPIView):
    queryset = Timeline.objects.all()
    serializer_class = TimelineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TimelineFilter
    search_fields = ["name", "description", "slug"]
    ordering_fields = ["start_date", "end_date", "academic_year", "academic_program"]
    ordering = ["academic_program", "academic_year", "start_date"]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Filter by name (contains)", type=openapi.TYPE_STRING),
            openapi.Parameter('slug', openapi.IN_QUERY, description="Filter by slug (exact match)", type=openapi.TYPE_STRING),
            openapi.Parameter('description', openapi.IN_QUERY, description="Filter by description content", type=openapi.TYPE_STRING),
            openapi.Parameter('academic_year', openapi.IN_QUERY, description="Filter by academic year", type=openapi.TYPE_INTEGER),
            openapi.Parameter('academic_program', openapi.IN_QUERY, description="Filter by academic program (preparatory/superior)", type=openapi.TYPE_STRING),
            openapi.Parameter('timeline_type', openapi.IN_QUERY, description="Filter by timeline type (groups/themes/work/soutenance)", type=openapi.TYPE_STRING),
            openapi.Parameter('start_date_after', openapi.IN_QUERY, description="Filter by start date after", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('start_date_before', openapi.IN_QUERY, description="Filter by start date before", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('end_date_after', openapi.IN_QUERY, description="Filter by end date after", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('end_date_before', openapi.IN_QUERY, description="Filter by end date before", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active flag", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_current', openapi.IN_QUERY, description="Filter currently active timelines", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by timeline status (upcoming/active/expired/inactive)", type=openapi.TYPE_STRING),
            openapi.Parameter('match_student', openapi.IN_QUERY, description="Match timelines to user's student profile", type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: TimelineSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of timelines with enhanced filtering options.
        
        ## Endpoints
        GET /api/timelines/ - List teams with filtering options
        
        ## Query Parameters
        - Basic fields:
            - `name` (str) → Filter by name (contains match)
            - `slug` (str) → Filter by slug (exact match)
            - `description` (str) → Filter by description content
            - `academic_year` (int) → Filter by academic year
            - `academic_program` (str) → Filter by program (e.g., "preparatory", "superior")
            - `timeline_type` (str) → Filter by type (e.g., "groups", "themes")
        
        - Date range filters:
            - `start_date_after` (datetime) → Filter by start date after this time
            - `start_date_before` (datetime) → Filter by start date before this time
            - `end_date_after` (datetime) → Filter by end date after this time
            - `end_date_before` (datetime) → Filter by end date before this time
        
        - Status filters:
            - `is_active` (bool) → Filter by active flag
            - `is_current` (bool) → Filter currently active timelines by date range
            - `status` (str) → Filter by computed status ("active", "expired", "upcoming", "inactive")
        
        - Student matching:
            - `match_student` (bool) → Filter to match authenticated student's profile
        """
        return super().get(request, *args, **kwargs)
    
class MyTimelinesView(ListAPIView):
    """
    Get timelines relevant to the authenticated student.
    
    Returns timelines matching the student's academic program and year.
    """
    serializer_class = TimelineSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    
    @swagger_auto_schema(
        responses={
            200: TimelineSerializer(many=True),
            403: "You must be logged in as a student to use this endpoint."
        }
    )
    
    def get_queryset(self):
        student = self.request.user.student
        return Timeline.objects.filter(
            academic_program=student.academic_program,
            academic_year=student.current_year,
            is_active=True
        )