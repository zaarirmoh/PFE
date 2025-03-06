from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .user import User

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

    matricule = models.CharField(max_length=20, unique=True, default='ZAARIR')
    enrollment_year = models.PositiveIntegerField(help_text="Year of admission", default=2014)
    academic_program = models.CharField(max_length=20, choices=ACADEMIC_PROGRAM_CHOICES)
    current_year = models.PositiveSmallIntegerField(help_text="Current year in the program", default=1)
    # For superior class: speciality can be set once the student chooses one; optional in preparatory.
    speciality = models.CharField(max_length=50, null=True, blank=True)
    academic_status = models.CharField(max_length=20, choices=ACADEMIC_STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.matricule}"