from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_authenticated and user.is_superuser


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin access"""

    def test_func(self):
        return is_admin(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            from django.contrib import messages

            messages.error(self.request, "Access denied. Admin privileges required.")
            return redirect("purchases:list")
        return super().handle_no_permission()


def redirect_after_login(user):
    """Redirect user after login based on role"""
    if user.is_superuser:
        return "/dashboard/"
    else:
        return "/purchases/"


class AuditLogMixin:
    """
    Mixin to add audit logging capabilities to views.

    Logs user actions with IP address and user agent information.
    """

    def log_action(self, action, obj=None, changes=None):
        """
        Log an action to the audit log.

        Args:
            action: Action type (create, update, delete, etc.)
            obj: The object being acted upon
            changes: Dictionary of changes made
        """
        from delights.models import AuditLog
        from delights.middleware import get_client_ip

        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            model_name=obj.__class__.__name__ if obj else "",
            object_id=obj.pk if obj else None,
            object_repr=str(obj) if obj else "",
            changes=changes or {},
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:500],
        )
