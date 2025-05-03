# meetings/permissions.py
from rest_framework import permissions
from users.models import Teacher
from .models import JuryMember


class IsTeacherOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow teachers to create and modify meetings.
    Read-only access is allowed for other users.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed for teachers
        return hasattr(request.user, 'teacher')
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed for teachers
        return hasattr(request.user, 'teacher')


class IsMeetingCreatorOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow the meeting creator to modify meetings.
    Read-only access is allowed for other users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the meeting creator
        return obj.scheduled_by == request.user


class IsJuryPresident(permissions.BasePermission):
    """
    Custom permission to only allow jury presidents to update results.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is president of this defense
        return JuryMember.objects.filter(
            defense=obj,
            user=request.user,
            is_president=True
        ).exists()