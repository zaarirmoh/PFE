from rest_framework import serializers
from django.contrib.auth import get_user_model
from teams.models import Team, TeamJoinRequest, TeamMembership
from users.models import Student

User = get_user_model()

class TeamJoinRequestSerializer(serializers.ModelSerializer):
    """Serializer for TeamJoinRequest model"""
    
    team_id = serializers.IntegerField(write_only=True, source='team')
    message = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = TeamJoinRequest
        fields = ['id', 'team_id', 'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate request creation"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
            
        # Set requester to current user
        data['requester'] = request.user
            
        # Get team instance
        try:
            team_id = data.get('team')
            team = Team.objects.get(id=team_id)
            data['team'] = team
        except Team.DoesNotExist:
            raise serializers.ValidationError({"team_id": "Team does not exist"})
        
        # Check if user is already a member
        if TeamMembership.objects.filter(team=team, user=request.user).exists():
            raise serializers.ValidationError("You are already a member of this team")
            
        # Check for existing pending request
        if TeamJoinRequest.objects.filter(
            team=team, 
            requester=request.user, 
            status=TeamJoinRequest.STATUS_PENDING
        ).exists():
            raise serializers.ValidationError("You already have a pending join request for this team")
        
        # Check if team is already at capacity
        if not team.has_capacity:
            raise serializers.ValidationError(
                f"Team '{team.name}' has reached its maximum capacity of {team.maximum_members} members."
            )
        
        # Verify requester is a student
        try:
            student = request.user.student
        except Student.DoesNotExist:
            raise serializers.ValidationError("Only students can request to join teams.")
        
        # Check student's academic status
        if student.academic_status != 'active':
            raise serializers.ValidationError(
                "Only students with active status can request to join teams."
            )
        
        # Check academic year and program match
        if student.current_year != team.academic_year:
            raise serializers.ValidationError(
                f"Only students in academic year {team.academic_year} can join this team."
            )
        
        if student.academic_program != team.academic_program:
            raise serializers.ValidationError(
                f"Only students in the {team.academic_program} program can join this team."
            )

        return data
    

    def to_representation(self, instance):
        """Custom representation for join request"""
        return {
            'id': instance.id,
            'team': {
                'id': instance.team.id,
                'name': instance.team.name
            },
            'requester': {
                'username': instance.requester.username
            },
            'message': instance.message,
            'status': instance.status,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at
        }


class JoinRequestResponseSerializer(serializers.Serializer):
    """Serializer for responding to a join request"""
    
    action = serializers.ChoiceField(choices=['accept', 'decline'])