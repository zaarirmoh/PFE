# themes/models.py (add to existing file)
from common.models import AuditableModel
from django.db import models
from .theme_models  import *
class ThemeChoice(AuditableModel):
    """
    Represents a team's preferences for themes, ranked by priority.
    """
    team = models.OneToOneField('teams.Team', on_delete=models.CASCADE, related_name='theme_choice')
    choices = models.ManyToManyField('themes.Theme', through='ThemeRanking')
    submission_date = models.DateTimeField(auto_now_add=True)
    is_final = models.BooleanField(default=False, help_text="Whether this choice list is finalized")
    
    def __str__(self):
        return f"Theme choices for {self.team.name}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['team'], name='unique_team_theme_choice')
        ]

class ThemeRanking(models.Model):
    """
    Represents the ranking of a theme by a team.
    """
    theme_choice = models.ForeignKey(ThemeChoice, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField(help_text="1 is highest priority")
    
    class Meta:
        ordering = ['rank']
        constraints = [
            models.UniqueConstraint(fields=['theme_choice', 'theme'], name='unique_theme_in_choice'),
            models.UniqueConstraint(fields=['theme_choice', 'rank'], name='unique_rank_in_choice')
        ]
    
    def __str__(self):
        return f"{self.theme.title} (Rank: {self.rank})"

class ThemeAssignment(AuditableModel):
    """
    Represents the final assignment of a theme to a team.
    """
    team = models.OneToOneField('teams.Team', on_delete=models.CASCADE, related_name='assigned_theme')
    theme = models.OneToOneField(Theme, on_delete=models.CASCADE, related_name='assigned_team')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='theme_assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.theme.title} assigned to {self.team.name}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['team'], name='unique_team_assignment'),
            models.UniqueConstraint(fields=['theme'], name='unique_theme_assignment')
        ]