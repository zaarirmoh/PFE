from rest_framework import serializers
from .models import Timeline

class TimelineSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)
    academic_year_display = serializers.CharField(source='get_academic_year_display', read_only=True)
    timeline_type_display = serializers.CharField(source='get_timeline_type_display', read_only=True)
    
    class Meta:
        model = Timeline
        fields = [
            'id', 'slug', 'name', 'description', 
            'start_date', 'end_date', 'is_active', 
            'status', 'is_current', 'timeline_type',
            'timeline_type_display', 'academic_year',
            'academic_year_display'
        ]