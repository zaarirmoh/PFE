from rest_framework import serializers
from django.contrib.auth import get_user_model
from teams.models import TeamMembership

User = get_user_model()



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

