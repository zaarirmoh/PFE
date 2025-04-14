from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.models import TimeStampedModel
from teams.mixins import TeamRequestStatusMixin
from teams.models import Team
from .theme_models import Theme


class ThemeSupervisionRequest(TeamRequestStatusMixin, TimeStampedModel):
    """
    Represents a request from a team to a teacher for theme supervision.
    """
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='supervision_requests')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='supervision_requests')
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_supervision_requests'
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_supervision_requests',
        help_text="The supervisor being invited to supervise the theme"
    )
    status = models.CharField(
        max_length=20,
        choices=TeamRequestStatusMixin.STATUS_CHOICES,
        default=TeamRequestStatusMixin.STATUS_PENDING
    )
    message = models.TextField(blank=True, help_text="Optional message from the team")
    response_message = models.TextField(blank=True, help_text="Optional response message from the supervisor")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'theme'],
                condition=models.Q(status__in=['PENDING', 'ACCEPTED']),
                name='unique_active_supervision_request'
            )
        ]
        
    def __str__(self):
        return f"Theme supervision request from {self.team.name} for {self.theme.title}"
    
    def clean(self):
        """
        Validate that:
        - Requester is a team owner
        - Theme is available for supervision
        - Team doesn't already have an assigned theme
        """
        super().clean()
        
        from teams.models import TeamMembership
        from themes.models import ThemeAssignment
        
        # Verify requester is a team owner
        if not self.team.members.filter(
            teammembership__user=self.requester,
            teammembership__role=TeamMembership.ROLE_OWNER
        ).exists():
            raise ValidationError("Only team owners can request theme supervision.")
        
        # # Verify theme doesn't already have an assigned team
        # if hasattr(self.theme, 'assigned_team'):
        #     raise ValidationError(f"This theme is already assigned to another team.")
        
        # Verify team doesn't already have an assigned theme
        if hasattr(self.team, 'assigned_theme'):
            raise ValidationError(f"Your team already has an assigned theme.")
        
        # Verify team's academic constraints match the theme's
        if self.team.academic_year != str(self.theme.academic_year):
            raise ValidationError(
                f"Your team's academic year ({self.team.academic_year}) doesn't match "
                f"the theme's academic year ({self.theme.academic_year})."
            )
    
    def save(self, *args, **kwargs):
        """Save after validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def accept(self, response_message=""):
        """
        Accept the supervision request and create a theme assignment
        """
        from themes.models import ThemeAssignment
        
        # Verify the request is pending
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending requests can be accepted.")
        
        # Get the supervisor (theme proposer)
        supervisor = self.theme.proposed_by
        
        # Create the theme assignment
        ThemeAssignment.objects.create(
            team=self.team,
            theme=self.theme,
            assigned_by=supervisor
        )
        
        # Update request status and response message
        self.status = self.STATUS_ACCEPTED
        self.response_message = response_message
        self.save(update_fields=['status', 'response_message', 'updated_at'])
        
        return True
    
    def decline(self, response_message=""):
        """
        Decline the supervision request
        """
        # Verify the request is pending
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending requests can be declined.")
        
        # Update request status and response message
        self.status = self.STATUS_DECLINED
        self.response_message = response_message
        self.save(update_fields=['status', 'response_message', 'updated_at'])
        
        return True