# meetings/serializers.py
from rest_framework import serializers
from .models import Meeting
from teams.serializers import TeamSerializer
from users.serializers import StudentSerializer, TeacherSerializer


# class MeetingAttendanceSerializer(serializers.ModelSerializer):
#     """Serializer for meeting attendance"""
#     attendee = StudentSerializer(read_only=True)
    
#     class Meta:
#         model = MeetingAttendance
#         fields = [
#             'id', 'attendee', 'status', 'response_timestamp', 'response_notes'
#         ]
#         read_only_fields = ['id', 'attendee', 'response_timestamp']


# class MeetingAttendanceUpdateSerializer(serializers.ModelSerializer):
#     """Serializer for updating meeting attendance status"""
#     class Meta:
#         model = MeetingAttendance
#         fields = ['status', 'response_notes']


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
    


from .models import Upload

class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ['id', 'team', 'title', 'url', 'uploaded_by', 'created_at']
        read_only_fields = ['uploaded_by', 'created_at']
