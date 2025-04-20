from django.db import models
from .user import User

class ExternalUser(models.Model):
    UNIVERSITY = 'university'
    COMPANY = 'company'
    OTHER = 'other'
    EXTERNAL_USER_TYPE = (
        (UNIVERSITY, 'University'),
        (COMPANY, 'Company'),
        (OTHER, 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='external_user')
    EXTERNAL_USER_TYPE = models.CharField(max_length=50, choices=EXTERNAL_USER_TYPE, null=False, blank=False, default=OTHER)

