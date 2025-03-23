from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import action
from .models import Timeline
from teams.services import AutoTeamAssignmentService
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# Register your models here.
class TimelineAdmin(ModelAdmin):
    list_display = (
        'timeline_type', 'academic_program', 
        'academic_year','is_current', 'status'
    )
    list_filter = ('is_active', 'timeline_type')
    search_fields = ('name', 'description')
    readonly_fields = ('slug','timeline_type',)
    actions = ['trigger_auto_team_assignment']
    
    fieldsets = (
        (None, {
            'fields': ('slug', 'name', 'description')
        }),
        ('Timeline Type', {
            'fields': ('timeline_type', 'academic_program', 'academic_year'),
            'description': 'Set the type of timeline and which academic program and year it applies to.'
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date', 'is_active'),
            'description': 'Set the time period for this timeline. Leave end date blank for open-ended timelines.'
        }),
    )
    
    def trigger_auto_team_assignment(self, request, queryset):
        """Admin action to trigger auto team assignment for selected timelines."""
        success_count = 0
        for timeline in queryset:
            result = AutoTeamAssignmentService.assign_students_after_timeline(timeline.slug)
            
            if 'error' in result:
                messages.error(request, f"Failed for {timeline.name}: {result['error']}")
            else:
                success_count += 1
                messages.success(
                    request, 
                    f"Assigned {result['total_assigned']} students for {timeline.name} timeline. "
                    f"{result['total_unassigned']} students remain unassigned."
                )
        
        if success_count:
            if success_count == 1:
                self.message_user(request, "Auto team assignment completed for 1 timeline.", messages.SUCCESS)
            else:
                self.message_user(request, f"Auto team assignment completed for {success_count} timelines.", messages.SUCCESS)
    
    trigger_auto_team_assignment.short_description = "Run auto team assignment for selected timelines"
    
    
    def has_add_permission(self, request):
        """Prevent adding new timelines through admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting timelines through admin."""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Make slug field read-only and prevent changing timeline type."""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('slug',)
        return self.readonly_fields
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """Restrict changing the timeline type in the admin."""
        if db_field.name == 'slug':
            kwargs['disabled'] = True  # Disable the choice field
        return super().formfield_for_choice_field(db_field, request, **kwargs)
    
    @action(description=_("action"), icon="hub")
    def changelist_action1(self, request):
        messages.success(
            request, _("Changelist action has been successfully executed.")
        )
        return redirect(reverse_lazy("admin:timelines_timeline_changelist"))
    
    
admin.site.register(Timeline, TimelineAdmin)