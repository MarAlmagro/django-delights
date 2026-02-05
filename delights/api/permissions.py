"""
Custom permissions for Django Delights API.

Defines role-based access control for API endpoints.
"""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission that only allows admin (superuser) access.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to all authenticated users,
    but write access only to admins.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for admins
        return request.user.is_superuser


class IsStaffOrAdmin(permissions.BasePermission):
    """
    Permission that allows access to staff or admin users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows access to object owners or admins.
    Used for purchases where users should only see their own.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Admins can access any object
        if request.user.is_superuser:
            return True

        # Check if the object has a user field
        if hasattr(obj, "user"):
            return obj.user == request.user

        return False


class CanEditPrice(permissions.BasePermission):
    """
    Permission that allows price editing only by admins.
    Staff can edit other fields but not prices.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, check if price is being modified
        if request.method in ["PUT", "PATCH", "POST"]:
            if "price" in request.data and not request.user.is_superuser:
                return False

        return request.user.is_staff or request.user.is_superuser
