from django.db import transaction
from django.utils.html import escape
from teams.models import TeamMembership, TeamJoinRequest
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class TeamJoinRequestService:
    """Service class for team join request operations"""
    
    @staticmethod
    def create_join_request(team, requester, message=""):
        """
        Create a team join request and send notification
        
        Args:
            team (Team): Team to join
            requester (User): User requesting to join
            message (str): Optional message from requester
            
        Returns:
            TeamJoinRequest: The created request
        """
        try:
            with transaction.atomic():
                # Check if user is already a member
                if TeamMembership.objects.filter(team=team, user=requester).exists():
                    raise ValueError("You are already a member of this team")
                
                # Check for existing pending request
                existing_request = TeamJoinRequest.objects.filter(
                    team=team,
                    requester=requester,
                    status=TeamJoinRequest.STATUS_PENDING
                ).first()
                
                if existing_request:
                    return existing_request
                
                # Create join request - validation will happen in the model's clean method
                join_request = TeamJoinRequest.objects.create(
                    team=team,
                    requester=requester,
                    message=message,
                    status=TeamJoinRequest.STATUS_PENDING
                )
                
                # Send notification to team owners
                from notifications.services import NotificationService
                
                # Get team owners
                team_owners = team.members.filter(
                    teammembership__role=TeamMembership.ROLE_OWNER
                )
                
                # Format requester name
                requester_name = requester.get_full_name() or requester.username
                team_name = escape(team.name)
                
                for owner in team_owners:
                    # Create notification content
                    title = f"Team Join Request: {team_name}"
                    content = f"{requester_name} has requested to join your team '{team_name}'"
                    
                    # Add message if provided
                    if message:
                        content += f"\nMessage: \"{message}\""
                    
                    # Metadata for rich rendering
                    metadata = {
                        'join_request_id': join_request.id,
                        'team_id': team.id,
                        'team_name': team.name,
                        'requester': {
                            'id': requester.id,
                            'username': requester.username,
                            'name': requester_name,
                            'profile_picture': requester.profile_picture_url,
                        }
                    }
                    
                    # Create action URL for the request
                    action_url = f"/join-requests/{join_request.id}/"
                    
                    NotificationService.create_and_send(
                        recipient=owner,
                        title=title,
                        content=content,
                        notification_type='team_join_request',
                        related_object=join_request,
                        priority='medium',
                        action_url=action_url,
                        metadata=metadata
                    )
                
                return join_request
                
        except Exception as e:
            logger.error(f"Error creating team join request: {str(e)}")
            raise
    
    @staticmethod
    def process_join_request_response(user, request_id, response):
        """
        Process a team owner's response to a join request
        
        Args:
            user (User): User responding to request (must be team owner)
            request_id (int): ID of the join request
            response (str): 'accept' or 'decline'
            
        Returns:
            tuple: (success, result_data)
        """
        try:
            join_request = TeamJoinRequest.objects.select_related('team', 'requester').get(
                id=request_id,
                status=TeamJoinRequest.STATUS_PENDING
            )
            
            team = join_request.team
            requester = join_request.requester
            
            # Verify user is a team owner
            is_owner = TeamMembership.objects.filter(
                team=team,
                user=user,
                role=TeamMembership.ROLE_OWNER
            ).exists()
            
            if not is_owner:
                return False, {'error': 'Only team owners can respond to join requests'}
            
            result_data = {
                'team_id': team.id,
                'team_name': team.name,
                'requester_username': requester.username
            }
            
            if response == 'accept':
                try:
                    with transaction.atomic():
                        # Use the model's accept method which handles validation and membership creation
                        join_request.accept()
                        
                        # Notify the requester about acceptance
                        from notifications.services import NotificationService
                        
                        owner_name = user.get_full_name() or user.username
                        
                        NotificationService.create_and_send(
                            recipient=requester,
                            title=f"Join Request Accepted",
                            content=f"{owner_name} has accepted your request to join '{team.name}'",
                            notification_type='team_membership',
                            related_object=team,
                            action_url=f"/teams/{team.id}/",
                            metadata={
                                'team_id': team.id,
                                'owner_name': owner_name,
                                'event_type': 'join_request_accepted'
                            }
                        )
                        
                        # Get the newly created membership
                        membership = TeamMembership.objects.get(
                            user=requester,
                            team=team
                        )
                        result_data['role'] = membership.role
                    
                    return True, result_data
                except Exception as e:
                    logger.error(f"Error accepting join request: {str(e)}")
                    return False, {'error': str(e)}
                
            elif response == 'decline':
                try:
                    # Use the model's decline method
                    join_request.decline()
                    
                    # Notify requester about declination
                    from notifications.services import NotificationService
                    
                    owner_name = user.get_full_name() or user.username
                    
                    NotificationService.create_and_send(
                        recipient=requester,
                        title=f"Join Request Declined",
                        content=f"{owner_name} has declined your request to join '{team.name}'",
                        notification_type='team_update',
                        related_object=team,
                        priority='medium',
                        metadata={
                            'team_id': team.id,
                            'owner_name': owner_name,
                            'event_type': 'join_request_declined'
                        }
                    )
                    
                    return True, result_data
                except Exception as e:
                    logger.error(f"Error declining join request: {str(e)}")
                    return False, {'error': str(e)}
                
            return False, None
            
        except TeamJoinRequest.DoesNotExist:
            return False, {'error': 'Join request not found or already processed'}
        except Exception as e:
            logger.error(f"Error processing join request response: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def get_team_pending_requests(team):
        """
        Get pending join requests for a team
        
        Args:
            team (Team): Team to get requests for
            
        Returns:
            QuerySet: Pending join requests for the team
        """
        return TeamJoinRequest.objects.filter(
            team=team,
            status=TeamJoinRequest.STATUS_PENDING
        ).select_related('requester')
    
    @staticmethod
    def get_user_pending_requests(user):
        """
        Get pending join requests created by a user
        
        Args:
            user (User): User to get requests for
            
        Returns:
            QuerySet: Pending join requests created by the user
        """
        return TeamJoinRequest.objects.filter(
            requester=user,
            status=TeamJoinRequest.STATUS_PENDING
        ).select_related('team')
    
    @staticmethod
    def cancel_join_request(request_id, user):
        """
        Cancel a pending join request
        
        Args:
            request_id (int): ID of the join request
            user (User): User cancelling the request (must be requester)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Only allow the requester to cancel
            join_request = TeamJoinRequest.objects.select_related('team').get(
                id=request_id,
                requester=user,
                status=TeamJoinRequest.STATUS_PENDING
            )
                
            # Update request status
            join_request.status = TeamJoinRequest.STATUS_CANCELLED
            join_request.save(update_fields=['status', 'updated_at'])
            
            # Notify team owners
            from notifications.services import NotificationService
            
            team = join_request.team
            requester_name = user.get_full_name() or user.username
            
            # Get team owners
            team_owners = team.members.filter(
                teammembership__role=TeamMembership.ROLE_OWNER
            )
            
            for owner in team_owners:
                NotificationService.create_and_send(
                    recipient=owner,
                    title="Join Request Cancelled",
                    content=f"{requester_name} has cancelled their request to join '{team.name}'",
                    notification_type='team_update',
                    related_object=team,
                    priority='low',
                    metadata={
                        'team_id': team.id,
                        'event_type': 'join_request_cancelled'
                    }
                )
            
            return True
            
        except TeamJoinRequest.DoesNotExist:
            return False