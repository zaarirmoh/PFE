from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .user import User

class Administrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='administrator')
    # Additional fiels like ... ect.
    role_description = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role_description}"