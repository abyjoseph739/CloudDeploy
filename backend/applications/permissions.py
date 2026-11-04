from rest_framework.permissions import BasePermission
from accounts.models import User


class IsAdminOrApplicationOwner(BasePermission):
    """
    Object-level permission:
    - Admins and superusers can inspect and modify any application.
    - Developers can only inspect and modify applications they created.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "role", None) == User.Role.ADMIN or request.user.is_superuser:
            return True

        return obj.created_by == request.user

