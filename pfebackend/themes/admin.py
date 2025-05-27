from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models.theme_models import Theme
from notifications.services import NotificationService
from django.utils.html import format_html, format_html_join


class ThemeAdmin(ModelAdmin):
    list_display = ('title', 'proposed_by', 'academic_year')
    list_filter = ('academic_year',)
    search_fields = ('title', 'proposed_by__email')
    
    readonly_fields = ('documents_preview',)
    
    def documents_preview(self, obj):
        """Show document previews with download links similar to DocumentAdmin"""
        documents = obj.documents.all()
        if not documents:
            return "No documents attached"
        previews = []
        for doc in documents:
            preview = format_html(f'<a href="{doc.file.url}" target="_blank">Download File</a>')
            return preview
            previews.append(preview)
        return previews
    
    documents_preview.short_description = 'Attached Documents'
    
    fieldsets = (
        ('Theme info', {
            'fields': ('title', 'academic_year', 'proposed_by', 'co_supervisors', 'description', 'tools', 'documents', 'documents_preview', 'is_verified', ),
            'description': 'Set the time period for this timeline. Leave end date blank for open-ended timelines.'
        }),
    )
    
    
    
    def save_model(self, request, obj, form, change):
        if change:  # Only if editing an existing object
            old_obj = Theme.objects.get(pk=obj.pk)
            if old_obj.is_verified != obj.is_verified:
                # is_verified has changed!
                self.handle_verification_change(request, old_obj, obj)

        super().save_model(request, obj, form, change)

    def handle_verification_change(self, request, old_obj, new_obj):
        # Put your custom logic here
        if new_obj.is_verified:
            print(f"Theme '{new_obj.title}' has been verified!")
            
            # Notify the theme proposer
            NotificationService.create_and_send(
                recipient=new_obj.proposed_by,
                title="Theme Verified",
                content=f"Your theme '{new_obj.title}' has been verified.",
                notification_type="theme_verification",
                related_object=new_obj,
                priority="medium",
                action_url=f"/themes/{new_obj.id}/",
                metadata={
                    "theme_id": new_obj.id,
                    "academic_year": new_obj.academic_year
                }
            )
            
            # Notify all co-supervisors
            for supervisor in new_obj.co_supervisors.all():
                NotificationService.create_and_send(
                    recipient=supervisor,
                    title="Theme Verified",
                    content=f"A theme you are co-supervising '{new_obj.title}' has been verified.",
                    notification_type="theme_verification",
                    related_object=new_obj,
                    priority="medium",
                    action_url=f"/themes/{new_obj.id}/",
                    metadata={
                        "theme_id": new_obj.id,
                        "academic_year": new_obj.academic_year,
                        "proposed_by": new_obj.proposed_by.id
                    }
                )
            
        else:
            print(f"Theme '{new_obj.title}' has been unverified.")
            
            # Notify the theme proposer about unverification
            NotificationService.create_and_send(
                recipient=new_obj.proposed_by,
                title="Theme Unverified",
                content=f"Your theme '{new_obj.title}' has been unverified.",
                notification_type="theme_unverification",
                related_object=new_obj,
                priority="medium",
                action_url=f"/themes/{new_obj.id}/",
                metadata={
                    "theme_id": new_obj.id,
                    "academic_year": new_obj.academic_year
                }
            )
            
            # Notify all co-supervisors about unverification
            for supervisor in new_obj.co_supervisors.all():
                NotificationService.create_and_send(
                    recipient=supervisor,
                    title="Theme Unverified",
                    content=f"A theme you are co-supervising '{new_obj.title}' has been unverified.",
                    notification_type="theme_unverification",
                    related_object=new_obj,
                    priority="medium",
                    action_url=f"/themes/{new_obj.id}/",
                    metadata={
                        "theme_id": new_obj.id,
                        "academic_year": new_obj.academic_year,
                        "proposed_by": new_obj.proposed_by.id
                    }
                )

admin.site.register(Theme, ThemeAdmin)