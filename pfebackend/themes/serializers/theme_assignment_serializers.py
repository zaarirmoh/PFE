from rest_framework import serializers
from ..models.project_models import *


class ThemeAssignmentSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    theme_title = serializers.CharField(source='theme.title', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        model = ThemeAssignment
        fields = ('id', 'team', 'team_name', 'theme', 'theme_title', 
                  'assigned_by', 'assigned_by_name')
        read_only_fields = ('assigned_date', 'assigned_by')
        
