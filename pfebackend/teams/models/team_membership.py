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
        Validate that the user meets the team's academic constraints:
        - User must be a student
        - Student must have active status
        - Student must be in the same academic year and program as the team
        """
        super().clean()
        
        # Verify that user is a student
        try:
            student = self.user.student
        except Student.DoesNotExist:
            raise ValidationError("Only students can be team members.")
        
        # Check student's academic status
        if student.academic_status != 'active':
            raise ValidationError("Only students with active status can join teams.")
        
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
