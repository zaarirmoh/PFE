from teams.models import Team, TeamMembership
from notifications.services import NotificationService
from django.core.exceptions import ValidationError

class TeamService:
    """Service class for team-related operations"""
    
    @classmethod
    def create_team_with_auto_name(cls, description, owner):
        """
        Creates a team with automatically generated name in the format 'Groupe X'
        
        Args:
            description: Team description
            owner: The user who will own the team
            
        Returns:
            The created team instance
        """
        # Get the highest team number from existing teams with "Groupe" prefix
        # Filter by owner's academic year to ensure numbers are unique per year
        student = owner.student
        academic_year = student.current_year
        
        last_team = Team.objects.filter(
            name__startswith='Groupe ',
            academic_year=academic_year
        ).order_by('-name').first()
        
        next_number = 1  # Default to 1 if no teams exist
        if last_team:
            try:
                # Extract the number from the last team name and increment
                last_number = int(last_team.name.replace('Groupe ', ''))
                next_number = last_number + 1
            except (ValueError, AttributeError):
                # If parsing fails, default to 1
                pass
        
        # Generate the team name with the next number
        generated_name = f"Groupe {next_number}"
        
        # Use the existing create_team method
        return cls.create_team(
            name=generated_name,
            description=description,
            owner=owner
        )

    
    @staticmethod
    def create_team(name, description, owner):
        """
        Create a new team with the given owner
        
        Args:
            name: Team name
            description: Team description
            owner: User who will be the team owner
            
        Returns:
            Team: The created team instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Use the model's factory method instead of manual creation
        team = Team.create_team(owner, name, description)
        
        NotificationService.create_and_send(
                recipient=owner,
                title="Team Created",
                content=f"You created the team '{team.name}'",
                notification_type='team_update',
                related_object=team,
                priority='low',
                metadata={
                    'team_id': team.id,
                    'event_type': 'team_created'
                }
            )
        return team
    
    @staticmethod
    def update_team(team, user, **update_data):
        """
        Update a team with the given data
        
        Args:
            team: Team instance to update
            user: User performing the update
            update_data: Data to update (name, description)
            
        Returns:
            Team: The updated team instance
        """
        old_name = team.name
        
        # Update fields
        if 'name' in update_data:
            team.name = update_data['name']
        if 'description' in update_data:
            team.description = update_data['description']
            
        team.updated_by = user
        team.save()
        
        # Send notification if name changed
        if old_name != team.name:
            NotificationService.create_and_send(
                recipient=user,
                title="Team Updated",
                content=f"Team name changed from '{old_name}' to '{team.name}'",
                notification_type='team_update',
                related_object=team,
                priority='medium',
                metadata={
                    'team_id': team.id,
                    'old_name': old_name,
                    'new_name': team.name,
                    'event_type': 'team_renamed'
                }
            )
        
        return team
    
    @staticmethod
    def delete_team(team, user):
        """
        Delete a team and notify the user
        
        Args:
            team: Team instance to delete
            user: User performing the deletion
        """
        team_name = team.name
        team_id = team.id
        team.delete()
        
        # Send notification
        NotificationService.create_and_send(
            recipient=user,
            title="Team Deleted",
            content=f"Team '{team_name}' was deleted",
            notification_type='team_update',
            priority='medium',
            metadata={
                'team_name': team_name,
                'event_type': 'team_deleted'
            }
        )
    
    @staticmethod
    def add_member(team, user, new_member, role=TeamMembership.ROLE_MEMBER):
        """
        Add a member to a team
        
        Args:
            team: Team instance
            user: User performing the action (for notification)
            new_member: User to add as a member
            role: Role for the new member (default: member)
            
        Returns:
            TeamMembership: The created membership
            
        Raises:
            ValidationError: If validation fails
        """
        # Create membership - validation will be handled by the model's clean method
        membership = TeamMembership(
            user=new_member,
            team=team,
            role=role
        )
        # This will trigger validation via full_clean in the save method
        membership.save()
        
        # Send notifications
        NotificationService.create_and_send(
            recipient=new_member,
            title="Team Invitation",
            content=f"You have been added to team '{team.name}'",
            notification_type='team_update',
            related_object=team,
            priority='medium',
            metadata={
                'team_id': team.id,
                'event_type': 'member_added'
            }
        )
        
        # Notify team owner
        owner = team.owner
        if owner and owner != user:
            NotificationService.create_and_send(
                recipient=owner,
                title="New Team Member",
                content=f"{new_member.username} has been added to your team '{team.name}'",
                notification_type='team_update',
                related_object=team,
                priority='low',
                metadata={
                    'team_id': team.id,
                    'member_id': new_member.id,
                    'event_type': 'member_added'
                }
            )
            
        return membership
    
    @staticmethod
    def remove_member(team, user, member_to_remove):
        """
        Remove a member from a team
        
        Args:
            team: Team instance
            user: User performing the action (for notification)
            member_to_remove: User to remove from the team
            
        Raises:
            ValidationError: If trying to remove the owner
        """
        # Check if the member is the owner
        membership = TeamMembership.objects.filter(
            team=team,
            user=member_to_remove
        ).first()
        
        if not membership:
            raise ValidationError(f"User {member_to_remove.username} is not a member of this team.")
            
        if membership.role == TeamMembership.ROLE_OWNER:
            raise ValidationError("Cannot remove the team owner. Transfer ownership first.")
        
        # Remove the member
        membership.delete()
        
        # Send notifications
        NotificationService.create_and_send(
            recipient=member_to_remove,
            title="Team Membership Ended",
            content=f"You have been removed from team '{team.name}'",
            notification_type='team_update',
            priority='medium',
            metadata={
                'team_name': team.name,
                'event_type': 'member_removed'
            }
        )
        
        # Notify team owner
        owner = team.owner
        if owner and owner != user:
            NotificationService.create_and_send(
                recipient=owner,
                title="Team Member Removed",
                content=f"{member_to_remove.username} has been removed from your team '{team.name}'",
                notification_type='team_update',
                related_object=team,
                priority='low',
                metadata={
                    'team_id': team.id,
                    'event_type': 'member_removed'
                }
            )
    
    @staticmethod
    def transfer_ownership(team, current_owner, new_owner):
        """
        Transfer team ownership to another member
        
        Args:
            team: Team instance
            current_owner: Current team owner
            new_owner: User to transfer ownership to
            
        Raises:
            ValidationError: If validation fails
        """
        # Verify current owner
        if team.owner != current_owner:
            raise ValidationError("Only the team owner can transfer ownership.")
        
        # Check if new owner is a member
        new_owner_membership = TeamMembership.objects.filter(
            team=team,
            user=new_owner
        ).first()
        
        if not new_owner_membership:
            raise ValidationError(f"User {new_owner.username} must be a team member before becoming owner.")
        
        # Update roles
        current_owner_membership = TeamMembership.objects.get(
            team=team,
            user=current_owner
        )
        
        current_owner_membership.role = TeamMembership.ROLE_MEMBER
        new_owner_membership.role = TeamMembership.ROLE_OWNER
        
        current_owner_membership.save()
        new_owner_membership.save()
        
        # Send notifications
        NotificationService.create_and_send(
            recipient=new_owner,
            title="Team Ownership Transferred",
            content=f"You are now the owner of team '{team.name}'",
            notification_type='team_update',
            related_object=team,
            priority='high',
            metadata={
                'team_id': team.id,
                'event_type': 'ownership_transferred'
            }
        )
        
        NotificationService.create_and_send(
            recipient=current_owner,
            title="Team Ownership Transferred",
            content=f"You have transferred ownership of team '{team.name}' to {new_owner.username}",
            notification_type='team_update',
            related_object=team,
            priority='medium',
            metadata={
                'team_id': team.id,
                'event_type': 'ownership_transferred'
            }
        )
    
    @staticmethod
    def check_student_eligibility(student_user, team):
        """
        Check if a student is eligible to join a specific team
        
        Args:
            student_user: The User object representing a student
            team: The Team to check eligibility for
            
        Returns:
            bool: True if eligible, False otherwise
        """
        try:
            # This will raise ValidationError if not eligible
            membership = TeamMembership(
                user=student_user,
                team=team,
                role=TeamMembership.ROLE_MEMBER
            )
            membership.clean()
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def get_user_teams(user):
        """
        Get teams that a user is a member of
        
        Args:
            user: User to get teams for
            
        Returns:
            QuerySet: Teams the user is a member of
        """
        return Team.objects.filter(members=user)
    
    @staticmethod
    def get_team_members(team):
        """
        Get members of a team with their roles
        
        Args:
            team: Team to get members for
            
        Returns:
            QuerySet: TeamMembership objects for the team
        """
        return TeamMembership.objects.filter(team=team).select_related('user')
    
    @staticmethod
    def get_filterable_queryset():
        """
        Get an optimized queryset for list views with related data
        
        Returns:
            QuerySet: Optimized Team queryset
        """
        return Team.objects.all().prefetch_related(
            'members', 
            'teammembership_set'
        )