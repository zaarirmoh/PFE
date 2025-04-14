from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from themes.models.project_models import ThemeChoice, ThemeAssignment
from themes.serializers.theme_assignment_serializers import ThemeChoiceSerializer, ThemeAssignmentSerializer
from users.permissions import IsStudent, IsTeacher, IsAdministrator
from teams.permissions import IsTeamOwner
from teams.models import Team, TeamMembership

class ThemeChoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for teams to submit and manage their theme choices.
    """
    serializer_class = ThemeChoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['team', 'is_final']
    pagination_class = StaticPagination
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'administrator':
            return ThemeChoice.objects.all()
            
        elif user.user_type == 'teacher':
            return ThemeChoice.objects.all()  # This could be refined based on your team supervision model
            
        elif user.user_type == 'student':
            # Get teams where the student is a member
            user_teams = Team.objects.filter(
                teammember__user=user,
                teammember__status='accepted'
            )
            return ThemeChoice.objects.filter(team__in=user_teams)
            
        return ThemeChoice.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        team = serializer.validated_data.get('team')
        
        serializer.save()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsStudent(),IsTeamOwner()]
        elif self.action == 'destroy':
            return [permissions.IsAuthenticated(), IsAdministrator()]
        return [permissions.IsAuthenticated()]

class ThemeAssignmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for administrators to assign themes to teams.
    """
    queryset = ThemeAssignment.objects.all()
    serializer_class = ThemeAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StaticPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['team', 'theme']
    search_fields = ['team__name', 'theme__title', 'notes']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdministrator()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdministrator])
    def auto_assign(self, request):
        """
        Automatically assign themes to teams based on preferences.
        This is a simple implementation that could be enhanced with more 
        sophisticated algorithms.
        """
        # Get all teams with finalized choices
        choices = ThemeChoice.objects.filter(is_final=True)
        
        # Create a dict to track theme assignments
        assigned_themes = {}
        assigned_teams = {}
        
        # First pass: assign first choices where possible
        for choice in choices:
            team = choice.team
            rankings = choice.themeranking_set.all().order_by('rank')
            
            if not rankings:
                continue
                
            for ranking in rankings:
                theme = ranking.theme
                
                # Check if theme is still available
                if theme.id not in assigned_themes:
                    # Assign theme to team
                    assignment = ThemeAssignment.objects.create(
                        team=team,
                        theme=theme,
                        assigned_by=request.user,
                        notes=f"Auto-assigned (preference rank: {ranking.rank})"
                    )
                    
                    assigned_themes[theme.id] = team.id
                    assigned_teams[team.id] = theme.id
                    break
        
        # Return summary of assignments
        return Response({
            "message": f"Successfully assigned {len(assigned_teams)} themes to teams",
            "assignments": ThemeAssignmentSerializer(
                ThemeAssignment.objects.filter(assigned_by=request.user),
                many=True
            ).data
        })