import uuid
from rest_framework import permissions, filters
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from teams.models import Team
from teams.serializers import TeamSerializer
from teams.permissions import IsTeamMember, IsTeamOwner
from teams.services import TeamService
from notifications.services import NotificationService
from common.pagination import StaticPagination
from users.permissions import IsStudent
from django_filters.rest_framework import DjangoFilterBackend
from teams.filters import TeamFilter

class TeamListCreateView(ListCreateAPIView):
    """
    List and create teams with comprehensive filtering.
    
    ## Endpoints
    GET /api/teams/ - List teams with filtering options
    POST /api/teams/ - Create a new team (creator becomes owner)
    
    ## Query Parameters
    - Basic filters:
        - `description` - Filter by description (contains, case-insensitive)
        - `academic_year` - Filter by academic year
        - `academic_program` - Filter by academic program
    
    - Date filters:
        - `created_after` - Teams created after specified date (YYYY-MM-DD)
        - `created_before` - Teams created before specified date (YYYY-MM-DD)
        - `updated_after` - Teams updated after specified date (YYYY-MM-DD)
        - `updated_before` - Teams updated before specified date (YYYY-MM-DD)
    
    - Boolean filters:
        - `is_verified` - Filter by verification status (true/false)
        - `is_member` - Teams where current user is a member (true/false)
        - `has_capacity` - Teams with capacity for more members (true/false)
        - `is_owner` - Teams where current user is the owner (true/false)
        - `match_student_profile` - Teams matching current user's academic year and program (true/false)
    
    - Member count filters:
        - `min_members` - Teams with at least this many members
        - `max_members` - Teams with at most this many members
        - `maximum_size` - Filter by team's maximum allowed size
    
    - Pagination:
        - `page` - Page number
        - `page_size` - Number of results per page
    
    - Sorting:
        - `ordering` - Sort by field (prefix with - for descending)
          Examples: ordering=name, ordering=-created_at
    
    - Searching:
        - `search` - Search in name and description
    """
    serializer_class = TeamSerializer
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TeamFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'academic_year']
    ordering = ['name']
    
    def get_permissions(self):
        """
        Apply IsStudent permission only for POST requests.
        """
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """Return teams with proper filtering and optimal performance"""
        queryset = Team.objects.all()
        # .prefetch_related('members', 'teammembership_set')
        return queryset

    
    def perform_create(self, serializer):
        """Create a new team with the current user as owner"""
        try:
            # generated_name = str(uuid.uuid4())
                
            # Use TeamService to create the team
            team = TeamService.create_team_with_auto_name(
                description=serializer.validated_data.get('description', ''),
                owner=self.request.user
            )
            
            # Set serializer instance for proper response
            serializer.instance = team
            
        except DjangoValidationError as e:
            raise ValidationError({'detail': e.message})
        


class TeamDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a team
    
    GET /api/teams/{id}/ - View team details (members only)
    PUT/PATCH /api/teams/{id}/ - Update team (owners only)
    DELETE /api/teams/{id}/ - Delete team (owners only)
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_permissions(self):
        """Use different permission classes based on the request method"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsTeamOwner()]
        return super().get_permissions()

    def perform_update(self, serializer):
        """Update team and create notification if name changed"""
        team = self.get_object()
        TeamService.update_team(
            team=team,
            user=self.request.user,
            **serializer.validated_data
        )

    def perform_destroy(self, instance):
        """Delete team and create notification"""
        team = self.get_object()
        TeamService.delete_team(team, self.request.user)