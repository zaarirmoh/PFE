from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from themes.models.theme_models import Theme
from themes.serializers.theme_creation_serializers import ThemeSerializer
from users.permissions import IsTeacher
from common.pagination import StaticPagination

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
        - `academic_year` (int) - Filter by academic year.
        - `academic_program` (str) - Filter by academic program (`preparatory` / `superior`).
        - `specialty` (str) - Filter by specialty (`IASD`, `SIW`, `ISI`, `3CS`, `2CPI`).
        - `proposed_by` (int) - Filter by teacher who proposed the theme.
    """
    queryset = Theme.objects.all().order_by("-created_at")
    serializer_class = ThemeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "proposed_by"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]

    def get_permissions(self):
        """ Allow only teachers to create, update, or delete themes. """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

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
                "academic_year", openapi.IN_QUERY, description="Filter by academic year",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "academic_program", openapi.IN_QUERY, description="Filter by academic program",
                type=openapi.TYPE_STRING,
                enum=["preparatory", "superior"]
            ),
            openapi.Parameter(
                "specialty", openapi.IN_QUERY, description="Filter by specialty",
                type=openapi.TYPE_STRING,
                enum=["IASD", "SIW", "ISI", "3CS", "2CPI"]
            ),
            openapi.Parameter(
                "proposed_by", openapi.IN_QUERY, description="Filter by teacher ID who proposed the theme",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "search", openapi.IN_QUERY, description="Search themes by title or description",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "ordering", openapi.IN_QUERY, description="Order results by `created_at` or `title`",
                type=openapi.TYPE_STRING,
                enum=["created_at", "title"]
            ),
        ],
        responses={200: ThemeSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """ Retrieve a list of themes with filtering, searching, and ordering. """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific theme.",
        responses={200: ThemeSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """ Retrieve details of a specific theme. """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new theme. Only teachers can create themes.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["title", "specialty", "description", "tools", "academic_year", "academic_program"],
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, description="Title of the theme"),
                "co_supervisors": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="List of co-supervising teachers"
                ),
                "description": openapi.Schema(type=openapi.TYPE_STRING, description="Detailed description"),
                "tools": openapi.Schema(type=openapi.TYPE_STRING, description="Comma-separated list of tools used"),
                "documents": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="List of document IDs associated with the theme"
                ),
                "academic_year": openapi.Schema(type=openapi.TYPE_STRING, description="Academic year of the theme"),
            }
        ),
        responses={201: ThemeSerializer()}
    )
    def create(self, request, *args, **kwargs):
        """ Create a new theme (Teachers only). """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an existing theme. Only teachers can update themes.",
        request_body=ThemeSerializer,
        responses={200: ThemeSerializer()}
    )
    def update(self, request, *args, **kwargs):
        """ Update an existing theme (Teachers only). """
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a theme. Only teachers can update themes.",
        request_body=ThemeSerializer,
        responses={200: ThemeSerializer()}
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
