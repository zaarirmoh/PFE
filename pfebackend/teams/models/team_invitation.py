from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.models import TimeStampedModel
from users.models import Student
from .team import Team
from teams.mixins import TeamRequestStatusMixin


class TeamInvitation(TeamRequestStatusMixin, TimeStampedModel):
    """
    Represents an invitation to join a team.
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_invitations'
    )
    status = models.CharField(
        max_length=20,
        choices=TeamRequestStatusMixin.STATUS_CHOICES,
        default=TeamRequestStatusMixin.STATUS_PENDING
        )
    message = models.TextField(blank=True, help_text="Optional message from the inviter")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'invitee'],
                condition=models.Q(status__in=['PENDING', 'ACCEPTED']),  # Only enforce uniqueness for active requests
                name='unique_active_invitation'
            )
        ]
        
    def __str__(self):
        return f"{self.inviter.username} invited {self.invitee.username} to {self.team.name}"
    
    def clean(self):
        """
        Validate that:
        - Inviter is a team member
        - Invitee meets the team's academic constraints
        - Team has not reached capacity
        """
        super().clean()
        
        # Verify inviter is a team member
        if not self.team.members.filter(id=self.inviter.id).exists():
            raise ValidationError("Only team members can send invitations.")
        
        # Verify invitee is not already a team member
        if self.team.members.filter(id=self.invitee.id).exists():
            raise ValidationError(f"{self.invitee.username} is already a member of this team.")
        
        # Check if team is already at capacity
        if not self.team.has_capacity:
            raise ValidationError(
                f"Team '{self.team.name}' has reached its maximum capacity of {self.team.maximum_members} members."
            )
        
        # Verify invitee is a student
        try:
            student = self.invitee.student
        except Student.DoesNotExist:
            raise ValidationError("Only students can be invited to teams.")
        
        # Check student's academic status
        if student.academic_status != 'active':
            raise ValidationError(
                "Only students with active status can be invited to teams."
            )
        
        # Check academic year match
        if student.current_year != self.team.academic_year:
            raise ValidationError(
                f"Only students in academic year {self.team.academic_year} can be invited to this team."
            )
    
    def save(self, *args, **kwargs):
        """Save after validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def accept(self):
        """
        Accept the invitation and create a new team membership
        """
        from .team_membership import TeamMembership

        # Verify the invitation is pending
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending invitations can be accepted.")
        
        # Check if team is at capacity (rechecking here for safety)
        if not self.team.has_capacity:
            self.status = self.STATUS_EXPIRED
            self.save()
            raise ValidationError(
                f"Team '{self.team.name}' has reached its maximum capacity of {self.team.maximum_members} members."
            )
        
        # Create the team membership
        TeamMembership.objects.create(
            user=self.invitee,
            team=self.team,
            role=TeamMembership.ROLE_MEMBER
        )
        
        # # Update invitation status
        # self.status = self.STATUS_ACCEPTED
        # self.save()
        TeamInvitation.objects.filter(pk=self.pk).update(status=self.STATUS_ACCEPTED)
        self.refresh_from_db()
        return True
    
    def decline(self):
        """
        Decline the invitation
        """
        # Verify the invitation is pending
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending invitations can be declined.")
        
        # Update invitation status
        self.status = self.STATUS_DECLINED
        self.save()
        
        return True