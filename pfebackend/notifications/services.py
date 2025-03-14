# notifications/services.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from django.template.loader import render_to_string
from django.utils.html import escape
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service class for notification-related operations
    """
    
    @staticmethod
    def create_notification(recipient, content, notification_type, related_object=None, 
                           title="", priority='medium', action_url='', metadata=None):
        """
        Create a notification and store it in the database
        
        Args:
            recipient: User receiving the notification
            content: Text content of the notification
            notification_type: Type of notification
            related_object: Optional related Django model instance
            title: Optional title for the notification
            priority: Priority level (low, medium, high)
            action_url: URL for action button
            metadata: Additional data for rendering
            
        Returns:
            Notification: The created notification instance
        """
        try:
            content_type = None
            object_id = None
            
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object)
                object_id = related_object.id
            
            notification = Notification.objects.create(
                recipient=recipient,
                title=title,
                content=content,
                type=notification_type,
                content_type=content_type,
                object_id=object_id,
                priority=priority,
                action_url=action_url,
                metadata=metadata or {}
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None
    
    @staticmethod
    def send_notification(notification):
        """
        Send a notification via WebSocket
        
        Args:
            notification: Notification instance to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            channel_layer = get_channel_layer()
            
            notification_data = notification.to_dict()
            
            # Send to user's notification group
            async_to_sync(channel_layer.group_send)(
                f"user_{notification.recipient.id}_notifications",
                {
                    'type': 'notification_message',
                    'notification': notification_data
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    @staticmethod
    def create_and_send(recipient, content, notification_type, related_object=None, 
                       title="", priority='medium', action_url='', metadata=None):
        """
        Create a notification and send it via WebSocket
        
        Returns:
            Notification: The created notification or None if failed
        """
        notification = NotificationService.create_notification(
            recipient, content, notification_type, related_object, 
            title, priority, action_url, metadata
        )
        
        if notification:
            NotificationService.send_notification(notification)
            
        return notification
    
    @staticmethod
    def mark_as_read(user, notification_id):
        """
        Mark a specific notification as read
        
        Args:
            user: User who owns the notification
            notification_id: ID of the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.status = 'read'
            notification.save(update_fields=['status', 'updated_at'])
            return True
            
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def mark_all_as_read(user):
        """
        Mark all user's unread notifications as read
        
        Args:
            user: User whose notifications to mark as read
            
        Returns:
            int: Number of notifications marked as read
        """
        count = Notification.objects.filter(
            recipient=user,
            status='unread'
        ).update(status='read')
        
        return count
    
    @staticmethod
    def archive_notification(user, notification_id):
        """
        Archive a notification
        
        Args:
            user: User who owns the notification
            notification_id: ID of the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.status = 'archived'
            notification.save(update_fields=['status', 'updated_at'])
            return True
            
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def get_pending_notifications(user, limit=10):
        """
        Get recent unread notifications for user
        
        Args:
            user: User whose notifications to retrieve
            limit: Maximum number of notifications to return
            
        Returns:
            list: List of notification dictionaries
        """
        notifications = Notification.objects.filter(
            recipient=user,
            status='unread'
        ).select_related('content_type').order_by('-created_at')[:limit]
        
        return [notification.to_dict() for notification in notifications]
    
    @staticmethod
    def get_notifications_by_type(user, notification_type, status=None, limit=None):
        """
        Get notifications of a specific type
        
        Args:
            user: User whose notifications to retrieve
            notification_type: Type of notifications to retrieve
            status: Optional status filter
            limit: Optional limit
            
        Returns:
            QuerySet: Filtered notification queryset
        """
        queryset = Notification.objects.filter(
            recipient=user,
            type=notification_type
        )
        
        if status:
            queryset = queryset.filter(status=status)
            
        queryset = queryset.order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
            
        return queryset