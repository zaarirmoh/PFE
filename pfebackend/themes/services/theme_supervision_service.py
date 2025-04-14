from django.db import transaction
from django.utils.html import escape
from django.core.exceptions import ValidationError
from channels.db import database_sync_to_async
from themes.models import Theme, ThemeSupervisionRequest
from teams.models import TeamMembership
import logging

logger = logging.getLogger(__name__)


class ThemeSupervisionService:
    """Service class for theme supervision request operations"""
    
    # Update the create_supervision_request method to include the invitee parameter
    @staticmethod
    def create_supervision_request(theme, team, requester, invitee=None, message=""):
        """
        Create a theme supervision request and send notification
        
        Args:
            theme (Theme): Theme to request supervision for
            team (Team): Team requesting supervision
            requester (User): User making the request (must be team owner)
            invitee (User): User being invited to supervise (defaults to theme proposer)
            message (str): Optional message to include with request
            
        Returns:
            ThemeSupervisionRequest: The created request
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            with transaction.atomic():
                # Verify requester is a team owner
                is_owner = TeamMembership.objects.filter(
                    team=team,
                    user=requester,
                    role=TeamMembership.ROLE_OWNER
                ).exists()
                
                if not is_owner:
                    raise ValidationError("Only team owners can request theme supervision.")
                
                # Set default invitee to theme proposer if not provided
                if invitee is None:
                    invitee = theme.proposed_by
                
                # Check for existing pending request
                existing_request = ThemeSupervisionRequest.objects.filter(
                    team=team,
                    theme=theme,
                    invitee=invitee,
                    status=ThemeSupervisionRequest.STATUS_PENDING
                ).first()
                
                if existing_request:
                    return existing_request
                
                # Create supervision request - validation will be handled by the model's clean method
                supervision_request = ThemeSupervisionRequest(
                    theme=theme,
                    team=team,
                    requester=requester,
                    invitee=invitee,
                    status=ThemeSupervisionRequest.STATUS_PENDING,
                    message=message
                )
                
                # This will trigger validation via full_clean in the save method
                supervision_request.save()
                
                # Send notification to theme supervisor
                from notifications.services import NotificationService
                
                # Format requester name and team name
                requester_name = requester.get_full_name() or requester.username
                team_name = escape(team.name)
                theme_title = escape(theme.title)
                
                # Create better formatted request content
                title = f"Theme Supervision Request: {theme_title}"
                content = f"{requester_name} has requested supervision for theme '{theme_title}' on behalf of team '{team_name}'"
                
                if message:
                    content += f"\n\nMessage: {message}"
                
                # Metadata for rich rendering
                metadata = {
                    'request_id': supervision_request.id,
                    'theme_id': theme.id,
                    'theme_title': theme.title,
                    'team_id': team.id,
                    'team_name': team.name,
                    'requester': {
                        'id': requester.id,
                        'username': requester.username,
                        'name': requester_name
                    }
                }
                
                # Create action URL for the supervision request
                action_url = f"/supervision-requests/{supervision_request.id}/"
                
                # Send notification to the invitee
                NotificationService.create_and_send(
                    recipient=invitee,
                    title=title,
                    content=content,
                    notification_type='theme_supervision_request',
                    related_object=supervision_request,
                    priority='medium',
                    action_url=action_url,
                    metadata=metadata
                )
                
                # Only notify co-supervisors if the main supervisor is invited
                if invitee == theme.proposed_by:
                    for co_supervisor in theme.co_supervisors.all():
                        NotificationService.create_and_send(
                            recipient=co_supervisor,
                            title=title,
                            content=content,
                            notification_type='theme_supervision_request',
                            related_object=supervision_request,
                            priority='medium',
                            action_url=action_url,
                            metadata=metadata
                        )
                
                return supervision_request
                
        except ValidationError as e:
            logger.error(f"Validation error creating supervision request: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating supervision request: {str(e)}")
            raise
    
    @staticmethod
    def process_supervision_request_response(user, request_id, response, message=""):
        """
        Process a supervisor's response to a supervision request
        
        Args:
            user (User): User responding to request (must be theme proposer or co-supervisor)
            request_id (int): ID of the supervision request
            response (str): 'accept' or 'decline'
            message (str): Optional response message
            
        Returns:
            tuple: (success, result_data)
        """
        try:
            supervision_request = ThemeSupervisionRequest.objects.select_related(
                'theme', 'team', 'requester'
            ).get(
                id=request_id,
                status=ThemeSupervisionRequest.STATUS_PENDING
            )
            
            theme = supervision_request.theme
            team = supervision_request.team
            requester = supervision_request.requester
            
            # Verify user is the theme proposer or a co-supervisor
            is_proposer = theme.proposed_by == user
            is_co_supervisor = theme.co_supervisors.filter(id=user.id).exists()
            
            if not (is_proposer or is_co_supervisor):
                return False, {'error': 'Only the theme proposer or co-supervisors can respond to supervision requests'}
            
            result_data = {
                'theme_id': theme.id,
                'theme_title': theme.title,
                'team_id': team.id,
                'team_name': team.name
            }
            
            if response == 'accept':
                try:
                    with transaction.atomic():
                        # Use the model's accept method
                        supervision_request.accept(response_message=message)
                        
                        # Notify the team owner about acceptance
                        from notifications.services import NotificationService
                        
                        supervisor_name = user.get_full_name() or user.username
                        
                        NotificationService.create_and_send(
                            recipient=requester,
                            title=f"Supervision Request Accepted",
                            content=f"{supervisor_name} has accepted your request for supervision of theme '{theme.title}'",
                            notification_type='theme_assignment',
                            related_object=team.assigned_theme,
                            action_url=f"/teams/{team.id}/theme/",
                            metadata={
                                'team_id': team.id,
                                'theme_id': theme.id,
                                'theme_title': theme.title,
                                'supervisor_name': supervisor_name,
                                'event_type': 'supervision_request_accepted'
                            }
                        )
                        
                        # Also notify other team members
                        team_members = team.members.exclude(id=requester.id)
                        for member in team_members:
                            NotificationService.create_and_send(
                                recipient=member,
                                title=f"Theme Assigned to Your Team",
                                content=f"Your team has been assigned the theme '{theme.title}', supervised by {supervisor_name}",
                                notification_type='theme_assignment',
                                related_object=team.assigned_theme,
                                action_url=f"/teams/{team.id}/theme/",
                                metadata={
                                    'team_id': team.id,
                                    'theme_id': theme.id,
                                    'theme_title': theme.title,
                                    'supervisor_name': supervisor_name,
                                    'event_type': 'theme_assigned'
                                }
                            )
                    
                    return True, result_data
                    
                except ValidationError as e:
                    return False, {'error': str(e)}
                
            elif response == 'decline':
                try:
                    # Use the model's decline method
                    supervision_request.decline(response_message=message)
                    
                    # Notify the team owner about declination
                    from notifications.services import NotificationService
                    
                    supervisor_name = user.get_full_name() or user.username
                    
                    NotificationService.create_and_send(
                        recipient=requester,
                        title=f"Supervision Request Declined",
                        content=f"{supervisor_name} has declined your request for supervision of theme '{theme.title}'",
                        notification_type='theme_update',
                        related_object=theme,
                        priority='medium',
                        metadata={
                            'team_id': team.id,
                            'theme_id': theme.id,
                            'theme_title': theme.title,
                            'supervisor_name': supervisor_name,
                            'event_type': 'supervision_request_declined',
                            'response_message': message
                        }
                    )
                    
                    return True, result_data
                
                except ValidationError as e:
                    return False, {'error': str(e)}
                
            return False, {'error': 'Invalid response. Must be "accept" or "decline".'}
            
        except ThemeSupervisionRequest.DoesNotExist:
            return False, {'error': 'Supervision request not found or already processed'}
        except Exception as e:
            logger.error(f"Error processing supervision request response: {str(e)}")
            return False, {'error': str(e)}
    
    @classmethod
    @database_sync_to_async
    def process_supervision_request_response_async(cls, user, request_id, response, message=""):
        """
        Async wrapper for processing supervision request responses
        
        Args:
            user (User): User responding to request
            request_id (int): ID of the supervision request
            response (str): 'accept' or 'decline'
            message (str): Optional response message
            
        Returns:
            tuple: (success, result_data)
        """
        return cls.process_supervision_request_response(user, request_id, response, message)
    
    @staticmethod
    def get_user_pending_supervision_requests(user):
        """
        Get pending supervision requests for a user (as supervisor)
        
        Args:
            user (User): Supervisor to get requests for
            
        Returns:
            QuerySet: Pending supervision requests for the user
        """
        # Get themes where user is proposer or co-supervisor
        proposed_themes = Theme.objects.filter(proposed_by=user)
        co_supervised_themes = Theme.objects.filter(co_supervisors=user)
        
        # Combine the themes
        all_supervised_themes = proposed_themes.union(co_supervised_themes)
        
        # Find pending requests for these themes
        return ThemeSupervisionRequest.objects.filter(
            theme__in=all_supervised_themes,
            status=ThemeSupervisionRequest.STATUS_PENDING
        ).select_related('theme', 'team', 'requester')
    
    @staticmethod
    def get_team_supervision_requests(team):
        """
        Get supervision requests made by a team
        
        Args:
            team (Team): Team to get requests for
            
        Returns:
            QuerySet: Supervision requests made by the team
        """
        return ThemeSupervisionRequest.objects.filter(
            team=team
        ).select_related('theme', 'requester')
    
    @staticmethod
    def cancel_supervision_request(request_id, user):
        """
        Cancel a pending supervision request
        
        Args:
            request_id (int): ID of the supervision request
            user (User): User cancelling the request (must be team owner)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the request
            supervision_request = ThemeSupervisionRequest.objects.select_related('team', 'theme').get(
                id=request_id,
                status=ThemeSupervisionRequest.STATUS_PENDING
            )
            
            team = supervision_request.team
            
            # Verify user is a team owner
            is_owner = TeamMembership.objects.filter(
                team=team,
                user=user,
                role=TeamMembership.ROLE_OWNER
            ).exists()
            
            if not is_owner:
                return False
                
            # Update request status
            supervision_request.status = ThemeSupervisionRequest.STATUS_CANCELLED
            supervision_request.save(update_fields=['status', 'updated_at'])
            
            # Notify the theme proposer
            from notifications.services import NotificationService
            
            theme = supervision_request.theme
            requester_name = user.get_full_name() or user.username
            
            NotificationService.create_and_send(
                recipient=theme.proposed_by,
                title="Supervision Request Cancelled",
                content=f"{requester_name} has cancelled the request for supervision of theme '{theme.title}' for team '{team.name}'",
                notification_type='theme_update',
                related_object=theme,
                priority='low',
                metadata={
                    'team_id': team.id,
                    'theme_id': theme.id,
                    'theme_title': theme.title,
                    'event_type': 'supervision_request_cancelled'
                }
            )
            
            # Also notify co-supervisors
            for co_supervisor in theme.co_supervisors.all():
                NotificationService.create_and_send(
                    recipient=co_supervisor,
                    title="Supervision Request Cancelled",
                    content=f"{requester_name} has cancelled the request for supervision of theme '{theme.title}' for team '{team.name}'",
                    notification_type='theme_update',
                    related_object=theme,
                    priority='low',
                    metadata={
                        'team_id': team.id,
                        'theme_id': theme.id,
                        'theme_title': theme.title,
                        'event_type': 'supervision_request_cancelled'
                    }
                )
            
            return True
            
        except ThemeSupervisionRequest.DoesNotExist:
            return False