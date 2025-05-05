# meetings/serializers.py
from rest_framework import serializers
from .models import Meeting
from teams.serializers import TeamSerializer
from users.serializers import TeacherSerializer
from teams.serializers import TeamSerializer
from teams.models import TeamMembership
from teams.serializers import TeamMembershipSerializer
from themes.serializers import ThemeOutputSerializer as ThemeSerializer
from users.serializers import CustomUserSerializer as UserSerializer
from themes.models import ThemeAssignment
from .models import Defense, JuryMember
from teams.serializers import TeamSerializer
from themes.serializers import ThemeOutputSerializer
from .models import Upload, ResourceComment
from users.serializers import CustomUserSerializer

class MeetingListSerializer(serializers.ModelSerializer):
    """Serializer for listing meetings"""
    scheduled_by = TeacherSerializer(read_only=True)
    team_name = serializers.StringRelatedField(source='team.name')
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'team', 'team_name', 'scheduled_by', 
            'scheduled_at', 'duration_minutes', 'location_type', 
            'status'
        ]


class MeetingDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed meeting information"""
    scheduled_by = TeacherSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    # attendances = MeetingAttendanceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description', 'team', 'scheduled_by',
            'scheduled_at', 'duration_minutes', 'location_type',
            'location_details', 'meeting_link', 'status',
            'created_at', 'updated_at'
        ]


class MeetingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating meetings"""
    class Meta:
        model = Meeting
        fields = [
            'title', 'description', 'team', 'scheduled_at',
            'duration_minutes', 'location_type', 'location_details',
            'meeting_link'
        ]
        
    def validate(self, attrs):
        """Validate the meeting data"""
        location_type = attrs.get('location_type')
        meeting_link = attrs.get('meeting_link')
        location_details = attrs.get('location_details')
        
        # Validate location information
        if location_type == Meeting.LOCATION_TYPE_ONLINE and not meeting_link:
            raise serializers.ValidationError(
                {"meeting_link": "Meeting link is required for online meetings."}
            )
        
        if location_type == Meeting.LOCATION_TYPE_PHYSICAL and not location_details:
            raise serializers.ValidationError(
                {"location_details": "Location details are required for physical meetings."}
            )
            
        # Scheduled time validation is handled by the model's clean method
        
        return attrs


class MeetingStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating meeting status"""
    class Meta:
        model = Meeting
        fields = ['status']
        
    def validate_status(self, value):
        """Validate the status transition"""
        instance = self.instance
        
        if instance.status == Meeting.STATUS_CANCELLED and value != Meeting.STATUS_CANCELLED:
            raise serializers.ValidationError("Cannot change status of a cancelled meeting.")
            
        if instance.status == Meeting.STATUS_COMPLETED and value != Meeting.STATUS_COMPLETED:
            raise serializers.ValidationError("Cannot change status of a completed meeting.")
            
        return value
    


class ResourceCommentSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = ResourceComment
        fields = ['id', 'content', 'author', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']


class UploadSerializer(serializers.ModelSerializer):
    """
    Serializer for file uploads.
    Includes commenting functionality and filtering options.
    """
    uploaded_by = CustomUserSerializer(read_only=True)
    comments = ResourceCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Upload
        fields = ['id', 'team', 'title', 'url', 'uploaded_by', 'created_at', 'comments']
        read_only_fields = ['uploaded_by', 'created_at']
        swagger_schema_fields = {
            "title": "Upload",
            "description": "A file upload with associated comments",
            "properties": {
                "team": {
                    "type": "integer",
                    "description": "ID of the team this upload belongs to"
                },
                "title": {
                    "type": "string", 
                    "description": "Title of the uploaded file"
                },
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL where the file can be accessed"
                },
                "comments": {
                    "type": "array",
                    "description": "List of comments on this upload",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "content": {"type": "string"},
                            "author": {"type": "object"},
                            "created_at": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            }
        }


class JuryMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = JuryMember
        fields = ['id', 'user', 'user_name', 'role', 'role_name', 'is_president', 'notes']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
        
    def get_role_name(self, obj):
        return obj.role.name if obj.role else None
        
class DefenseSerializer(serializers.ModelSerializer):
    jury_members = JuryMemberSerializer(many=True, read_only=True)
    team = TeamSerializer
    class Meta:
        model = Defense
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        
class DefenseDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed defense information"""
    team = TeamSerializer(read_only=True)
    theme = ThemeOutputSerializer(read_only=True)
    jury_members = JuryMemberSerializer(many=True, read_only=True)
    
    class Meta:
        model = Defense
        fields = [
            'id', 'title', 'theme_assignment', 'team', 'theme',
            'jury_members', 'date', 'start_time', 'end_time',
            'location', 'room', 'defense_uri', 'report_uri',
            'specifications_document_uri', 'description',
            'status', 'result', 'grade', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
        
class ProjectListSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for projects (theme assignments) that combines
    all related information using existing serializers.
    """
    theme = ThemeSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    assigned_by = UserSerializer(read_only=True)
    
    # Add computed fields for quick access to important information
    theme_title = serializers.CharField(source='theme.title', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    academic_year = serializers.CharField(source='team.academic_year', read_only=True)
    
    # Get team owner for quick access
    team_owner = serializers.SerializerMethodField()
    
    # Get team members with roles
    team_members = serializers.SerializerMethodField()
    
    # Get theme supervisors
    supervisors = serializers.SerializerMethodField()
    
    # Get project artifacts
    uploads = serializers.SerializerMethodField()
    meetings = serializers.SerializerMethodField()
    
    class Meta:
        model = ThemeAssignment
        fields = [
            'id', 'theme', 'team', 'assigned_by',
            'theme_title', 'team_name', 'academic_year',
            'team_owner', 'team_members', 'supervisors',
            'uploads', 'meetings',
            'created_at', 'updated_at'
        ]
    
    def get_team_owner(self, obj):
        """Get the team owner"""
        owner_membership = TeamMembership.objects.filter(
            team=obj.team, 
            role=TeamMembership.ROLE_OWNER
        ).select_related('user').first()
        
        if owner_membership:
            # Use your existing UserSerializer
            return UserSerializer(owner_membership.user).data
        return None
    
    def get_team_members(self, obj):
        """Get all team members with roles"""
        memberships = TeamMembership.objects.filter(
            team=obj.team
        ).select_related('user')
        
        # Use your existing TeamMembershipSerializer
        return TeamMembershipSerializer(memberships, many=True).data
    
    def get_supervisors(self, obj):
        """Get theme proposer and co-supervisors"""
        supervisors = {
            'proposer': UserSerializer(obj.theme.proposed_by).data,
            'co_supervisors': UserSerializer(obj.theme.co_supervisors.all(), many=True).data
        }
        return supervisors
    
    def get_uploads(self, obj):
        """Get team uploads"""
        # Use your existing UploadSerializer
        return UploadSerializer(obj.team.uploads.all(), many=True).data
    
    def get_meetings(self, obj):
        """Get team meetings"""
        # Use your existing MeetingSerializer
        return MeetingDetailSerializer(obj.team.meetings.all(), many=True).data

