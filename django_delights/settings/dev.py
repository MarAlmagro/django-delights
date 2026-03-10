"""
Django development settings for django_delights project.

These settings are for local development only.
For production settings, see prod.py.
"""

import os

from .base import *  # noqa: F401, F403

# =============================================================================
# Development-specific Settings
# =============================================================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]

# Use a development-safe secret key if none provided
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-key-not-for-production-use-only-in-development",
)


# =============================================================================
# Database - SQLite for Development
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        "CONN_MAX_AGE": 60,  # Keep connections for 60 seconds
    }
}


# =============================================================================
# Static Files - Development
# =============================================================================

# Use simple static file storage in development
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


# =============================================================================
# Email - Console Backend for Development
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# =============================================================================
# CORS - Allow all origins in development
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True


# =============================================================================
# REST Framework - Relaxed throttling for development
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/hour",
    "user": "10000/hour",
}


# =============================================================================
# Debug Toolbar - Performance Monitoring
# =============================================================================

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1", "localhost"]


# =============================================================================
# Logging - More verbose for development
# =============================================================================

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405
