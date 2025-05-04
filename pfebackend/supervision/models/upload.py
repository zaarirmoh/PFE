from django.db import models
from django.conf import settings
from teams.models import Team


class Upload(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='uploads')
    title = models.CharField(max_length=255)
    url = models.URLField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title