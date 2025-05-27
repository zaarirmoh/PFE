from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
import unfold.admin
from unfold.decorators import action
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from .admin_filters import AcademicYearFilter
from django.urls import reverse_lazy, path, reverse
from django.utils.translation import gettext_lazy as _
from .admin_forms import CustomUserChangeForm, CustomUserCreationForm
from .admin_inlines import (
    StudentProfileInline,
    TeacherProfileInline,
    AdministratorProfileInline,
    ExternalUserProfileInline,
)
from django.http import HttpResponseRedirect
from users.models import User, Student, StudentSkill, ExcelUpload
from users.serializers.base import BaseProfileSerializer
from django.template.response import TemplateResponse
from ..student_importer_test_servic import import_students_from_excel
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

# Dictionary mapping user types to their corresponding inline classes
USER_TYPE_INLINES = {
    'student': StudentProfileInline,
    'teacher': TeacherProfileInline,
    'administrator': AdministratorProfileInline,
    'external_user': ExternalUserProfileInline,
}

class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'username')
    exclude = ('password',)
    list_filter =  (AcademicYearFilter,)
    
    # Set filter_horizontal to an empty tuple since we don't have groups or user_permissions
    filter_horizontal = ()
    
    fieldsets = (
        (None, {'fields': ('email', 'username')}),
        (
            'Personal info',
            {
                'fields': ('first_name', 'last_name'),
                'classes': ['callapse'],
            }
        ),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    def get_inlines(self, request, obj=None):
        """Dynamically load the correct profile inline based on user_type."""
        if obj is None:
            return []
            
        inline_class = USER_TYPE_INLINES.get(obj.user_type)
        return [inline_class] if inline_class else []
    
    def response_add(self, request, obj, post_url_continue=None):
        """After adding a new user, redirect to the change page to show profile fields"""
        # Create the appropriate profile
        self._create_profile(obj)
        
        # Show a message to the user
        messages.add_message(
            request, messages.INFO, 
            f'User created successfully. You can now edit the {obj.user_type} profile details.'
        )
        
        # Redirect to the change page
        return redirect(f"../../../users/user/{obj.pk}/change/")
        
    def save_model(self, request, obj, form, change):
        """Save the user and ensure profile exists."""
        with transaction.atomic():
            # Save the user first
            super().save_model(request, obj, form, change)
            
            # If this is an existing user and user_type changed, handle profile switch
            if change and 'user_type' in form.changed_data:
                self._handle_user_type_change(obj)
    
    def _create_profile(self, user):
        """Create the appropriate profile for a user."""
        profile_model = USER_TYPE_INLINES.get(user.user_type)
        if profile_model and profile_model.model:
            # Check if profile already exists
            profile = BaseProfileSerializer.get_profile_instance(user)
            if not profile:
                profile_model.model.objects.create(user=user)
    
    def _handle_user_type_change(self, user):
        """Handle changing a user's type by creating the new profile if needed."""
        # Create new profile for the user's new type
        self._create_profile(user)
        
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-students/',
                self.admin_site.admin_view(self.import_students_view),
                name='users_user_import_students',
            ),
        ]
        return custom_urls + urls

    def import_students_view(self, request):
        if request.method == "POST":
            excel_file = request.FILES.get('excel_file')
            academic_year = request.POST.get('academic_year')
            
            if excel_file and academic_year:
                # Save the file temporarily
                file_path = default_storage.save(f'temp/students_import/{excel_file.name}', ContentFile(excel_file.read()))
                try:
                    # Call the import function
                    import_students_from_excel(default_storage.path(file_path), academic_year)
                    messages.success(request, f"Successfully imported students for academic year {academic_year}")
                except Exception as e:
                    messages.error(request, f"Error importing students: {str(e)}")
                finally:
                    # Clean up the temporary file
                    if default_storage.exists(file_path):
                        default_storage.delete(file_path)
            else:
                messages.error(request, "Please provide both an Excel file and academic year")
            
            return redirect("admin:users_user_changelist")

        # Get available academic years from the ACADEMIC_YEAR_TRANSITIONS
        from ..student_importer_test_servic import ACADEMIC_YEAR_TRANSITIONS
        academic_years = list(ACADEMIC_YEAR_TRANSITIONS.keys())
        
        context = {
            'title': 'Import Students',
            'academic_years': academic_years,
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/users/user/import_students.html", context)

    @action(description=_("Import Students from Excel"), icon="upload")
    def import_students_action(self, request):
        return redirect('admin:users_user_import_students')
    
    def changelist_view(self, request, extra_context=None):
        # Redirect to 2nd year timelines if no filter is applied
        if 'user_type__exact' not in request.GET:
            return HttpResponseRedirect(f"{reverse('admin:users_user_changelist')}?user_type__exact=administrator")
        return super().changelist_view(request, extra_context)
        
    @action(description=_("action"), icon="hub")
    def changelist_action1(self, request):
        messages.success(
            request, _("Changelist action has been successfully executed.")
        )
        return redirect(reverse_lazy("admin:users_user_changelist"))
    
# Register your models here.
admin.site.register(User, CustomUserAdmin)
# admin.site.register(StudentSkill, ModelAdmin)
admin.site.register(ExcelUpload, ModelAdmin)
admin.site.unregister(Group)
