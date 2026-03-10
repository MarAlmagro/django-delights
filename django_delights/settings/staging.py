"""
Django staging settings for django_delights project.

Similar to production but with additional debugging capabilities.
"""

import os

from .prod import *  # noqa: F401, F403, E501

# =============================================================================
# Staging-specific Settings
# =============================================================================

# Allow more verbose logging in staging
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405

# Enable Django Debug Toolbar in staging (optional)
if os.getenv("ENABLE_DEBUG_TOOLBAR", "False").lower() == "true":
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]

# Staging environment flag
STAGING = True

# Less strict throttling for staging
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "200/hour",
    "user": "2000/hour",
}

# Override Sentry environment if configured
if SENTRY_DSN:  # noqa: F405
    import sentry_sdk

    sentry_sdk.set_tag("environment", "staging")
