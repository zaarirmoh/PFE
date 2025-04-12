from django.db import transaction
from django.utils.html import escape
from django.core.exceptions import ValidationError
from channels.db import database_sync_to_async
from teams.models import TeamMembership, TeamInvitation
import logging

logger = logging.getLogger(__name__)


class TeamInvitationService:
    """Service class for team invitation operations"""
    
    @staticmethod
    def create_invitation(team, inviter, invitee, message=""):
        """
        Create a team invitation and send notification
        
        Args:
            team (Team): Team to invite to
            inviter (User): User sending the invitation
            invitee (User): User receiving the invitation
            message (str): Optional message to include with invitation
            
        Returns:
            TeamInvitation: The created invitation
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            with transaction.atomic():
                # Create invitation - validation will be handled by the model's clean method
                invitation = TeamInvitation(
                    team=team,
                    inviter=inviter,
                    invitee=invitee,
                    status=TeamInvitation.STATUS_PENDING,
                    message=message
                )
                
                # This will trigger validation via full_clean in the save method
                invitation.save()
                
                # Send notification
                from notifications.services import NotificationService
                
                # Format inviter name
                inviter_name = inviter.get_full_name() or inviter.username
                team_name = escape(team.name)
                
                # Create better formatted invitation content
                title = f"Team Invitation: {team_name}"
                content = f"{inviter_name} has invited you to join the team '{team_name}'"
                
                if message:
                    content += f"\n\nMessage: {message}"
                
                # Metadata for rich rendering
                metadata = {
                    'invitation_id': invitation.id,
                    'team_id': team.id,
                    'team_name': team.name,
                    'inviter': {
                        'id': inviter.id,
                        'username': inviter.username,
                        'name': inviter_name
                    }
                }
                
                # Create action URL for the invitation
                action_url = f"/invitations/{invitation.id}/"
                
                NotificationService.create_and_send(
                    recipient=invitee,
                    title=title,
                    content=content,
                    notification_type='team_invitation',
                    related_object=invitation,
                    priority='medium',
                    action_url=action_url,
                    metadata=metadata
                )
                
                return invitation
                
        except ValidationError as e:
            logger.error(f"Validation error creating team invitation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating team invitation: {str(e)}")
            raise
    
    @staticmethod
    def process_invitation_response(user, invitation_id, response):
        """
        Process a user's response to a team invitation
        
        Args:
            user (User): User responding to invitation
            invitation_id (int): ID of the invitation
            response (str): 'accept' or 'decline'
            
        Returns:
            tuple: (success, result_data)
        """
        try:
            invitation = TeamInvitation.objects.select_related('team', 'inviter').get(
                id=invitation_id,
                invitee=user,
                status=TeamInvitation.STATUS_PENDING
            )
            
            team = invitation.team
            inviter = invitation.inviter
            
            result_data = {
                'team_id': team.id,
                'team_name': team.name
            }
            
            if response == 'accept':
                try:
                    with transaction.atomic():
                        # Use the model's accept method which handles validation
                        invitation.accept()
                        
                        # Notify the inviter about acceptance
                        from notifications.services import NotificationService
                        
                        member_name = user.get_full_name() or user.username
                        
                        NotificationService.create_and_send(
                            recipient=inviter,
                            title=f"Invitation Accepted",
                            content=f"{member_name} has accepted your invitation to join '{team.name}'",
                            notification_type='team_membership',
                            related_object=team,
                            action_url=f"/teams/{team.id}/members/",
                            metadata={
                                'team_id': team.id,
                                'member_id': user.id,
                                'member_name': member_name,
                                'event_type': 'invitation_accepted'
                            }
                        )
                        
                        # Get the new member's role
                        membership = TeamMembership.objects.get(user=user, team=team)
                        result_data['role'] = membership.role
                    
                    return True, result_data
                    
                except ValidationError as e:
                    return False, {'error': str(e)}
                
            elif response == 'decline':
                try:
                    # Use the model's decline method
                    invitation.decline()
                    
                    # Notify inviter about declination
                    from notifications.services import NotificationService
                    
                    member_name = user.get_full_name() or user.username
                    
                    NotificationService.create_and_send(
                        recipient=inviter,
                        title=f"Invitation Declined",
                        content=f"{member_name} has declined your invitation to join '{team.name}'",
                        notification_type='team_update',
                        related_object=team,
                        priority='low',
                        metadata={
                            'team_id': team.id,
                            'event_type': 'invitation_declined'
                        }
                    )
                    
                    return True, result_data
                
                except ValidationError as e:
                    return False, {'error': str(e)}
                
            return False, {'error': 'Invalid response. Must be "accept" or "decline".'}
            
        except TeamInvitation.DoesNotExist:
            return False, {'error': 'Invitation not found or already processed'}
        except Exception as e:
            logger.error(f"Error processing invitation response: {str(e)}")
            return False, {'error': str(e)}
    
    @classmethod
    @database_sync_to_async
    def process_invitation_response_async(cls, user, invitation_id, response):
        """
        Async wrapper for processing invitation responses
        
        Args:
            user (User): User responding to invitation
            invitation_id (int): ID of the invitation
            response (str): 'accept' or 'decline'
            
        Returns:
            tuple: (success, result_data)
        """
        return cls.process_invitation_response(user, invitation_id, response)
    
    @staticmethod
    def get_user_pending_invitations(user):
        """
        Get pending invitations for a user
        
        Args:
            user (User): User to get invitations for
            
        Returns:
            QuerySet: Pending invitations for the user
        """
        return TeamInvitation.objects.filter(
            invitee=user,
            status=TeamInvitation.STATUS_PENDING
        ).select_related('team', 'inviter')
    
    @staticmethod
    def cancel_invitation(invitation_id, cancelling_user):
        """
        Cancel a pending invitation
        
        Args:
            invitation_id (int): ID of the invitation
            cancelling_user (User): User cancelling the invitation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Only allow the inviter or a team owner to cancel
            invitation = TeamInvitation.objects.select_related('team').get(
                id=invitation_id,
                status=TeamInvitation.STATUS_PENDING
            )
            
            is_inviter = invitation.inviter == cancelling_user
            is_team_owner = TeamMembership.objects.filter(
                team=invitation.team,
                user=cancelling_user,
                role=TeamMembership.ROLE_OWNER
            ).exists()
            
            if not (is_inviter or is_team_owner):
                return False
                
            # Update invitation status using the constants from the model
            invitation.status = TeamInvitation.STATUS_CANCELLED
            invitation.save(update_fields=['status', 'updated_at'])
            
            # Notify the invitee
            from notifications.services import NotificationService
            
            NotificationService.create_and_send(
                recipient=invitation.invitee,
                title="Invitation Cancelled",
                content=f"Your invitation to join '{invitation.team.name}' has been cancelled",
                notification_type='team_update',
                related_object=invitation.team,
                priority='low',
                metadata={
                    'team_id': invitation.team.id,
                    'event_type': 'invitation_cancelled'
                }
            )
            
            return True
            
        except TeamInvitation.DoesNotExist:
            return False