from rest_framework import serializers
from teams.models import Team


from rest_framework import serializers
from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer for Team model with enhanced validation and representation
    """
    owner = serializers.SerializerMethodField(read_only=True)
    member_count = serializers.SerializerMethodField(read_only=True)
    has_capacity = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'created_at', 'updated_at',
            'academic_year', 'academic_program', 'maximum_members',
            'owner', 'member_count', 'has_capacity', 'is_verified',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 
            'academic_year', 'academic_program', 'maximum_members',
            'is_verified',
        ]
        
    def get_owner(self, obj):
        """Get the owner's username"""
        owner = obj.owner
        if owner:
            return {
                'id': owner.id,
                'username': owner.username,
            }
        return None
    
    def get_member_count(self, obj):
        """Get the number of team members"""
        return obj.members.count()
    
    def get_has_capacity(self, obj):
        """Check if the team has capacity for more members"""
        return obj.has_capacity
        
    def validate_name(self, value):
        """Ensure team name is unique (case-insensitive)"""
        # When updating, exclude current instance
        queryset = Team.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise serializers.ValidationError("A team with this name already exists.")
        return value