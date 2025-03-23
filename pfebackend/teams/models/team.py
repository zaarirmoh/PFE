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
    - A student can only create one team per academic year and program
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
    is_verified = models.BooleanField(default=False)
    
    # Maximum members setting is now handled by TeamSettings globally
    # This field indicates the specific limit for this team, which defaults to the global setting
    maximum_members = models.PositiveSmallIntegerField(
        help_text="Maximum number of members allowed in this team"
    )
    
    class Meta:
        # Add unique constraint for name (case-insensitive handled in validation)
        unique_together = [('academic_year', 'academic_program', 'name')]
    
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
    
    @property
    def program_year_settings(self):
        """Get the program-year settings for this team"""
        return TeamSettings.get_settings(
            program=self.academic_program,
            year=self.academic_year
        )
    
    def clean(self):
        """Validate the model before saving"""
        super().clean()
        
        # Ensure maximum_members doesn't exceed global limit
        program_year_max = TeamSettings.get_maximum_members(
            program=self.academic_program,
            year=self.academic_year
        )
        if self.maximum_members > program_year_max:
            self.maximum_members = program_year_max
    
    def save(self, *args, **kwargs):
        """
        Save the model after validation. 
        If maximum_members is not set, use the global default.
        """
        if not self.maximum_members:
            self.maximum_members = TeamSettings.get_maximum_members(
                program=self.academic_program,
                year=self.academic_year
            )
            
        self.full_clean()
        super().save(*args, **kwargs)
        
    @classmethod
    def student_has_team_for_year_program(cls, student_user, year, program):
        """
        Check if a student already owns a team for the given academic year and program.
        
        Args:
            student_user: The User object representing a student
            year: The academic year to check
            program: The academic program to check
            
        Returns:
            bool: True if the student already has a team for the year/program, False otherwise
        """
        from .team_membership import TeamMembership
        
        # Find teams where the user is an owner
        owned_teams = cls.objects.filter(
            teammembership__user=student_user,
            teammembership__role=TeamMembership.ROLE_OWNER,
            academic_year=year,
            academic_program=program
        )
        
        return owned_teams.exists()
    
    @classmethod
    def student_is_member_for_year_program(cls, student_user, year, program):
        """
        Check if a student is already a member of any team for the given academic year and program.
        
        Args:
            student_user: The User object representing a student
            year: The academic year to check
            program: The academic program to check
            
        Returns:
            bool: True if the student is already a member of a team for the year/program, False otherwise
        """
        # Find teams where the user is a member
        member_teams = cls.objects.filter(
            members=student_user,
            academic_year=year,
            academic_program=program
        )
        
        return member_teams.exists()
    @classmethod
    def create_team(cls, owner, name, description=""):
        """
        Factory method to create a team with proper validation:
        - Validates that the owner is a student with active status
        - Sets the academic constraints from the owner's profile
        - Uses the global maximum_members setting
        - Ensures the student hasn't already created a team for this year/program
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
        
        # Check if student already owns a team for this year/program
        if cls.student_has_team_for_year_program(owner, student.current_year, student.academic_program):
            raise ValidationError(
                f"You have already created a team for {student.current_year} year in the {student.academic_program} program. "
                "A student can only create one team per academic year and program."
            )
            
        # Check if the student is already a member of a team for their academic year/program
        if cls.student_is_member_for_year_program(owner, student.current_year, student.academic_program):
            raise ValidationError(
                f"You are already a member of a team for academic year {student.current_year} in the {student.academic_program} program."
            )
            
        max_members = TeamSettings.get_maximum_members(
            program=student.academic_program,
            year=student.current_year
        )


        # Create the team with academic constraints from the owner
        team = cls(
            name=name,
            description=description,
            academic_year=student.current_year,
            academic_program=student.academic_program,
            maximum_members=max_members,
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