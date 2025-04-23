# from django.contrib import admin
# from unfold.admin import ModelAdmin
# from django.utils.html import format_html
# from .models.theme_models import Theme

# @admin.register(Theme)
# class ThemeAdmin(ModelAdmin):
#     list_display = ('title', 'proposed_by', 'academic_year', 'document_preview', 'created_at')
#     list_filter = ('academic_year', 'created_at')
#     search_fields = ('title', 'proposed_by__email')
#     readonly_fields = ('created_at', 'updated_at', 'document_preview')

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
#         """Show previews of related documents if they are images."""
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
#         """Allow adding new themes"""
#         return True

#     def has_delete_permission(self, request, obj=None):
#         """Allow deleting themes"""
#         return True
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models.theme_models import Theme
from .models.project_models import ThemeAssignment  # import your intermediate model
# from .models.team_models import Team  # adjust import if needed
 

admin.site.register(Theme)
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

