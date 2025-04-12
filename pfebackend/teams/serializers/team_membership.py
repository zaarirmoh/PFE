from rest_framework import serializers
from django.contrib.auth import get_user_model
from teams.models import TeamMembership, Team
from users.models import Student

User = get_user_model()


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Serializer for TeamMembership model"""
    
    username = serializers.CharField(write_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    academic_year = serializers.CharField(source='team.academic_year', read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = ['id', 'team', 'username', 'user', 'team_name', 'academic_year', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'user', 'team_name', 'academic_year']
        
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

        # Get team instance
        team = data.get('team')
        
        # If this is a create operation, perform additional validations
        if not self.instance:
            # Check if user is already a member
            if TeamMembership.objects.filter(team=team, user=user).exists():
                raise serializers.ValidationError("User is already a member of this team")
            
            # Check if team is at capacity (skip for owners which is needed for team creation)
            if data.get('role') != TeamMembership.ROLE_OWNER and not team.has_capacity:
                raise serializers.ValidationError(
                    f"Team '{team.name}' has reached its maximum capacity of {team.maximum_members} members."
                )
            
            # Verify user is a student
            try:
                student = user.student
            except Student.DoesNotExist:
                raise serializers.ValidationError("Only students can be team members.")
            
            # Check student's academic status
            if student.academic_status != 'active':
                raise serializers.ValidationError("Only students with active status can join teams.")
            
            # Check academic year match
            if student.current_year != team.academic_year:
                raise serializers.ValidationError(
                    f"Only students in academic year {team.academic_year} can join this team."
                )
                
        return data