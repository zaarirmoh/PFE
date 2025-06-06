from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from users.models import Student
from .team import Team

class TeamMembership(models.Model):
    """
    Represents the relationship between a User and a Team,
    including the role of the user in the team.
    """
    ROLE_OWNER = 'owner'
    ROLE_MEMBER = 'member'
    
    ROLE_CHOICES = (
        (ROLE_OWNER, 'Owner'),
        (ROLE_MEMBER, 'Member'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'team')
        
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.get_role_display()})"
    
    def clean(self):
        """
        Validate that:
        - The user meets the team's academic constraints
        - The team has not reached its member limit
        """
        super().clean()
        
        # Skip team size validation for owners (needed for team creation)
        if self.role != self.ROLE_OWNER:
            # Check if team is already at capacity
            current_count = self.team.members.count()
            if current_count >= self.team.maximum_members:
                raise ValidationError(
                    f"Team '{self.team.name}' has reached its maximum capacity of {self.team.maximum_members} members."
                )
        
        # Verify that user is a student
        try:
            student = self.user.student
        except Student.DoesNotExist:
            raise ValidationError("Only students can be team members.")
        
        # Check student's academic status
        if student.academic_status != 'active':
            raise ValidationError("Only students with active status can join teams.")
        
        # Check academic year match
        if student.current_year != self.team.academic_year:
            raise ValidationError(
                f"Only students in academic year {self.team.academic_year} can join this team."
            )
            
        # Check if the user is already an owner of a team for this academic year
        # This should only be checked when creating a new membership (not for the initial owner)
        if not self.pk:  # Only for new memberships
            owned_teams = Team.objects.filter(
                teammembership__user=self.user,
                teammembership__role=TeamMembership.ROLE_OWNER,
                academic_year=self.team.academic_year
            )
            
            if owned_teams.exists():
                raise ValidationError(
                    f"You already own a team for academic year {self.team.academic_year} "
                    f"and cannot join another team in the same year."
                )
    
    def save(self, *args, **kwargs):
        """Save after validation"""
        self.full_clean()
        super().save(*args, **kwargs)