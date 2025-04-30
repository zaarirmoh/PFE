from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models.theme_models import Theme
from .models.project_models import ThemeAssignment
from notifications.services import NotificationService


class ThemeAdmin(ModelAdmin):
    list_display = ('title', 'proposed_by', 'academic_year')
    list_filter = ('academic_year',)
    search_fields = ('title', 'proposed_by__email')
    
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
admin.site.register(ThemeAssignment)

# class ThemeAssignmentInline(admin.TabularInline):
#     model = ThemeAssignment
#     extra = 1
#     autocomplete_fields = ['team']  # helps if you have many teams


# @admin.register(Theme)
# class ThemeAdmin(ModelAdmin):
#     list_display = ('title', 'proposed_by', 'academic_year', 'document_preview', 'created_at')
#     list_filter = ('academic_year', 'created_at')
#     search_fields = ('title', 'proposed_by__email')
#     readonly_fields = ('created_at', 'updated_at', 'document_preview')
#     inlines = [ThemeAssignmentInline]  # 👈 This allows assignment of teams to the theme

#     fieldsets = (
#         ('Theme Details', {
#             'fields': ('title', 'proposed_by', 'co_supervisors', 'description', 'tools')
#         }),
#         ('Academic Information', {
#             'fields': ['academic_year']
#         }),
#         ('Documents', {
#             'fields': ('documents', 'document_preview'),
#             'description': 'Uploaded documents related to this theme.'
#         }),
#         ('Metadata', {
#             'fields': ('created_at', 'updated_at'),
#             'description': 'Automatically managed timestamps',
#         }),
#     )

#     def document_preview(self, obj):
#         if obj.documents.exists():
#             previews = []
#             for doc in obj.documents.all():
#                 if doc.file and doc.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
#                     previews.append(f'<img src="{doc.file.url}" width="80px" style="margin:2px;border-radius:5px;" />')
#                 else:
#                     previews.append(f'<a href="{doc.file.url}" target="_blank">{doc.title} (Download)</a>')
#             return format_html(" ".join(previews))
#         return "-"

#     document_preview.short_description = "Document Previews"

#     def has_add_permission(self, request):
#         return True

#     def has_delete_permission(self, request, obj=None):
#         return True

