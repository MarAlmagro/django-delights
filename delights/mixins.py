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
            messages.error(self.request, 'Access denied. Admin privileges required.')
            return redirect('purchases:list')
        return super().handle_no_permission()


def redirect_after_login(user):
    """Redirect user after login based on role"""
    if user.is_superuser:
        return '/dashboard/'
    else:
        return '/purchases/'

