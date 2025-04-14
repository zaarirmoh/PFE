from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import make_aware, is_naive
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import json

from timelines.models import Timeline

@receiver(post_save, sender=Timeline)
def schedule_reassignment_on_end(sender, instance, created, **kwargs):
    if created and instance.timeline_type == "groups":
        end_date = instance.end_date
        if is_naive(end_date):
            end_date = make_aware(end_date)

        clocked_schedule, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=end_date
        )
        task_name = f"Reassign-{instance.academic_year}-{instance.pk}"

        PeriodicTask.objects.create(
            clocked=clocked_schedule,
            name=task_name,
            task='teams.tasks.reassign_students_task',
            one_off=True,
            args=json.dumps([instance.academic_year, 2, 6]),  # Static min=2, max=6
        )
