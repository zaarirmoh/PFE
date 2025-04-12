from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Team, TeamMembership, TeamSettings

class TeamMembershipInline(TabularInline):
    """
    Inline view of team memberships - completely read-only
    """
    model = TeamMembership
    extra = 0  # No extra empty forms
    readonly_fields = ('user', 'team', 'role', 'joined_at')
    can_delete = False
    tab = True
    
    def has_add_permission(self, request, obj=None):
        """Prevent adding team members via admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent changing team members via admin"""
        return False

class TeamAdmin(ModelAdmin):
    """
    Admin configuration for Team model.
    - Only is_verified field can be changed
    - Team creation through admin is disabled
    - Team deletion through admin is disabled
    - Team members displayed as read-only inline items
    """
    # Fields to display in the list view
    list_display = ('name', 'academic_year', 'current_member_count', 'maximum_members', 'is_verified')
    
    # Fields to filter by in the sidebar
    list_filter = ('is_verified', 'academic_year')
    
    # Fields to search by
    search_fields = ('name', 'description')
    
    # Default ordering
    ordering = ('academic_year', 'name', '-created_at')
    
    # Only is_verified can be edited
    readonly_fields = ('name', 'description', 'academic_year', 
                      'maximum_members', 'created_at', 
                      'updated_at', 'created_by', 'updated_by')
    
    # Display team memberships inline
    inlines = [TeamMembershipInline]
    
    fieldsets = (
        ('Team info', {
            'fields': ('name', 'description')
        }),
        ('Academic info', {
            'fields': ('academic_year', 'maximum_members'),
            'classes': ('collapse',)
        }),
        ('Verification Status', {
            'fields': ('is_verified',),
            'description': 'Administrators can verify teams to indicate official recognition.'
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable the ability to add new teams through admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion of teams through admin"""
        return False
    
    def current_member_count(self, obj):
        """Display the current number of members"""
        return obj.current_member_count
    current_member_count.short_description = 'Member Count'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related to reduce queries"""
        return super().get_queryset(request).prefetch_related('members', 'teammembership_set')
    
    def save_model(self, request, obj, form, change):
        """Set updated_by when saving"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class TeamSettingsAdmin(ModelAdmin):
    """
    Admin for team settings per academic year
    """
    list_display = ('academic_year', 'maximum_members')
    list_filter = ('academic_year',)
    search_fields = ('academic_year',)
    ordering = ('academic_year',)
    
    fieldsets = (
        ('Settings', {
            'fields': ('academic_year', 'maximum_members'),
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by when saving"""
        if not obj.pk:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Team, TeamAdmin)
admin.site.register(TeamSettings, TeamSettingsAdmin)
# admin.site.register(TeamMembership)