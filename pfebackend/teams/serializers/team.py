from rest_framework import serializers
from teams.models import Team


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
