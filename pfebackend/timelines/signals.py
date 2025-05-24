from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import make_aware, is_naive, now, timedelta
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import json
import logging

from timelines.models import Timeline
from notifications.services import NotificationService

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Timeline)
def schedule_reassignment_on_end(sender, instance, created, **kwargs):
    # Only process group timelines
    if instance.timeline_type == "groups":
        end_date = instance.end_date
        if is_naive(end_date):
            end_date = make_aware(end_date)

        task_name = f"Reassign-{instance.academic_year}-{instance.pk}"

        if created:
            # For newly created group timelines
            logger.info(f"Creating new auto-assignment task for timeline: {instance.name}")
            
            clocked_schedule, _ = ClockedSchedule.objects.get_or_create(
                clocked_time=end_date
            )
            
            PeriodicTask.objects.create(
                clocked=clocked_schedule,
                name=task_name,
                task='teams.tasks.reassign_students_task',
                one_off=True,
                args=json.dumps([instance.academic_year, 2, 6]),  # Static min=2, max=6
            )
        else:
            # For updated group timelines, update the existing task
            try:
                task = PeriodicTask.objects.get(name=task_name)
                
                # Update the scheduled time
                if not task.clocked or task.clocked.clocked_time != end_date:
                    logger.info(f"Updating auto-assignment task timing for timeline: {instance.name}")
                    
                    # Create or get the new schedule
                    clocked_schedule, _ = ClockedSchedule.objects.get_or_create(
                        clocked_time=end_date
                    )
                    
                    # Update the task with the new schedule
                    task.clocked = clocked_schedule
                    task.save()
            except PeriodicTask.DoesNotExist:
                # If task doesn't exist for some reason, create it
                logger.warning(f"Auto-assignment task not found for existing timeline: {instance.name}. Creating new task.")
                
                clocked_schedule, _ = ClockedSchedule.objects.get_or_create(
                    clocked_time=end_date
                )
                
                PeriodicTask.objects.create(
                    clocked=clocked_schedule,
                    name=task_name,
                    task='teams.tasks.reassign_students_task',
                    one_off=True,
                    args=json.dumps([instance.academic_year, 2, 6]),  # Static min=2, max=6
                )


