from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Timeline

# Register your models here.
class TimelineAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'start_date', 'end_date', 'is_active', 'is_current')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('slug',)
    
    fieldsets = (
        (None, {
            'fields': ('slug', 'name', 'description')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date', 'is_active'),
            'description': 'Set the time period for this timeline. Leave end date blank for open-ended timelines.'
        }),
    )
    
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

    
    
admin.site.register(Timeline, TimelineAdmin)