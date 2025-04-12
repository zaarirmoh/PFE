
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .user import User
from django.core.exceptions import ValidationError

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    
    ACADEMIC_STATUS_CHOICES = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('graduated', 'Graduated'),
    )
    
    ACADEMIC_YEAR_CHOICES = (
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4siw', '4th Year SIW'),
        ('4isi', '4th Year ISI'),
        ('4iasd', '4th Year IASD'),
        ('5siw', '5th Year SIW'),
        ('5isi', '5th Year ISI'),
        ('5iasd', '5th Year IASD'),
    )

    matricule = models.CharField(max_length=20, unique=True, blank=True, null=True)
    enrollment_year = models.PositiveIntegerField(help_text="Year of admission", default=2014)
    current_year = models.CharField(max_length=5, choices=ACADEMIC_YEAR_CHOICES, help_text="Current year in the program")
    # group = models.PositiveSmallIntegerField(
    #     blank=True, 
    #     null=True, 
    #     help_text="Student's group number"
    # )
    academic_status = models.CharField(max_length=20, choices=ACADEMIC_STATUS_CHOICES, default='active')
    
    def save(self, *args, **kwargs):
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