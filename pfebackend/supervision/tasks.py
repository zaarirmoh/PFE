# meetings/tasks.py
from celery import shared_task
from .signals import send_upcoming_meeting_reminders
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_meeting_reminders():
    """
    Celery task to send reminders for upcoming meetings
    """
    logger.info("Starting task: send_meeting_reminders")
    send_upcoming_meeting_reminders()
    logger.info("Completed task: send_meeting_reminders")