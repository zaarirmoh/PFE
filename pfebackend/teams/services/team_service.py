from teams.models import Team, TeamMembership
from notifications.services import NotificationService

class TeamService:
    """Service class for team-related operations"""
    
    @staticmethod
    def create_team(name, description, owner):
        """
        Create a new team with the given owner
        
        Args:
            name: Team name
            description: Team description
            owner: User who will be the team owner
            
        Returns:
            Team: The created team instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Use the model's factory method instead of manual creation
        team = Team.create_team(owner, name, description)
        
        NotificationService.create_and_send(
                recipient=owner,
                title="Team Created",
                content=f"You created the team '{team.name}'",
                notification_type='team_update',
                related_object=team,
                priority='low',
                metadata={
                    'team_id': team.id,
                    'event_type': 'team_created'
                }
            )
        return team
    
    @staticmethod
    def update_team(team, user, **update_data):
        """
        Update a team with the given data
        
        Args:
            team: Team instance to update
            user: User performing the update
            update_data: Data to update (name, description)
            
        Returns:
            Team: The updated team instance
        """
        old_name = team.name
        
        # Update fields
        if 'name' in update_data:
            team.name = update_data['name']
        if 'description' in update_data:
            team.description = update_data['description']
            
        team.updated_by = user
        team.save()
        
        # Send notification if name changed
        if old_name != team.name:
            NotificationService.create_and_send(
                recipient=user,
                title="Team Updated",
                content=f"Team name changed from '{old_name}' to '{team.name}'",
                notification_type='team_update',
                related_object=team,
                priority='medium',
                metadata={
                    'team_id': team.id,
                    'old_name': old_name,
                    'new_name': team.name,
                    'event_type': 'team_renamed'
                }
            )
        
        return team

    
    @staticmethod
    def delete_team(team, user):
        """
        Delete a team and notify the user
        
        Args:
            team: Team instance to delete
            user: User performing the deletion
        """
        team_name = team.name
        team_id = team.id
        team.delete()
        
        # Send notification
        NotificationService.create_and_send(
            recipient=user,
            title="Team Deleted",
            content=f"Team '{team_name}' was deleted",
            notification_type='team_update',
            priority='medium',
            metadata={
                'team_name': team_name,
                'event_type': 'team_deleted'
            }
        )


  
    
    @staticmethod
    def get_user_teams(user):
        """
        Get teams that a user is a member of
        
        Args:
            user: User to get teams for
            
        Returns:
            QuerySet: Teams the user is a member of
        """
        return Team.objects.filter(members=user)
    
    @staticmethod
    def get_team_members(team):
        """
        Get members of a team with their roles
        
        Args:
            team: Team to get members for
            
        Returns:
            QuerySet: TeamMembership objects for the team
        """
        return TeamMembership.objects.filter(team=team).select_related('user')
    
    @staticmethod
    def get_filterable_queryset():
        """
        Get an optimized queryset for list views with related data
        
        Returns:
            QuerySet: Optimized Team queryset
        """
        return Team.objects.all().prefetch_related(
            'members', 
            'teammembership_set'
        )
        
