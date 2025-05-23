# meetings/admin.py
from django.contrib import admin
from .models import Meeting, Defense
from unfold.admin import ModelAdmin, TabularInline
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from notifications.services import NotificationService
from .models import Defense, JuryMember

class JuryRoleAdmin(ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']

class JuryMemberInline(TabularInline):
    model = JuryMember
    extra = 1
    autocomplete_fields = ['user']


class DefenseAdmin(ModelAdmin):
    list_display = ['title', 'theme_display', 'team_display', 'date', 'start_time', 'end_time', 'status']
    list_filter = ['date', 'status', 'theme_assignment__theme__academic_year']
    search_fields = ['title', 'theme_assignment__team__name', 'theme_assignment__theme__title']
    date_hierarchy = 'date'
    inlines = [JuryMemberInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'theme_assignment', 'description')
        }),
        (_('Schedule'), {
            'fields': ('date', 'start_time', 'end_time', 'location', 'room')
        }),
        (_('Status and Result'), {
            'fields': ('status', 'result', 'grade')
        }),
        (_('Audit Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'theme_assignment', 
            'theme_assignment__team', 
            'theme_assignment__theme'
        )
    
    def team_display(self, obj):
        url = reverse('admin:teams_team_change', args=[obj.team.id])
        return format_html('<a href="{}">{}</a>', url, obj.team.name)
    team_display.short_description = _('Team')
    team_display.admin_order_field = 'theme_assignment__team__name'
    
    def theme_display(self, obj):
        url = reverse('admin:themes_theme_change', args=[obj.theme.id])
        return format_html('<a href="{}">{}</a>', url, obj.theme.title)
    theme_display.short_description = _('Theme')
    theme_display.admin_order_field = 'theme_assignment__theme__title'
    
    def save_model(self, request, obj, form, change):
        obj._is_new = not obj.pk
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        defense = form.instance
        is_new = getattr(defense, '_is_new', False)
        if is_new:
            # Send notifications for new defense
            self._send_defense_created_notifications(defense, request.user)
        else:
            # Send notifications for updated defense
            changed_fields = form.changed_data
            self._send_defense_updated_notifications(defense, request.user, changed_fields)
    
    def _send_defense_created_notifications(self, defense, admin_user):
        """
        Send notifications to all relevant users when a new defense is created
        """
        # Get team members
        team = defense.team
        team_members = team.members.all()
        
        # Get theme supervisor and co-supervisors
        theme = defense.theme
        supervisor = theme.proposed_by
        co_supervisors = theme.co_supervisors.all()
        
        # Get jury members
        # jury_members = [jm.user for jm in defense.jury_members.all()]
        jury_members = [jm for jm in defense.jury_members.all()]
        
        # 1. Notify team members
        defense_url = f"/defenses/{defense.id}/"  # Adjust based on your URL structure
        for member in team_members:
            NotificationService.create_and_send(
                recipient=member,
                title=_("Defense Scheduled"),
                content=_(f"Your team's defense for '{theme.title}' has been scheduled for {defense.date} at {defense.start_time}."),
                notification_type="defense_scheduled",
                related_object=defense,
                priority="high",
                action_url=defense_url,
                metadata={
                    "defense_id": defense.id,
                    "defense_date": defense.date.isoformat(),
                    "defense_time": defense.start_time.isoformat(),
                    "location": defense.location,
                    "room": defense.room,
                }
            )
        
        # 2. Notify theme supervisor and co-supervisors
        for teacher in [supervisor] + list(co_supervisors):
            NotificationService.create_and_send(
                recipient=teacher,
                title=_("Defense Supervision"),
                content=_(f"You are supervising a defense for team '{team.name}' on {defense.date} at {defense.start_time}."),
                notification_type="defense_supervision",
                related_object=defense,
                priority="medium",
                action_url=defense_url,
                metadata={
                    "defense_id": defense.id,
                    "defense_date": defense.date.isoformat(),
                    "defense_time": defense.start_time.isoformat(),
                    "team_name": team.name,
                    "location": defense.location,
                    "room": defense.room,
                }
            )
        for jury_member in jury_members:
            jury_user = jury_member.user
            if jury_user not in ([supervisor] + list(co_supervisors)):  # Avoid duplicate notifications
                NotificationService.create_and_send(
                    recipient=jury_user,
                    title=_("Jury Participation"),
                    content=_(f"You are assigned as a jury member for team '{team.name}' defense on {defense.date} at {defense.start_time}."),
                    notification_type="jury_assignment",
                    related_object=defense,
                    priority="medium",
                    action_url=defense_url,
                    metadata={
                        "jury_role": jury_member.role.name,
                        "is_president": jury_member.is_president,
                        "defense_id": defense.id,
                        "defense_date": defense.date.isoformat(),
                        "defense_time": defense.start_time.isoformat(),
                        "team_name": team.name,
                        "location": defense.location,
                        "room": defense.room,
                    }
                )
    
    def _send_defense_updated_notifications(self, defense, admin_user, changed_fields):
        """
        Send notifications when defense details are updated
        """
        # Only send notifications for relevant changes
        important_changes = set(changed_fields) & {'date', 'start_time', 'end_time', 'location', 'room', 'status'}
        
        if not important_changes:
            return
        
        # Get all relevant people
        team = defense.team
        team_members = team.members.all()
        
        theme = defense.theme
        supervisor = theme.proposed_by
        co_supervisors = theme.co_supervisors.all()
        
        jury_members = [jm.user for jm in defense.jury_members.all()]
        
        # Create change message
        change_message = _("Defense details have been updated")
        if 'status' in changed_fields and defense.status == 'cancelled':
            change_message = _("Defense has been cancelled")
        elif 'status' in changed_fields and defense.status == 'postponed':
            change_message = _("Defense has been postponed")
        elif 'date' in changed_fields or 'start_time' in changed_fields:
            change_message = _("Defense date or time has been changed")
        elif 'location' in changed_fields or 'room' in changed_fields:
            change_message = _("Defense location has been changed")
        
        # All recipients (deduplicated)
        all_recipients = set(team_members) | {supervisor} | set(co_supervisors) | set(jury_members)
        
        # Notify all recipients
        defense_url = f"/defenses/{defense.id}/"  # Adjust based on your URL structure
        for recipient in all_recipients:
            NotificationService.create_and_send(
                recipient=recipient,
                title=_("Defense Update"),
                content=f"{change_message} - {team.name}, {defense.date} at {defense.start_time}.",
                notification_type="defense_updated",
                related_object=defense,
                priority="high",
                action_url=defense_url,
                metadata={
                    "defense_id": defense.id,
                    "defense_date": defense.date.isoformat(),
                    "defense_time": defense.start_time.isoformat(),
                    "location": defense.location,
                    "room": defense.room,
                    "status": defense.status,
                    "changes": list(important_changes)
                }
            )


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
    
# admin.site.register(JuryRole, JuryRoleAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Defense, DefenseAdmin)