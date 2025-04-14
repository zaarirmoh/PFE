from rest_framework import permissions

class IsThemeSupervisor(permissions.BasePermission):
    """
    Allow access only to theme supervisors (proposer or co-supervisor).
    """
    def has_object_permission(self, request, view, obj):
        theme = obj.theme
        user = request.user
        
        # Check if user is the theme proposer or a co-supervisor
        is_proposer = theme.proposed_by == user
        is_co_supervisor = theme.co_supervisors.filter(id=user.id).exists()
        
        return is_proposer or is_co_supervisor