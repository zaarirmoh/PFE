# notification_service.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from teams.models import TeamInvitation

def create_notification(recipient, content, notification_type, related_object=None, 
                        priority='medium', action_url=''):
    """
    Create a notification and send it via WebSocket
    """
    # Create notification in database
    content_type = None
    object_id = None
    
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.id
    
    notification = Notification.objects.create(
        recipient=recipient,
        content=content,
        type=notification_type,
        content_type=content_type,
        object_id=object_id,
        priority=priority,
        action_url=action_url
    )
    
    # Send real-time notification through WebSocket
    channel_layer = get_channel_layer()
    
    # Prepare notification data for sending
    notification_data = {
        'id': notification.id,
        'content': notification.content,
        'type': notification.type,
        'created_at': notification.created_at.isoformat(),
        'priority': notification.priority,
        'action_url': notification.action_url
    }
    
    # Send to user's notification group
    async_to_sync(channel_layer.group_send)(
        f"user_{recipient.id}_notifications",
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )
    
    return notification

def send_team_invitation(team, inviter, invitee):
    """
    Send a team invitation and create a notification
    """
    # Create invitation
    invitation = TeamInvitation.objects.create(
        team=team,
        inviter=inviter,
        invitee=invitee
    )
    
    # Create notification
    content = f"{inviter.get_full_name()} invited you to join team '{team.name}'"
    action_url = f"/teams/invitations/{invitation.id}/"
    
    create_notification(
        recipient=invitee,
        content=content,
        notification_type='activity',
        related_object=invitation,
        priority='medium',
        action_url=action_url
    )
    
    return invitation