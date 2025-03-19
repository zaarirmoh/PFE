from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .user import User

class Teacher(models.Model):
    PROFESSOR = 'professeur'
    MAITRE_CONFERENCES_A = 'maitre_conferences_a'
    MAITRE_CONFERENCES_B = 'maitre_conferences_b'
    MAITRE_ASSISTANT_A = 'maitre_assistant_a'
    MAITRE_ASSISTANT_B = 'maitre_assistant_b'
    GRADE_CHOICES = (
        (PROFESSOR, 'Professeur'),
        (MAITRE_CONFERENCES_A, 'Maître de conférences A'),
        (MAITRE_CONFERENCES_B, 'Maître de conférences B'),
        (MAITRE_ASSISTANT_A, 'Maître assistant A'),
        (MAITRE_ASSISTANT_B, 'Maitre assistant B'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    department = models.CharField(max_length=50, null=True, blank=True)
    grade = models.CharField(max_length=50, choices=GRADE_CHOICES, null=False, blank=False, default=MAITRE_ASSISTANT_B)

