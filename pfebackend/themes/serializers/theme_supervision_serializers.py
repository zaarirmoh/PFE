from rest_framework import serializers
from teams.models import Team
from users.serializers import StudentSerializer, TeacherSerializer
from teams.serializers import TeamSerializer
from themes.serializers import ThemeOutputSerializer
from themes.models import Theme, ThemeSupervisionRequest




# class ThemeSupervisionRequestSerializer(serializers.ModelSerializer):
#     theme = ThemeOutputSerializer(read_only=True)
#     team = TeamSerializer(read_only=True)
#     requester = StudentSerializer(read_only=True)
#     invitee = TeacherSerializer(read_only=True)
#     supervisor = serializers.SerializerMethodField()
    
#     class Meta:
#         model = ThemeSupervisionRequest
#         fields = [
#             'id', 'theme', 'team', 'requester', 'invitee', 'supervisor',
#             'status', 'message', 'response_message', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['status', 'response_message', 'created_at', 'updated_at']
    
#     def get_supervisor(self, obj):
#         return TeacherSerializer(obj.theme.proposed_by).data
class ThemeSupervisionRequestSerializer(serializers.ModelSerializer):
    theme = ThemeOutputSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    # requester = StudentSerializer(read_only=True)
    requester = serializers.SerializerMethodField()
    invitee = serializers.SerializerMethodField()  # Changed to method field to handle multiple user types
    supervisor = serializers.SerializerMethodField()
    
    class Meta:
        model = ThemeSupervisionRequest
        fields = [
            'id', 'theme', 'team', 'requester', 'invitee', 'supervisor',
            'status', 'message', 'response_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'response_message', 'created_at', 'updated_at']
    
    def get_supervisor(self, obj):
        return TeacherSerializer(obj.theme.proposed_by).data
    
    def get_invitee(self, obj):
        # Handle different user types
        user = obj.invitee
        if hasattr(user, 'teacher'):
            return TeacherSerializer(user.teacher).data
        else:
            # If no teacher profile, return basic user info
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'user_type': user.user_type
            }
    def get_requester(self, obj):
        # Handle User object directly
        user = obj.requester
        if hasattr(user, 'student'):
            return StudentSerializer(user.student).data
        else:
            # If no student profile, return basic user info
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'user_type': user.user_type
            }

class CreateThemeSupervisionRequestSerializer(serializers.Serializer):
    theme_id = serializers.IntegerField()
    team_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        # Get theme and team
        try:
            theme = Theme.objects.get(id=data['theme_id'])
            team = Team.objects.get(id=data['team_id'])
        except Theme.DoesNotExist:
            raise serializers.ValidationError("Theme not found")
        except Team.DoesNotExist:
            raise serializers.ValidationError("Team not found")
        
        # Add theme and team objects to validated data
        data['theme'] = theme
        data['team'] = team
        data['invitee'] = theme.proposed_by  # Default invitee is the theme proposer
        
        return data


class ProcessSupervisionRequestSerializer(serializers.Serializer):
    response = serializers.ChoiceField(choices=['accept', 'decline'])
    message = serializers.CharField(required=False, allow_blank=True)