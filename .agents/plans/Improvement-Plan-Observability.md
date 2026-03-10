# Observability & Error Handling Improvement Plan

**Priority:** High  
**Estimated Effort:** 2 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses observability gaps and error handling improvements identified during the comprehensive project review.

---

## 1. High: Add Request ID Tracking

**Current Issue:** No correlation IDs for request tracing across logs

### Solution: Install django-request-id

```bash
pip install django-request-id
```

### Configuration

```python
# settings/base.py
MIDDLEWARE = [
    'request_id.middleware.RequestIdMiddleware',  # Add first
    'django.middleware.security.SecurityMiddleware',
    ...
]

# Update logging format
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'request_id.logging.RequestIdFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} [{request_id}] {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
    },
    ...
}

# Add request ID to API responses
REST_FRAMEWORK = {
    ...
    'DEFAULT_RENDERER_CLASSES': [
        'delights.api.renderers.RequestIdRenderer',
    ],
}
```

### Custom Renderer

```python
# delights/api/renderers.py
from rest_framework.renderers import JSONRenderer
from request_id import get_current_request_id

class RequestIdRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        if response:
            response['X-Request-ID'] = get_current_request_id() or ''
        return super().render(data, accepted_media_type, renderer_context)
```

### Tasks
- [ ] Add `django-request-id` to requirements.txt
- [ ] Configure middleware and logging
- [ ] Create custom API renderer
- [ ] Add request ID to error responses
- [ ] Test request ID propagation

---

## 2. High: Implement Specific Exception Handling

**File:** `delights/views.py`  
**Current Issue:** Generic `except Exception` catches everything

### Current Code (Lines 687-691)
```python
except Exception as e:
    messages.error(
        request, f"Purchase could not be completed: {str(e)}. Please try again."
    )
    return redirect(URL_PURCHASES_CONFIRM)
```

### Improved Solution

```python
# delights/exceptions.py
class PurchaseError(Exception):
    """Base exception for purchase-related errors."""
    pass

class InsufficientInventoryError(PurchaseError):
    """Raised when inventory is insufficient for purchase."""
    def __init__(self, ingredient_name, required, available):
        self.ingredient_name = ingredient_name
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient {ingredient_name}: need {required}, have {available}"
        )

class DishUnavailableError(PurchaseError):
    """Raised when a dish is no longer available."""
    def __init__(self, dish_name):
        self.dish_name = dish_name
        super().__init__(f"Dish '{dish_name}' is no longer available")

class ConcurrentModificationError(PurchaseError):
    """Raised when data was modified during transaction."""
    pass
```

### Updated View

```python
# delights/views.py
from delights.exceptions import (
    PurchaseError,
    InsufficientInventoryError,
    DishUnavailableError,
)
import logging

logger = logging.getLogger(__name__)

@login_required
@transaction.atomic
def purchase_finalize(request):
    try:
        # ... existing logic ...
        pass
    except DishUnavailableError as e:
        logger.warning(f"Purchase failed - dish unavailable: {e}", extra={
            'user_id': request.user.id,
            'dish': e.dish_name,
        })
        messages.error(request, str(e))
        return redirect(URL_PURCHASES_ADD)
    except InsufficientInventoryError as e:
        logger.warning(f"Purchase failed - insufficient inventory: {e}", extra={
            'user_id': request.user.id,
            'ingredient': e.ingredient_name,
        })
        messages.error(request, str(e))
        return redirect(URL_PURCHASES_CONFIRM)
    except PurchaseError as e:
        logger.error(f"Purchase failed: {e}", exc_info=True)
        messages.error(request, "Purchase could not be completed. Please try again.")
        return redirect(URL_PURCHASES_CONFIRM)
    except Exception as e:
        logger.exception(f"Unexpected error during purchase: {e}")
        messages.error(request, "An unexpected error occurred. Please contact support.")
        return redirect(URL_PURCHASES_ADD)
```

### Tasks
- [ ] Create `delights/exceptions.py` with custom exceptions
- [ ] Update `purchase_finalize` with specific exception handling
- [ ] Add logging with context to all exception handlers
- [ ] Update API views with similar exception handling
- [ ] Add tests for each exception type

---

## 3. High: Add Sentry Error Tracking

**Current Issue:** No external error monitoring

### Solution: Install Sentry SDK

```bash
pip install sentry-sdk
```

### Configuration

```python
# settings/prod.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

SENTRY_DSN = os.getenv('SENTRY_DSN')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,
        send_default_pii=False,  # Don't send PII
        environment=os.getenv('DJANGO_ENV', 'production'),
        release=os.getenv('APP_VERSION', '1.0.0'),
    )
```

### Tasks
- [ ] Add `sentry-sdk` to requirements.txt
- [ ] Configure Sentry in prod.py
- [ ] Add SENTRY_DSN to .env.example
- [ ] Test error reporting
- [ ] Set up Sentry alerts

---

## 4. Medium: Add Structured Logging with Context

**Current Issue:** Logs lack user and request context

### Solution: Custom Logging Middleware

```python
# delights/middleware.py
import logging
import threading

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class LoggingContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user if request.user.is_authenticated else None
        _thread_locals.path = request.path
        _thread_locals.method = request.method
        
        response = self.get_response(request)
        return response

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.user = getattr(_thread_locals, 'user', None)
        record.user_id = record.user.id if record.user else 'anonymous'
        record.username = record.user.username if record.user else 'anonymous'
        record.path = getattr(_thread_locals, 'path', '-')
        record.method = getattr(_thread_locals, 'method', '-')
        return True
```

### Updated Logging Config

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'context': {
            '()': 'delights.middleware.ContextFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} [{username}] {method} {path} {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(username)s %(path)s %(module)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['context'],
        },
    },
    ...
}
```

### Tasks
- [ ] Create logging context middleware
- [ ] Add `python-json-logger` to requirements.txt
- [ ] Configure JSON logging for production
- [ ] Add context to all logger calls
- [ ] Test log output format

---

## 5. Medium: Add Prometheus Metrics

**Current Issue:** No metrics collection for monitoring

### Solution: Install django-prometheus

```bash
pip install django-prometheus
```

### Configuration

```python
# settings/base.py
INSTALLED_APPS = [
    'django_prometheus',
    ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Database metrics
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        ...
    }
}
```

### Custom Metrics

```python
# delights/metrics.py
from prometheus_client import Counter, Histogram

purchase_counter = Counter(
    'delights_purchases_total',
    'Total number of purchases',
    ['status']
)

purchase_value = Histogram(
    'delights_purchase_value',
    'Purchase value distribution',
    buckets=[5, 10, 25, 50, 100, 250, 500]
)

inventory_adjustment = Counter(
    'delights_inventory_adjustments_total',
    'Total inventory adjustments',
    ['ingredient', 'action']
)
```

### Usage in Views

```python
# delights/views.py
from delights.metrics import purchase_counter, purchase_value

def purchase_finalize(request):
    ...
    purchase_counter.labels(status='completed').inc()
    purchase_value.observe(float(purchase.total_price_at_purchase))
    ...
```

### Tasks
- [ ] Add `django-prometheus` to requirements.txt
- [ ] Configure middleware and database wrapper
- [ ] Create custom business metrics
- [ ] Add `/metrics` endpoint
- [ ] Set up Grafana dashboards

---

## 6. Medium: Create Audit Logging

**Current Issue:** No tracking of who changed what

### Solution: Audit Log Model

```python
# delights/models.py
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('purchase', 'Purchase'),
        ('inventory_adjust', 'Inventory Adjustment'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} at {self.timestamp}"
```

### Audit Logging Mixin

```python
# delights/mixins.py
from delights.models import AuditLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class AuditLogMixin:
    def log_action(self, action, obj=None, changes=None):
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            model_name=obj.__class__.__name__ if obj else '',
            object_id=obj.pk if obj else None,
            object_repr=str(obj) if obj else '',
            changes=changes or {},
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
        )
```

### Tasks
- [ ] Create AuditLog model
- [ ] Create AuditLogMixin
- [ ] Apply to sensitive views (purchases, inventory, user management)
- [ ] Add admin view for audit logs
- [ ] Add retention policy (delete logs older than X days)
- [ ] Add audit log export functionality

---

## 7. Low: Add Health Check Enhancements

**Current Issue:** Basic health check doesn't verify dependencies

### Enhanced Health Check

```python
# delights/api/views.py
from django.db import connection
from django.core.cache import cache
import redis

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        health = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            health['checks']['database'] = 'ok'
        except Exception as e:
            health['checks']['database'] = f'error: {str(e)}'
            health['status'] = 'unhealthy'
        
        # Cache check (if configured)
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health['checks']['cache'] = 'ok'
            else:
                health['checks']['cache'] = 'error: cache not responding'
        except Exception as e:
            health['checks']['cache'] = f'error: {str(e)}'
        
        status_code = 200 if health['status'] == 'healthy' else 503
        return Response(health, status=status_code)
```

### Tasks
- [ ] Enhance health check with dependency verification
- [ ] Add database connectivity check
- [ ] Add cache connectivity check
- [ ] Add readiness vs liveness endpoints
- [ ] Update Docker health check to use enhanced endpoint

---

## 8. Low: Add Request/Response Logging

**Current Issue:** No visibility into API request/response patterns

### Solution: Request Logging Middleware

```python
# delights/middleware.py
import logging
import time
import json

logger = logging.getLogger('delights.requests')

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log API requests
        if request.path.startswith('/api/'):
            logger.info(
                'API Request',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'user_id': request.user.id if request.user.is_authenticated else None,
                }
            )
        
        # Log slow requests
        if duration > 1.0:  # > 1 second
            logger.warning(
                f'Slow request: {request.path}',
                extra={
                    'duration_ms': round(duration * 1000, 2),
                }
            )
        
        return response
```

### Tasks
- [ ] Create request logging middleware
- [ ] Configure separate logger for requests
- [ ] Add slow request alerts
- [ ] Set up log aggregation (ELK/Loki)

---

## Dependencies to Add

```txt
# requirements.txt additions
sentry-sdk>=1.40.0
django-prometheus>=2.3.0
python-json-logger>=2.0.0

# requirements-dev.txt additions
django-request-id>=1.0.0
```

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Exception handling, request IDs | 1 sprint |
| Phase 2 | Sentry, structured logging | 0.5 sprint |
| Phase 3 | Metrics, audit logging | 1 sprint |

---

## Success Metrics

- [ ] All errors captured in Sentry
- [ ] Request IDs in all log entries
- [ ] Audit logs for all sensitive operations
- [ ] Prometheus metrics exposed
- [ ] Health check verifies all dependencies
- [ ] Slow requests logged and alerted
- [ ] No generic `except Exception` without logging
