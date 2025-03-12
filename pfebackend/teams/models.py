from django.db import models
from django.conf import settings
from common.models import TimeStampedModel, AuditableModel

class Team(AuditableModel):
    """
    Represents a team that can have multiple members with different roles.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='TeamMembership',
        related_name='teams'
    )
    
    def __str__(self):
        return self.name
    
    @property
    def owner(self):
        """Returns the owner of the team"""
        return self.members.filter(teammembership__role='owner').first()


class TeamMembership(models.Model):
    """
    Represents the relationship between a User and a Team,
    including the role of the user in the team.
    """
    ROLE_OWNER = 'owner'
    ROLE_MEMBER = 'member'
    
    ROLE_CHOICES = (
        (ROLE_OWNER, 'Owner'),
        (ROLE_MEMBER, 'Member'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'team')
        
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.get_role_display()})"


class TeamInvitation(TimeStampedModel):
    """
    Represents an invitation to join a team.
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
    )
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_invitations'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    class Meta:
        unique_together = ('team', 'invitee', 'status')
        
    def __str__(self):
        return f"{self.inviter.username} invited {self.invitee.username} to {self.team.name}"