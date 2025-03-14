from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.models import AuditableModel
from users.models import Student


class Team(AuditableModel):
    """
    Represents a team that can have multiple student members with different roles.
    Constraints:
    - Only students can create teams
    - Team members must share the same academic year, program and have 'active' status
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='TeamMembership',
        related_name='teams'
    )
    
    # Team academic constraints - these will be set from the owner's student profile
    academic_year = models.PositiveSmallIntegerField(
        help_text="Academic year requirement for team members"
    )
    academic_program = models.CharField(
        max_length=20, 
        choices=Student.ACADEMIC_PROGRAM_CHOICES,
        help_text="Academic program requirement for team members"
    )
    
    def __str__(self):
        return self.name
    
    @property
    def owner(self):
        """Returns the owner of the team"""
        return self.members.filter(teammembership__role='owner').first()
    
    def clean(self):
        """Validate the model before saving"""
        super().clean()
    
    def save(self, *args, **kwargs):
        """Save the model after validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def create_team(cls, owner, name, description=""):
        """
        Factory method to create a team with proper validation:
        - Validates that the owner is a student with active status
        - Sets the academic constraints from the owner's profile
        """
        from .team_membership import TeamMembership
        
        # Check if the owner is a student
        try:
            student = owner.student
        except Student.DoesNotExist:
            raise ValidationError("Only students can create teams.")
        
        # Check if the student has active status
        if student.academic_status != 'active':
            raise ValidationError("Only students with active status can create teams.")
        
        # Create the team with academic constraints from the owner
        team = cls(
            name=name,
            description=description,
            academic_year=student.current_year,
            academic_program=student.academic_program,
            created_by=owner,
            updated_by=owner
        )
        team.save()
        
        # Add the owner to the team
        TeamMembership.objects.create(
            user=owner,
            team=team,
            role=TeamMembership.ROLE_OWNER
        )
        
        return team