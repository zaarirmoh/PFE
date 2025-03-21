from rest_framework import serializers
from .models import Timeline

class TimelineSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Timeline
        fields = ['id', 'slug', 'name', 'description', 'start_date', 
                 'end_date', 'is_active', 'status', 'is_current','academic_year','academic_program']
