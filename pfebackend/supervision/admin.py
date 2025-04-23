# meetings/admin.py
from django.contrib import admin
from .models import Meeting
from unfold.admin import ModelAdmin, TabularInline



# class MeetingAttendanceInline(TabularInline):
#     """Inline admin for meeting attendances"""
#     model = MeetingAttendance
#     extra = 0
#     readonly_fields = ['response_timestamp']


@admin.register(Meeting)
class MeetingAdmin(ModelAdmin):
    """Admin configuration for the Meeting model"""
    list_display = ['title', 'team', 'scheduled_by', 'scheduled_at', 'status']
    list_filter = ['status', 'location_type', 'scheduled_at']
    search_fields = ['title', 'description', 'team__name', 'scheduled_by__username']
    date_hierarchy = 'scheduled_at'
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    # inlines = [MeetingAttendanceInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'team', 'scheduled_by')
        }),
        ('Schedule', {
            'fields': ('scheduled_at', 'duration_minutes', 'status')
        }),
        ('Location', {
            'fields': ('location_type', 'location_details', 'meeting_link')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


# @admin.register(MeetingAttendance)
# class MeetingAttendanceAdmin(ModelAdmin):
#     """Admin configuration for the MeetingAttendance model"""
#     list_display = ['meeting', 'attendee', 'status', 'response_timestamp']
#     list_filter = ['status', 'response_timestamp']
#     search_fields = ['meeting__title', 'attendee__username', 'response_notes']
#     readonly_fields = ['response_timestamp']