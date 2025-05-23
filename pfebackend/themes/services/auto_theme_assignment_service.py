from django.db import transaction
from django.db.models import Count
import logging
from teams.models import Team
from themes.models import Theme, ThemeAssignment
from users.models import User


logger = logging.getLogger(__name__)

class AutoThemeAssignmentService:
    """
    Service for automatically assigning validated themes to teams based on academic year matching.
    This service will:
    1. Find all teams without assigned themes for a given year
    2. Find all validated themes for the same year
    3. Assign themes to teams randomly
    """
    
    @classmethod
    @transaction.atomic
    def assign_themes_for_year(cls, academic_year, assigned_by_user, max_teams_per_theme=None):
        """
        Main entry point to assign themes to teams for a specific academic year.
        
        Args:
            academic_year (str): The academic year code ('2', '3', '4siw', etc.)
            assigned_by_user (User): The user who is performing the assignment
            
        Returns:
            dict: Statistics about the assignments made
        """
        try:
            logger.info(f"Starting theme assignment for year '{academic_year}'")
            
            stats = {
                "academic_year": academic_year,
                "teams_without_theme": 0,
                "available_themes": 0,
                "assignments_created": 0,
                "remaining_teams": 0,
                "remaining_themes": 0
            }
            
            # Step 1: Get teams without assigned themes for this year
            teams_without_theme = cls._get_teams_without_theme(academic_year)
            stats["teams_without_theme"] = len(teams_without_theme)
            
            # Step 2: Get validated themes for this year
            available_themes = cls._get_available_themes(academic_year, max_teams_per_theme=max_teams_per_theme)
            stats["available_themes"] = len(available_themes)
            
            # Step 3: Assign themes to teams
            if teams_without_theme and available_themes:
                result = cls._assign_themes_to_teams(teams_without_theme, available_themes, assigned_by_user)
                stats.update(result)
            
            logger.info(f"Theme assignment completed: {stats['assignments_created']} assignments created")
            return stats
            
        except Exception as e:
            logger.exception(f"Error during theme assignment: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_teams_without_theme(academic_year):
        """
        Get teams that don't have an assigned theme for the given academic year.
        
        Args:
            academic_year (str): The academic year code
            
        Returns:
            QuerySet: Team objects without assigned themes
        """
        # Get teams that don't have a ThemeAssignment
        teams = Team.objects.filter(
            academic_year=academic_year
        ).exclude(
            assigned_theme__isnull=False
        )
        
        logger.debug(f"Found {teams.count()} teams without themes for year {academic_year}")
        return teams
    
    @staticmethod
    def _get_available_themes(academic_year, max_teams_per_theme=None):
        """
        Get validated themes that can be assigned to more teams.
        
        Args:
            academic_year (str): The academic year code
            max_teams_per_theme (int|None): Optional max teams per theme
            
        Returns:
            QuerySet: Theme objects available for assignment
        """
        themes = Theme.objects.filter(
            academic_year=academic_year,
            is_verified=True
        )
        
        if max_teams_per_theme is not None:
            # Annotate with current assignment count and filter
            themes = themes.annotate(
                assignment_count=Count('assigned_teams')
            ).filter(
                assignment_count__lt=max_teams_per_theme
            )
        
        logger.debug(f"Found {themes.count()} available themes for year {academic_year}")
        return themes
    
    @classmethod
    def _assign_themes_to_teams(cls, teams, themes, assigned_by_user):
        """
        Assign themes to teams randomly.
        
        Args:
            teams (QuerySet): Teams to assign themes to
            themes (QuerySet): Themes available for assignment
            assigned_by_user (User): User performing the assignment
            
        Returns:
            dict: Statistics about the assignments
        """
        # Convert to lists for easier manipulation
        teams_list = list(teams)
        themes_list = list(themes)
        
        assignments_created = 0
        
        # Randomize the order
        import random
        random.shuffle(teams_list)
        random.shuffle(themes_list)
        
        # Assign themes to teams until we run out of either
        for team, theme in zip(teams_list, themes_list):
            try:
                # Create the theme assignment
                ThemeAssignment.objects.create(
                    team=team,
                    theme=theme,
                    assigned_by=assigned_by_user,
                    title=f"{theme.title} - {team.name}"
                )
                assignments_created += 1
                logger.debug(f"Assigned theme '{theme.title}' to team '{team.name}'")
            except Exception as e:
                logger.error(f"Failed to assign theme to team: {str(e)}")
                continue
        
        return {
            "assignments_created": assignments_created,
            "remaining_teams": len(teams_list) - assignments_created,
            "remaining_themes": len(themes_list) - assignments_created
        }