from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """
    Signal handler that sends notifications via WebSocket when created
    """
    if created:
        from .services import NotificationService
        NotificationService.send_notification(instance)