from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.management import call_command
from django.utils import timezone
import logging
from timelines.models import Timeline

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Timeline)
def handle_timeline_status_change(sender, instance, created, **kwargs):
    """
    Signal handler to detect when the GROUPS timeline's status changes to 'expired'.
    Triggers the auto team assignment if the timeline is configured for it.
    """
    # Skip if this is a creation event or if assignment already processed
    if created or instance.team_assignment_processed:
        return
        
    # Only process the GROUPS timeline
    if instance.slug != Timeline.GROUPS:
        return
    
    # Check if the timeline just expired
    if instance.status == 'expired' and instance.auto_assign_teams:
        # Timeline has ended and is configured for auto team assignment
        logger.info(f"Groups timeline has ended. Running auto team assignment.")
        
        try:
            # Run the management command
            call_command('auto_assign_teams', instance.slug)
            
            # Update the timeline to record that assignment has been processed
            # Use update() to avoid triggering the signal again
            Timeline.objects.filter(pk=instance.pk).update(
                team_assignment_processed=True,
                team_assignment_date=timezone.now()
            )
            
            # Refresh the instance data
            instance.refresh_from_db()
            
            logger.info(f"Auto team assignment completed for groups timeline")
        except Exception as e:
            logger.error(f"Error during auto team assignment for groups timeline: {str(e)}")