from rest_framework import permissions


class CanAccessPanel(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'userprofile'):
            return False

        return request.user.userprofile.can_access_panel