from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from .admin_forms import CustomUserChangeForm, CustomUserCreationForm
from .admin_inlines import (
    StudentProfileInline,
    TeacherProfileInline,
    AdministratorProfileInline
)
from users.models import User
from users.serializers.base import BaseProfileSerializer

# admin.site.unregister(User)

# Dictionary mapping user types to their corresponding inline classes
USER_TYPE_INLINES = {
    'student': StudentProfileInline,
    'teacher': TeacherProfileInline,
    'administrator': AdministratorProfileInline,
}

class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'username', 'user_type', 'is_active', 'is_staff', 'is_superuser')
    exclude = ('password',)
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser')
    
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
        (
            'User Type',
            {
                'fields': ('user_type',),
                'classes': ['callapse'],
            }
        ),
        (
            'Permissions',
            {
                'fields': ('is_active', 'is_staff', 'is_superuser'),
                'classes': ['callapse'],  # Changed from 'callapse' to 'tab'
                'description': 'Manage user permissions and access levels'
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
    
# Register your models here.
admin.site.register(User, CustomUserAdmin)