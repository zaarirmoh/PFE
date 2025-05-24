from django.db import models
from django.conf import settings
from teams.models import Team
from common.models import TimeStampedModel


class Upload(TimeStampedModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='uploads')
    title = models.CharField(max_length=255)
    url = models.URLField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title


class ResourceComment(TimeStampedModel):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"Comment by {self.author.username} on {self.upload.title}"

    class Meta:
        ordering = ['-created_at']