# themes/models.py (add to existing file)
from common.models import AuditableModel, TimeStampedModel
from django.db import models
from .theme_models  import *
from teams.models import Team



class ThemeAssignment(TimeStampedModel):
    """
    Represents the final assignment of a theme to a team.
    """
    title = models.CharField(max_length=255, blank=True, null=True)
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='assigned_theme')
    # theme = models.OneToOneField(Theme, on_delete=models.CASCADE, related_name='assigned_team')
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='assigned_teams')

    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='theme_assignments')

    def __str__(self):
        return f"{self.theme.title} assigned to {self.team.name}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['team'], name='unique_team_assignment'),
            # models.UniqueConstraint(fields=['theme'], name='unique_theme_assignment')
        ]