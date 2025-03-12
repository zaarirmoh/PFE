from rest_framework import serializers
from django.contrib.auth import get_user_model
from teams.models import Team, TeamInvitation, TeamMembership

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model"""
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate_name(self, value):
        """Ensure team name is unique (case-insensitive)"""
        # When updating, exclude current instance
        queryset = Team.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise serializers.ValidationError("A team with this name already exists.")
        return value
    
    def to_representation(self, instance):
        """Add additional fields to the response"""
        data = super().to_representation(instance)
        data.update({
            'owner': instance.owner.username if instance.owner else None,
            'member_count': instance.members.count(),
        })
        return data


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Serializer for TeamMembership model"""
    
    username = serializers.CharField(write_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = ['id', 'team', 'username', 'user', 'team_name', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'user', 'team_name']
        
    def get_user(self, obj):
        """Return username and display name of user"""
        return {
            'username': obj.user.username,
            'display_name': obj.user.get_full_name() or obj.user.username
        }
        
    def validate(self, data):
        """Validate membership creation/update"""
        # Get user instance from username
        try:
            username = data.pop('username')
            user = User.objects.get(username=username)
            data['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User does not exist"})

        # If this is a create operation, check for existing membership
        if not self.instance:
            if TeamMembership.objects.filter(team=data['team'], user=user).exists():
                raise serializers.ValidationError("User is already a member of this team")
                
        return data


class TeamInvitationSerializer(serializers.ModelSerializer):
    """Serializer for TeamInvitation model"""
    
    team_id = serializers.IntegerField(write_only=True, source='team')
    invitee_username = serializers.CharField(write_only=True, source='invitee')
    
    class Meta:
        model = TeamInvitation
        fields = ['id', 'team_id', 'invitee_username', 'status', 'created_at', 'updated_at']
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
            'status': instance.status,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at
        }


class InvitationResponseSerializer(serializers.Serializer):
    """Serializer for responding to an invitation"""
    
    action = serializers.ChoiceField(choices=['accept', 'decline'])