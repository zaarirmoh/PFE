# meetings/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Meeting
from notifications.services import NotificationService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Meeting)
def handle_meeting_update(sender, instance, **kwargs):
    """Handle meeting updates and store previous state for comparison"""
    if instance.pk:
        try:
            # Store the old instance for comparison in post_save
            instance._old_instance = Meeting.objects.get(pk=instance.pk)
        except Meeting.DoesNotExist:
            instance._old_instance = None


@receiver(post_save, sender=Meeting)
def send_meeting_update_notifications(sender, instance, created, **kwargs):
    """
    Send notifications when meeting details are updated (not for new meetings)
    This is a backup mechanism - primary notifications are sent by the service
    """
    if not created and hasattr(instance, '_old_instance') and instance._old_instance:
        old_instance = instance._old_instance
        
        # Key attributes to check for changes
        changed_attrs = []
        
        # Check for date/time changes
        if instance.scheduled_at != old_instance.scheduled_at:
            changed_attrs.append('scheduled_time')
            
        # Check for location changes
        location_changed = (
            instance.location_type != old_instance.location_type or
            instance.location_details != old_instance.location_details or
            instance.meeting_link != old_instance.meeting_link
        )
        if location_changed:
            changed_attrs.append('location')
            
        # Check for title/description changes
        if instance.title != old_instance.title:
            changed_attrs.append('title')
        if instance.description != old_instance.description:
            changed_attrs.append('description')
            
        # Only trigger if any notifications haven't been sent by service
        # This avoids duplicate notifications
        if changed_attrs and not getattr(instance, '_notifications_sent', False):
            logger.info(f"Signal detected changes in meeting {instance.id}: {changed_attrs}")


# @receiver(post_save, sender=MeetingAttendance)
# def handle_attendance_update(sender, instance, created, **kwargs):
#     """
#     Send notifications or reminders for attendance updates
#     This is a backup mechanism - primary notifications are sent by the service
#     """
#     # No action needed for new records or if notifications have been sent by service
#     if created or getattr(instance, '_notifications_sent', False):
#         return
        
#     logger.info(f"Signal detected attendance update: {instance.id}, status: {instance.status}")


def send_upcoming_meeting_reminders():
    """
    Send reminders for upcoming meetings (to be called by a scheduler)
    """
    # Find meetings happening in next 24 hours
    now = timezone.now()
    tomorrow = now + timezone.timedelta(hours=24)
    
    # Find upcoming meetings that are still scheduled
    upcoming_meetings = Meeting.objects.filter(
        scheduled_at__gt=now,
        scheduled_at__lte=tomorrow,
        status=Meeting.STATUS_SCHEDULED
    ).select_related('team')
    
    for meeting in upcoming_meetings:
        # Send reminder to all team members
        team_members = meeting.team.members.all()
        team_name = meeting.team.name
        scheduled_time = meeting.scheduled_at.strftime("%A, %B %d at %I:%M %p")
        
        title = f"Reminder: Upcoming Meeting - {meeting.title}"
        content = (
            f"Reminder: You have an upcoming team meeting for '{team_name}'.\n\n"
            f"Meeting: {meeting.title}\n"
            f"When: {scheduled_time} (in less than 24 hours)\n"
            f"Duration: {meeting.duration_minutes} minutes\n"
        )
        
        if meeting.location_type == Meeting.LOCATION_TYPE_ONLINE:
            content += f"Location: Online\n"
            if meeting.meeting_link:
                content += f"Link: {meeting.meeting_link}\n"
        else:
            content += f"Location: {meeting.location_details}\n"
            
        # Add metadata for rich rendering
        metadata = {
            'meeting_id': meeting.id,
            'team_id': meeting.team.id,
            'team_name': team_name,
            'scheduled_at': meeting.scheduled_at.isoformat(),
            'event_type': 'meeting_reminder'
        }
        
        # Create action URL for the meeting
        action_url = f"/meetings/{meeting.id}/"
        
        # Send notifications to all team members
        for member in team_members:
            # # Check if user has already responded to the meeting
            # attendance = MeetingAttendance.objects.filter(
            #     meeting=meeting,
            #     attendee=member
            # ).first()
            
            # # Add attendance status to content if available
            # if attendance and attendance.status != MeetingAttendance.STATUS_PENDING:
            #     status_text = "confirmed" if attendance.status == MeetingAttendance.STATUS_CONFIRMED else "declined"
            #     content += f"\nYou have {status_text} this meeting."
            
            NotificationService.create_and_send(
                recipient=member,
                title=title,
                content=content,
                notification_type='meeting_reminder',
                related_object=meeting,
                priority='high',
                action_url=action_url,
                metadata=metadata
            )