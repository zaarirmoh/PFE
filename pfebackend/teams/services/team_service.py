from teams.models import Team, TeamMembership


class TeamService:
    """Service class for team-related operations"""
    
    @staticmethod
    def create_team(name, description, owner):
        """
        Create a new team with the given owner using the model's factory method
        """
        # Use the model's factory method instead of manual creation
        return Team.create_team(owner, name, description)


    
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
        
