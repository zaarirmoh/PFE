# meetings/models.py
from django.db import models
from django.conf import settings
from common.models import AuditableModel
from teams.models import Team
from django.core.exceptions import ValidationError


class Meeting(AuditableModel):
    """
    Represents a meeting scheduled by a teacher for a team.
    Meetings have a title, description, scheduled time, location, and status.
    """
    STATUS_SCHEDULED = 'scheduled'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = (
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
    )
    
    LOCATION_TYPE_ONLINE = 'online'
    LOCATION_TYPE_PHYSICAL = 'physical'
    
    LOCATION_TYPE_CHOICES = (
        (LOCATION_TYPE_ONLINE, 'Online'),
        (LOCATION_TYPE_PHYSICAL, 'Physical'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='meetings')
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='scheduled_meetings'
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    location_type = models.CharField(
        max_length=20, 
        choices=LOCATION_TYPE_CHOICES, 
        default=LOCATION_TYPE_ONLINE
    )
    location_details = models.CharField(max_length=255, blank=True)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_SCHEDULED
    )
    
    class Meta:
        ordering = ['scheduled_at']
        
    def __str__(self):
        return f"{self.title} ({self.team.name}) - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Validate the model before saving"""
        super().clean()
        
        # # Ensure that either meeting_link or location_details is provided
        # if self.location_type == self.LOCATION_TYPE_ONLINE and not self.meeting_link:
        #     raise ValidationError("Meeting link is required for online meetings.")
        
        # if self.location_type == self.LOCATION_TYPE_PHYSICAL and not self.location_details:
        #     raise ValidationError("Location details are required for physical meetings.")
        
        # Ensure scheduled_at is in the future for new meetings
        if not self.pk and self.scheduled_at <= timezone.now():
            raise ValidationError("Meeting time must be in the future.")
    
    def save(self, *args, **kwargs):
        """Save after validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def cancel(self, cancelled_by=None):
        """
        Cancel a meeting and notify participants
        
        Args:
            cancelled_by: User who cancelled the meeting
        """
        if self.status != self.STATUS_SCHEDULED:
            raise ValidationError("Only scheduled meetings can be cancelled.")
            
        self.status = self.STATUS_CANCELLED
        if cancelled_by:
            self.updated_by = cancelled_by
            
        self.save(update_fields=['status', 'updated_by', 'updated_at'])
        
        # Notification will be handled by signals or service
        
    def mark_as_completed(self, completed_by=None):
        """
        Mark a meeting as completed
        
        Args:
            completed_by: User who marked the meeting as completed
        """
        if self.status != self.STATUS_SCHEDULED:
            raise ValidationError("Only scheduled meetings can be marked as completed.")
            
        self.status = self.STATUS_COMPLETED
        if completed_by:
            self.updated_by = completed_by
            
        self.save(update_fields=['status', 'updated_by', 'updated_at'])


# class MeetingAttendance(models.Model):
#     """
#     Represents attendance status for a meeting participant
#     """
#     STATUS_PENDING = 'pending'
#     STATUS_CONFIRMED = 'confirmed'
#     STATUS_DECLINED = 'declined'
#     STATUS_ATTENDED = 'attended'
#     STATUS_ABSENT = 'absent'
    
#     STATUS_CHOICES = (
#         (STATUS_PENDING, 'Pending'),
#         (STATUS_CONFIRMED, 'Confirmed'),
#         (STATUS_DECLINED, 'Declined'),
#         (STATUS_ATTENDED, 'Attended'),
#         (STATUS_ABSENT, 'Absent'),
#     )
    
#     meeting = models.ForeignKey(
#         Meeting, 
#         on_delete=models.CASCADE, 
#         related_name='attendances'
#     )
#     attendee = models.ForeignKey(
#         settings.AUTH_USER_MODEL, 
#         on_delete=models.CASCADE, 
#         related_name='meeting_attendances'
#     )
#     status = models.CharField(
#         max_length=20, 
#         choices=STATUS_CHOICES, 
#         default=STATUS_PENDING
#     )
#     response_timestamp = models.DateTimeField(null=True, blank=True)
#     response_notes = models.TextField(blank=True)
    
#     class Meta:
#         unique_together = ('meeting', 'attendee')
        
#     def __str__(self):
#         return f"{self.attendee.username} - {self.meeting.title} ({self.get_status_display()})"
        
#     def mark_attendance(self, status, notes=""):
#         """
#         Update the attendance status
        
#         Args:
#             status: New attendance status
#             notes: Optional notes about the attendance
#         """
#         if status not in dict(self.STATUS_CHOICES):
#             raise ValidationError(f"Invalid status: {status}")
            
#         self.status = status
        
#         if notes:
#             self.response_notes = notes
            
#         self.response_timestamp = timezone.now()
#         self.save(update_fields=['status', 'response_notes', 'response_timestamp'])


# Import at the end to avoid circular imports
from django.utils import timezone