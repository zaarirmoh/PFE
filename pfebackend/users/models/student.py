from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .user import User
from django.core.exceptions import ValidationError

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    # Additional fields like grade, etc.
    ACADEMIC_PROGRAM_CHOICES = (
        ('preparatory', 'Preparatory'),
        ('superior', 'Superior'),
    )

    ACADEMIC_STATUS_CHOICES = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('graduated', 'Graduated'),
    )

    matricule = models.CharField(max_length=20, unique=True, blank=True, null=True)
    enrollment_year = models.PositiveIntegerField(help_text="Year of admission", default=2014)
    academic_program = models.CharField(max_length=20, choices=ACADEMIC_PROGRAM_CHOICES)
    current_year = models.PositiveSmallIntegerField(help_text="Current year in the program", default=1)
    group = models.PositiveSmallIntegerField(
        blank=True, 
        null=True, 
        help_text="Student's group number"
    )
    # For superior class: speciality can be set once the student chooses one; optional in preparatory.
    speciality = models.CharField(max_length=50, null=True, blank=True)
    academic_status = models.CharField(max_length=20, choices=ACADEMIC_STATUS_CHOICES, default='active')
    
    def clean(self):
        # Validate current_year based on academic_program
        if self.academic_program == 'preparatory' and self.current_year not in [1, 2]:
            raise ValidationError({
                'current_year': f'For preparatory program, current year must be 1 or 2. Got {self.current_year}.'
            })
        elif self.academic_program == 'superior' and self.current_year not in [1, 2, 3]:
            raise ValidationError({
                'current_year': f'For superior program, current year must be 1, 2, or 3. Got {self.current_year}.'
            })
        
        super().clean()

    def save(self, *args, **kwargs):
        # Call clean method to ensure validation runs on save
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.matricule}"
    
    
    
class StudentSkill(models.Model):
    """
    Separate model for managing student skills with a many-to-many relationship.
    This allows for more flexibility and easier management of skills.
    """
    student = models.ForeignKey(
        'users.Student', 
        on_delete=models.CASCADE, 
        related_name='skills'
    )
    
    name = models.CharField(max_length=100)
    proficiency_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert')
        ],
        default='beginner'
    )
    
    def __str__(self):
        return f"{self.name} ({self.proficiency_level})"
    
    class Meta:
        unique_together = ('student', 'name')
        verbose_name = "Student Skill"
        verbose_name_plural = "Student Skills"