from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.models import TimeStampedModel
from users.models import Student
from .team import Team


class TeamJoinRequest(TimeStampedModel):
    """
    Represents a request from a student to join a team.
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_EXPIRED = 'expired'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_EXPIRED, 'Expired'),
    )
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='join_requests')
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_join_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    message = models.TextField(blank=True, help_text="Optional message from the requester")
    
    class Meta:
        unique_together = ('team', 'requester', 'status')

        
    def __str__(self):
        return f"{self.requester.username} requested to join {self.team.name}"
    
    def clean(self):
        """
        Validate that:
        - Requester is not already a team member
        - Requester meets the team's academic constraints
        - Team has not reached capacity
        """
        super().clean()
        
        # Verify requester is not already a team member
        if self.team.members.filter(id=self.requester.id).exists():
            raise ValidationError("You are already a member of this team.")
        
        # Check if team is already at capacity
        if not self.team.has_capacity:
            raise ValidationError(
                f"Team '{self.team.name}' has reached its maximum capacity of {self.team.maximum_members} members."
            )
        
        # Verify requester is a student
        try:
            student = self.requester.student
        except Student.DoesNotExist:
            raise ValidationError("Only students can request to join teams.")
        
        # Check student's academic status
        if student.academic_status != 'active':
            raise ValidationError(
                "Only students with active status can request to join teams."
            )
        
        # Check academic year and program match
        if student.current_year != self.team.academic_year:
            raise ValidationError(
                f"Only students in academic year {self.team.academic_year} can join this team."
            )
        
        if student.academic_program != self.team.academic_program:
            raise ValidationError(
                f"Only students in the {self.team.academic_program} program can join this team."
            )
    
    def save(self, *args, **kwargs):
        """Save after validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def accept(self):
        """
        Accept the join request and create a new team membership
        """
        from .team_membership import TeamMembership
        
        # Verify the request is pending
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending requests can be accepted.")
        
        # Check if team is at capacity (rechecking here for safety)
        if not self.team.has_capacity:
            self.status = self.STATUS_EXPIRED
            self.save()
            raise ValidationError(
                f"Team '{self.team.name}' has reached its maximum capacity of {self.team.maximum_members} members."
            )
        
        # Create the team membership
        TeamMembership.objects.create(
            user=self.requester,
            team=self.team,
            role=TeamMembership.ROLE_MEMBER
        )
        
        # Update request status
        self.status = self.STATUS_ACCEPTED
        self.save()
        
        return True
    
    def decline(self):
        """
        Decline the join request
        """
        # Verify the request is pending
        if self.status != self.STATUS_PENDING:
            raise ValidationError("Only pending requests can be declined.")
        
        # Update request status
        self.status = self.STATUS_DECLINED
        self.save()
        
        return True