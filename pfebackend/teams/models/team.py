from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.models import AuditableModel
from users.models import Student
from .settings import TeamSettings


class Team(AuditableModel):
    """
    Represents a team that can have multiple student members with different roles.
    Constraints:
    - Only students can create teams
    - Team members must share the same academic year, program and have 'active' status
    - Team size is limited by the global TeamSettings configuration
    """
    name = models.CharField(max_length=100, unique=True)
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
    is_verified = models.BooleanField(default=False)
    
    # Maximum members setting is now handled by TeamSettings globally
    # This field indicates the specific limit for this team, which defaults to the global setting
    maximum_members = models.PositiveSmallIntegerField(
        help_text="Maximum number of members allowed in this team"
    )
    
    def __str__(self):
        return self.name
    
    @property
    def owner(self):
        """Returns the owner of the team"""
        return self.members.filter(teammembership__role='owner').first()
    
    @property
    def current_member_count(self):
        """Returns the current number of team members"""
        return self.members.count()
    
    @property
    def has_capacity(self):
        """Check if the team has capacity for more members"""
        return self.current_member_count < self.maximum_members
    
    def clean(self):
        """Validate the model before saving"""
        super().clean()
        
        # Ensure maximum_members doesn't exceed global limit
        global_max = TeamSettings.get_maximum_members()
        if self.maximum_members > global_max:
            self.maximum_members = global_max
    
    def save(self, *args, **kwargs):
        """
        Save the model after validation. 
        If maximum_members is not set, use the global default.
        """
        if not self.maximum_members:
            self.maximum_members = TeamSettings.get_maximum_members()
            
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def create_team(cls, owner, name, description=""):
        """
        Factory method to create a team with proper validation:
        - Validates that the owner is a student with active status
        - Sets the academic constraints from the owner's profile
        - Uses the global maximum_members setting
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
            maximum_members=TeamSettings.get_maximum_members(),
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