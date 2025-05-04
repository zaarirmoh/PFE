from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from themes.models.theme_models import Theme
from themes.serializers.theme_creation_serializers import ThemeInputSerializer, ThemeOutputSerializer
from users.permissions import IsTeacher, IsExternalUser
from common.pagination import StaticPagination
from themes.filters import ThemeFilter

class ThemeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing themes.

    Available actions:
        - `list` (GET) - Retrieve all themes.
        - `retrieve` (GET) - Retrieve a specific theme.
        - `create` (POST) - Create a new theme (Teachers only).
        - `update` (PUT/PATCH) - Update a theme (Teachers only).
        - `destroy` (DELETE) - Delete a theme (Teachers only).

    Filters:
        - `title` (str) - Filter by title (case-insensitive, partial match).
        - `description` (str) - Filter by description (case-insensitive, partial match).  
        - `academic_year` (str) - Filter by academic year.
        - `proposed_by` (int) - Filter by teacher ID who proposed the theme.
        - `co_supervised_by` (int) - Filter by co-supervisor ID.
        - `team_id` (int) - Filter by team ID to get themes assigned to that team.
        - `is_member` (bool) - For students: filter to show only themes assigned to teams they are members of.
        - `is_supervisor` (bool) - For teachers: filter to show only themes they propose or co-supervise.
        - `is_assigned` (bool) - Filter to show only themes that are assigned to any team.
        - `created_after`, `created_before`, `updated_after`, `updated_before` (datetime) - Filter by creation/update date.
        - `is_verified` (bool) - Filter by verification status.
    """
    queryset = Theme.objects.all().order_by("-created_at")

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StaticPagination
    filterset_class = ThemeFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]

    def get_permissions(self):
        """ Allow only teachers to create, update, or delete themes. """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [(permissions.IsAuthenticated & (IsTeacher | IsExternalUser))()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ThemeInputSerializer
        return ThemeOutputSerializer  

    def get_serializer_context(self):
        """
        Pass the request to the serializer context.
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(
        operation_description="Retrieve a list of themes with filtering, searching, and ordering.",
        manual_parameters=[
            openapi.Parameter(
                "title", openapi.IN_QUERY, description="Filter by title (case-insensitive, partial match)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "description", openapi.IN_QUERY, description="Filter by description (case-insensitive, partial match)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "academic_year", openapi.IN_QUERY, description="Filter by academic year",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "proposed_by", openapi.IN_QUERY, description="Filter by teacher ID who proposed the theme",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "co_supervised_by", openapi.IN_QUERY, description="Filter by co-supervisor ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "team_id", openapi.IN_QUERY, description="Filter by team ID to get themes assigned to that team",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "is_member", openapi.IN_QUERY, description="For students: filter to show only themes assigned to teams they are members of",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                "is_supervisor", openapi.IN_QUERY, description="For teachers: filter to show only themes they propose or co-supervise",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                "is_assigned", openapi.IN_QUERY, description="Filter to show only themes that are assigned to any team",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                "created_after", openapi.IN_QUERY, description="Filter themes created after this datetime",
                type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                "created_before", openapi.IN_QUERY, description="Filter themes created before this datetime",
                type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                "search", openapi.IN_QUERY, description="Search themes by title or description",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "ordering", openapi.IN_QUERY, description="Order results by `created_at` or `title`",
                type=openapi.TYPE_STRING,
                enum=["created_at", "-created_at", "title", "-title"]
            ),
            openapi.Parameter(
                "page", openapi.IN_QUERY, description="Page number for pagination",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "page_size", openapi.IN_QUERY, description="Number of results per page",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "is_verified", openapi.IN_QUERY, description="Filter by verification status",
                type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={200: ThemeOutputSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """ Retrieve a list of themes with filtering, searching, and ordering. """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific theme.",
        responses={200: ThemeOutputSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """ Retrieve details of a specific theme. """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new theme. Only teachers can create themes.",
        request_body=ThemeInputSerializer,
        responses={201: ThemeOutputSerializer()}
    )
    def create(self, request, *args, **kwargs):
        """ Create a new theme (Teachers only). """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an existing theme. Only teachers can update themes.",
        request_body=ThemeInputSerializer,
        responses={200: ThemeOutputSerializer()}
    )
    def update(self, request, *args, **kwargs):
        """ Update an existing theme (Teachers only). """
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a theme. Only teachers can update themes.",
        request_body=ThemeInputSerializer,
        responses={200: ThemeOutputSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        """ Partially update a theme (Teachers only). """
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a theme. Only teachers can delete themes.",
        responses={204: "No Content"}
    )
    def destroy(self, request, *args, **kwargs):
        """ Delete a theme (Teachers only). """
        return super().destroy(request, *args, **kwargs)