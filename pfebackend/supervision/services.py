# meetings/services.py
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from channels.db import database_sync_to_async
from .models import Meeting
from users.models import Teacher
from teams.models import TeamMembership
from notifications.services import NotificationService
import logging

logger = logging.getLogger(__name__)


class MeetingService:
    """Service class for meeting operations"""
    
    @staticmethod
    def create_meeting(teacher_user, team_id, meeting_data):
        """
        Create a meeting for a team and notify members
        
        Args:
            teacher_user (User): Teacher creating the meeting
            team_id (int): ID of the team
            meeting_data (dict): Meeting details
            
        Returns:
            Meeting: The created meeting
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If the user is not authorized
        """
        # # Validate that the user is a teacher
        # try:
        #     teacher = Teacher.objects.get(user=teacher_user)
        #     if not teacher.is_active:
        #         raise PermissionDenied("Only active teachers can create meetings.")
        # except Teacher.DoesNotExist:
        #     raise PermissionDenied("Only teachers can create meetings.")
            
        from teams.models import Team
        
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            raise ValidationError(f"Team with ID {team_id} does not exist.")
            
        try:
            with transaction.atomic():
                # Create the meeting
                meeting = Meeting(
                    team=team,
                    scheduled_by=teacher_user,
                    created_by=teacher_user,
                    updated_by=teacher_user,
                    **meeting_data
                )
                
                # This will trigger validation via full_clean in the save method
                meeting.save()
                
                # Create attendance records for all team members
                # team_members = TeamMembership.objects.filter(team=team).select_related('user')
                
                # for membership in team_members:
                #     MeetingAttendance.objects.create(
                #         meeting=meeting,
                #         attendee=membership.user
                #     )
                
                # Send notifications to team members
                MeetingService._send_meeting_notifications(meeting)
                
                return meeting
                
        except ValidationError as e:
            logger.error(f"Validation error creating meeting: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating meeting: {str(e)}")
            raise
    
    @staticmethod
    def update_meeting(meeting_id, teacher_user, meeting_data):
        """
        Update a meeting and notify members of changes
        
        Args:
            meeting_id (int): ID of the meeting
            teacher_user (User): Teacher updating the meeting
            meeting_data (dict): Updated meeting details
            
        Returns:
            Meeting: The updated meeting
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If the user is not authorized
        """
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            raise ValidationError(f"Meeting with ID {meeting_id} does not exist.")
            
        # Check if the user is authorized to update the meeting
        if meeting.scheduled_by != teacher_user:
            # Check if the user is a teacher (extra validation)
            try:
                Teacher.objects.get(user=teacher_user)
            except Teacher.DoesNotExist:
                raise PermissionDenied("Only teachers can update meetings.")
                
            raise PermissionDenied("Only the teacher who scheduled the meeting can update it.")
            
        if meeting.status != Meeting.STATUS_SCHEDULED:
            raise ValidationError("Cannot update a cancelled or completed meeting.")
            
        try:
            with transaction.atomic():
                # Update meeting fields
                for key, value in meeting_data.items():
                    setattr(meeting, key, value)
                
                meeting.updated_by = teacher_user
                meeting.save()
                
                # Notify team members of the update
                MeetingService._send_meeting_update_notifications(meeting)
                
                return meeting
                
        except ValidationError as e:
            logger.error(f"Validation error updating meeting: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating meeting: {str(e)}")
            raise
    
    @staticmethod
    def cancel_meeting(meeting_id, teacher_user):
        """
        Cancel a meeting and notify members
        
        Args:
            meeting_id (int): ID of the meeting
            teacher_user (User): Teacher cancelling the meeting
            
        Returns:
            Meeting: The cancelled meeting
            
        Raises:
            ValidationError: If validation fails
            PermissionDenied: If the user is not authorized
        """
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            raise ValidationError(f"Meeting with ID {meeting_id} does not exist.")
            
        # Check if the user is authorized to cancel the meeting
        if meeting.scheduled_by != teacher_user:
            # Check if the user is a teacher (extra validation)
            try:
                Teacher.objects.get(user=teacher_user)
            except Teacher.DoesNotExist:
                raise PermissionDenied("Only teachers can cancel meetings.")
                
            raise PermissionDenied("Only the teacher who scheduled the meeting can cancel it.")
            
        try:
            # Cancel the meeting
            meeting.cancel(cancelled_by=teacher_user)
            
            # Notify team members of the cancellation
            MeetingService._send_meeting_cancellation_notifications(meeting)
            
            return meeting
            
        except ValidationError as e:
            logger.error(f"Validation error cancelling meeting: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error cancelling meeting: {str(e)}")
            raise
    
    # @staticmethod
    # def update_attendance_status(attendance_id, user, status, notes=""):
    #     """
    #     Update an attendance status for a meeting
        
    #     Args:
    #         attendance_id (int): ID of the attendance record
    #         user (User): User updating their attendance
    #         status (str): New attendance status
    #         notes (str): Optional response notes
            
    #     Returns:
    #         MeetingAttendance: The updated attendance record
            
    #     Raises:
    #         ValidationError: If validation fails
    #         PermissionDenied: If the user is not authorized
    #     """
    #     try:
    #         attendance = MeetingAttendance.objects.select_related('meeting').get(id=attendance_id)
    #     except MeetingAttendance.DoesNotExist:
    #         raise ValidationError(f"Attendance record with ID {attendance_id} does not exist.")
            
    #     # Check if the user is authorized to update this attendance
    #     if attendance.attendee != user:
    #         raise PermissionDenied("You can only update your own attendance status.")
            
    #     # Check if the meeting is still scheduled
    #     if attendance.meeting.status != Meeting.STATUS_SCHEDULED:
    #         raise ValidationError("Cannot update attendance for a cancelled or completed meeting.")
            
    #     try:
    #         # Update the attendance
    #         attendance.mark_attendance(status, notes)
            
    #         # Notify the meeting creator of the response
    #         MeetingService._send_attendance_response_notification(attendance)
            
    #         return attendance
            
    #     except ValidationError as e:
    #         logger.error(f"Validation error updating attendance: {str(e)}")
    #         raise
    #     except Exception as e:
    #         logger.error(f"Error updating attendance: {str(e)}")
    #         raise
    
    @staticmethod
    def _send_meeting_notifications(meeting):
        """
        Send notifications to all team members about a new meeting
        
        Args:
            meeting (Meeting): The meeting to notify about
        """
        # Get all team members
        team_members = meeting.team.members.all()
        
        # Format meeting details
        team_name = meeting.team.name
        scheduled_time = meeting.scheduled_at.strftime("%A, %B %d, %Y at %I:%M %p")
        scheduled_by = meeting.scheduled_by.get_full_name() or meeting.scheduled_by.username
        
        title = f"New Team Meeting: {meeting.title}"
        content = (
            f"{scheduled_by} has scheduled a meeting for your team '{team_name}'.\n\n"
            f"Meeting: {meeting.title}\n"
            f"When: {scheduled_time}\n"
            f"Duration: {meeting.duration_minutes} minutes\n"
        )
        
        if meeting.location_type == Meeting.LOCATION_TYPE_ONLINE:
            content += f"Location: Online\n"
        else:
            content += f"Location: {meeting.location_details}\n"
            
        if meeting.description:
            content += f"\nDescription: {meeting.description}"
        
        # Add metadata for rich rendering
        metadata = {
            'meeting_id': meeting.id,
            'team_id': meeting.team.id,
            'team_name': team_name,
            'scheduled_by': {
                'id': meeting.scheduled_by.id,
                'name': scheduled_by
            },
            'scheduled_at': meeting.scheduled_at.isoformat(),
            'location_type': meeting.location_type,
            'profile_picture': meeting.scheduled_by.profile_picture_url,
        }
        
        # Create action URL for the meeting
        action_url = f"/meetings/{meeting.id}/"
        
        # Send notifications to all team members
        for member in team_members:
            NotificationService.create_and_send(
                recipient=member,
                title=title,
                content=content,
                notification_type='team_meeting',
                related_object=meeting,
                priority='high',
                action_url=action_url,
                metadata=metadata
            )
    
    @staticmethod
    def _send_meeting_update_notifications(meeting):
        """
        Send notifications to all team members about meeting updates
        
        Args:
            meeting (Meeting): The updated meeting
        """
        # Get all team members
        team_members = meeting.team.members.all()
        
        # Format meeting details
        team_name = meeting.team.name
        scheduled_time = meeting.scheduled_at.strftime("%A, %B %d, %Y at %I:%M %p")
        updated_by = meeting.updated_by.get_full_name() or meeting.updated_by.username
        
        title = f"Meeting Updated: {meeting.title}"
        content = (
            f"{updated_by} has updated the meeting for team '{team_name}'.\n\n"
            f"Meeting: {meeting.title}\n"
            f"When: {scheduled_time}\n"
            f"Duration: {meeting.duration_minutes} minutes\n"
        )
        
        if meeting.location_type == Meeting.LOCATION_TYPE_ONLINE:
            content += f"Location: Online\n"
        else:
            content += f"Location: {meeting.location_details}\n"
            
        if meeting.description:
            content += f"\nDescription: {meeting.description}"
        
        # Add metadata for rich rendering
        metadata = {
            'meeting_id': meeting.id,
            'team_id': meeting.team.id,
            'team_name': team_name,
            'updated_by': {
                'id': meeting.updated_by.id,
                'name': updated_by
            },
            'scheduled_at': meeting.scheduled_at.isoformat(),
            'location_type': meeting.location_type,
            'event_type': 'meeting_updated',
            'profile_picture': meeting.updated_by.profile_picture_url,
        }
        
        # Create action URL for the meeting
        action_url = f"/meetings/{meeting.id}/"
        
        # Send notifications to all team members
        for member in team_members:
            NotificationService.create_and_send(
                recipient=member,
                title=title,
                content=content,
                notification_type='team_meeting_update',
                related_object=meeting,
                priority='high',
                action_url=action_url,
                metadata=metadata
            )
    
    @staticmethod
    def _send_meeting_cancellation_notifications(meeting):
        """
        Send notifications to all team members about meeting cancellation
        
        Args:
            meeting (Meeting): The cancelled meeting
        """
        # Get all team members
        team_members = meeting.team.members.all()
        
        # Format meeting details
        team_name = meeting.team.name
        scheduled_time = meeting.scheduled_at.strftime("%A, %B %d, %Y at %I:%M %p")
        cancelled_by = meeting.updated_by.get_full_name() or meeting.updated_by.username
        
        title = f"Meeting Cancelled: {meeting.title}"
        content = (
            f"{cancelled_by} has cancelled the meeting for team '{team_name}'.\n\n"
            f"Meeting: {meeting.title}\n"
            f"Originally scheduled for: {scheduled_time}\n"
        )
        
        # Add metadata for rich rendering
        metadata = {
            'meeting_id': meeting.id,
            'team_id': meeting.team.id,
            'team_name': team_name,
            'cancelled_by': {
                'id': meeting.updated_by.id,
                'name': cancelled_by
            },
            'scheduled_at': meeting.scheduled_at.isoformat(),
            'event_type': 'meeting_cancelled',
            'profile_picture': meeting.updated_by.profile_picture_url,
        }
        
        # Create action URL for the team page
        action_url = f"/teams/{meeting.team.id}/"
        
        # Send notifications to all team members
        for member in team_members:
            NotificationService.create_and_send(
                recipient=member,
                title=title,
                content=content,
                notification_type='team_meeting_cancelled',
                related_object=meeting,
                priority='medium',
                action_url=action_url,
                metadata=metadata
            )
    
    # @staticmethod
    # def _send_attendance_response_notification(attendance):
    #     """
    #     Send notification to meeting creator about attendance response
        
    #     Args:
    #         attendance (MeetingAttendance): The updated attendance record
    #     """
    #     meeting = attendance.meeting
    #     attendee = attendance.attendee
    #     attendee_name = attendee.get_full_name() or attendee.username
        
    #     # Only send notification for confirmed or declined status
    #     if attendance.status not in [MeetingAttendance.STATUS_CONFIRMED, MeetingAttendance.STATUS_DECLINED]:
    #         return
            
    #     status_text = "confirmed attendance" if attendance.status == MeetingAttendance.STATUS_CONFIRMED else "declined attendance"
        
    #     title = f"Meeting Response: {attendee_name}"
    #     content = (
    #         f"{attendee_name} has {status_text} for the meeting '{meeting.title}' "
    #         f"scheduled for {meeting.scheduled_at.strftime('%A, %B %d at %I:%M %p')}.\n"
    #     )
        
    #     if attendance.response_notes:
    #         content += f"\nResponse notes: {attendance.response_notes}"
        
    #     # Add metadata for rich rendering
    #     metadata = {
    #         'meeting_id': meeting.id,
    #         'team_id': meeting.team.id,
    #         'attendee': {
    #             'id': attendee.id,
    #             'name': attendee_name
    #         },
    #         'status': attendance.status,
    #         'event_type': 'meeting_response'
    #     }
        
    #     # Create action URL for the meeting
    #     action_url = f"/meetings/{meeting.id}/"
        
    #     # Send notification to meeting creator
    #     NotificationService.create_and_send(
    #         recipient=meeting.scheduled_by,
    #         title=title,
    #         content=content,
    #         notification_type='meeting_response',
    #         related_object=meeting,
    #         priority='medium',
    #         action_url=action_url,
    #         metadata=metadata
    #     )
    
    @classmethod
    @database_sync_to_async
    def create_meeting_async(cls, teacher_user, team_id, meeting_data):
        """
        Async wrapper for creating meetings
        
        Args:
            teacher_user (User): Teacher creating the meeting
            team_id (int): ID of the team
            meeting_data (dict): Meeting details
            
        Returns:
            Meeting: The created meeting
        """
        return cls.create_meeting(teacher_user, team_id, meeting_data)
    
    @classmethod
    @database_sync_to_async
    def update_meeting_async(cls, meeting_id, teacher_user, meeting_data):
        """
        Async wrapper for updating meetings
        
        Args:
            meeting_id (int): ID of the meeting
            teacher_user (User): Teacher updating the meeting
            meeting_data (dict): Updated meeting details
            
        Returns:
            Meeting: The updated meeting
        """
        return cls.update_meeting(meeting_id, teacher_user, meeting_data)
    
    @classmethod
    @database_sync_to_async
    def cancel_meeting_async(cls, meeting_id, teacher_user):
        """
        Async wrapper for cancelling meetings
        
        Args:
            meeting_id (int): ID of the meeting
            teacher_user (User): Teacher cancelling the meeting
            
        Returns:
            Meeting: The cancelled meeting
        """
        return cls.cancel_meeting(meeting_id, teacher_user)
    
    # @classmethod
    # @database_sync_to_async
    # def update_attendance_status_async(cls, attendance_id, user, status, notes=""):
    #     """
    #     Async wrapper for updating attendance status
        
    #     Args:
    #         attendance_id (int): ID of the attendance record
    #         user (User): User updating their attendance
    #         status (str): New attendance status
    #         notes (str): Optional response notes
            
    #     Returns:
    #         MeetingAttendance: The updated attendance record
    #     """
    #     return cls.update_attendance_status(attendance_id, user, status, notes)