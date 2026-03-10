"""
Security middleware for Django Delights.

Adds security headers to all responses.
"""

import logging
import threading
import time

_thread_locals = threading.local()


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, "user", None)


def get_client_ip(request):
    """Extract client IP from request, considering proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


class LoggingContextMiddleware:
    """
    Middleware to add user and request context to thread-local storage.

    This allows loggers to access user information without explicitly
    passing it through the call stack.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user if request.user.is_authenticated else None
        _thread_locals.path = request.path
        _thread_locals.method = request.method

        response = self.get_response(request)
        return response


class ContextFilter(logging.Filter):
    """
    Logging filter that adds user and request context to log records.

    Adds the following fields to each log record:
    - user_id: ID of the authenticated user or 'anonymous'
    - username: Username of the authenticated user or 'anonymous'
    - path: Request path
    - method: HTTP method
    """

    def filter(self, record):
        user = getattr(_thread_locals, "user", None)
        record.user_id = user.id if user else "anonymous"
        record.username = user.username if user else "anonymous"
        record.path = getattr(_thread_locals, "path", "-")
        record.method = getattr(_thread_locals, "method", "-")
        return True


class RequestLoggingMiddleware:
    """
    Middleware to log API requests and slow requests.

    Logs:
    - All API requests with method, path, status, duration, and user
    - Slow requests (>1 second) with warnings
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("delights.requests")

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # Log API requests
        if request.path.startswith("/api/"):
            self.logger.info(
                "API Request",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "user_id": request.user.id
                    if request.user.is_authenticated
                    else None,
                },
            )

        # Log slow requests
        if duration > 1.0:  # > 1 second
            self.logger.warning(
                f"Slow request: {request.path}",
                extra={
                    "duration_ms": round(duration * 1000, 2),
                },
            )

        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(), microphone=()
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response
