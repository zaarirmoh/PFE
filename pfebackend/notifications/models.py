from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from common.models import TimeStampedModel
from django.conf import settings


class Notification(TimeStampedModel):
    NOTIFICATION_TYPES = (
        ('deadline', 'Deadline Reminder'),
        ('status', 'Status Update'),
        ('activity', 'Activity Notification'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    content = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=(('read', 'Read'), ('unread', 'Unread')), default='unread')
    
    # For referencing various models (Project, Team, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    action_url = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.recipient.username}: {self.content[:50]}"