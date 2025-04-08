from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import Document

@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = ('title', 'document_type', 'file_preview', 'created_at', 'updated_at')
    list_filter = ('document_type',)
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at', 'file_preview')

    fieldsets = (
        (None, {
            'fields': ('title', 'file', 'document_type', 'file_preview')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Automatically managed timestamps',
        }),
    )

    def file_preview(self, obj):
        """Show a preview of the document if it's an image, otherwise provide a download link."""
        if obj.file:
            if obj.file.name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return format_html(f'<img src="{obj.file.url}" width="100px" style="border-radius: 5px;" />')
            return format_html(f'<a href="{obj.file.url}" target="_blank">Download File</a>')
        return "-"
    
    file_preview.short_description = "Preview"

    def has_add_permission(self, request):
        """Allow adding new documents"""
        return True

    def has_delete_permission(self, request, obj=None):
        """Allow deleting documents"""
        return True

