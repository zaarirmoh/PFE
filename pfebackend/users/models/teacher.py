from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .user import User

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    # Additional fields like subject, etc.
    department = models.CharField(max_length=50, null=True, blank=True)