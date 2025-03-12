# notifications/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from common.models import TimeStampedModel
from django.conf import settings


class Notification(TimeStampedModel):
    """
    Model for storing user notifications with generic relations
    to support notifications from various sources.
    """
    NOTIFICATION_TYPES = (
        ('team_invitation', 'Team Invitation'),
        ('team_update', 'Team Update'),
        ('team_membership', 'Team Membership'),
        ('project_update', 'Project Update'),
        ('deadline', 'Deadline Reminder'),
        ('status', 'Status Update'),
        ('activity', 'Activity Notification'),
        ('system', 'System Notification'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    STATUS_CHOICES = (
        ('read', 'Read'),
        ('unread', 'Unread'),
        ('archived', 'Archived'),
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text="User who receives this notification"
    )
    
    title = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Short title for the notification"
    )
    
    content = models.TextField(
        help_text="Main notification message content"
    )
    
    type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES,
        help_text="Type of notification"
    )
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='unread',
        help_text="Current status of the notification"
    )
    
    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Content type of the related object"
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="ID of the related object"
    )
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional fields
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_LEVELS, 
        default='medium',
        help_text="Priority level of the notification"
    )
    
    action_url = models.CharField(
        max_length=255, 
        blank=True,
        help_text="URL for the action button in the notification"
    )
    
    # Store additional data for rendering the notification
    metadata = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Additional data for notification rendering and behavior"
    )
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.recipient.username}: {self.content[:50]}"
        
    def to_dict(self):
        """
        Convert notification to dictionary for API/WebSocket responses
        """
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'priority': self.priority,
            'action_url': self.action_url,
            'metadata': self.metadata
        }