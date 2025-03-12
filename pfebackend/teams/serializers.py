# api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from teams.models import Team, TeamInvitation, TeamMembership

User = get_user_model()

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'
        
    def validate_name(self, value):
        # Ensure team name is unique (case-insensitive)
        if Team.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A team with this name already exists.")
        return value
    def to_representation(self, instance):
        # Add additional fields to the response
        return {
            'id': instance.id,
            'name': instance.name,
            'description': instance.description,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'owner': instance.members.filter(teammembership__role='owner').first().username,
            'member_count': instance.members.count(),
        }


class TeamMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'
        
    def validate(self, data):
        # Get team instance
        try:
            data['team'] = Team.objects.get(id=data.pop('team'))
        except Team.DoesNotExist:
            raise serializers.ValidationError("Team does not exist")

        # Get user instance
        try:
            data['user'] = User.objects.get(username=data.pop('user'))
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

        # Prevent duplicate memberships
        if TeamMembership.objects.filter(team=data['team'], user=data['user']).exists():
            raise serializers.ValidationError("User is already a member of this team")

        return data

    
class TeamInvitationSerializer(serializers.ModelSerializer):
    team = serializers.IntegerField(write_only=True)
    invitee = serializers.CharField(write_only=True)

    class Meta:
        model = TeamInvitation
        fields = ['id', 'team', 'invitee', 'inviter', 'status']
        read_only_fields = ['id', 'status']

    def validate(self, data):
        # Get team instance
        try:
            data['team'] = Team.objects.get(id=data.pop('team'))
        except Team.DoesNotExist:
            raise serializers.ValidationError("Team does not exist")

        # Get invitee instance
        try:
            data['invitee'] = User.objects.get(username=data.pop('invitee'))
        except User.DoesNotExist:
            raise serializers.ValidationError("Invitee user does not exist")

        # Prevent self-invitation
        if data['invitee'] == self.context['request'].user:
            raise serializers.ValidationError("You cannot invite yourself")
        
        if TeamInvitation.objects.filter(team=data['team'], invitee=data['invitee'], status='pending').exists():
            raise serializers.ValidationError("A pending invitation already exists for this user")

        return data

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'team': instance.team.name,
            'inviter': instance.inviter.username,
            'invitee': instance.invitee.username,
            'status': instance.status,
        }