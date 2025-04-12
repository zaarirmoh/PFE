from rest_framework import serializers
from django.contrib.auth import get_user_model
from teams.models import Team, TeamInvitation, TeamMembership

User = get_user_model()


class TeamInvitationSerializer(serializers.ModelSerializer):
    """Serializer for TeamInvitation model"""
    
    team_id = serializers.IntegerField(write_only=True, source='team')
    invitee_username = serializers.CharField(write_only=True, source='invitee')
    message = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = TeamInvitation
        fields = ['id', 'team_id', 'invitee_username', 'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate invitation creation"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
            
        # Set inviter to current user
        data['inviter'] = request.user
            
        # Get team instance
        try:
            team_id = data.get('team')
            team = Team.objects.get(id=team_id)
            data['team'] = team
        except Team.DoesNotExist:
            raise serializers.ValidationError({"team_id": "Team does not exist"})

        # Get invitee instance
        try:
            invitee_username = data.get('invitee')
            invitee = User.objects.get(username=invitee_username)
            data['invitee'] = invitee
        except User.DoesNotExist:
            raise serializers.ValidationError({"invitee_username": "User does not exist"})

        # Prevent self-invitation
        if invitee == request.user:
            raise serializers.ValidationError("You cannot invite yourself")
        
        # Check if user is already a member
        if TeamMembership.objects.filter(team=team, user=invitee).exists():
            raise serializers.ValidationError("This user is already a team member")
            
        # Check for existing pending invitation
        if TeamInvitation.objects.filter(
            team=team, 
            invitee=invitee, 
            status=TeamInvitation.STATUS_PENDING
        ).exists():
            raise serializers.ValidationError("A pending invitation already exists for this user")
            
        # Check if team is already at capacity
        if not team.has_capacity:
            raise serializers.ValidationError(
                f"Team '{team.name}' has reached its maximum capacity of {team.maximum_members} members."
            )
            
        return data

    def to_representation(self, instance):
        """Custom representation for invitation"""
        return {
            'id': instance.id,
            'team': {
                'id': instance.team.id,
                'name': instance.team.name
            },
            'inviter': {
                'username': instance.inviter.username
            },
            'invitee': {
                'username': instance.invitee.username
            },
            'message': instance.message,
            'status': instance.status,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at
        }


class InvitationResponseSerializer(serializers.Serializer):
    """Serializer for responding to an invitation"""
    
    action = serializers.ChoiceField(choices=['accept', 'decline'])