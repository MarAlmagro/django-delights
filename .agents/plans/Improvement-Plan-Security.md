# Security Improvement Plan

**Priority:** Critical to High  
**Estimated Effort:** 2-3 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses security vulnerabilities and improvements identified during the comprehensive project review.

---

## 1. Critical: Remove Insecure Default Secret Key

**File:** `django_delights/settings.py`  
**Current Issue:** Fallback insecure secret key in development settings

### Current Code
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-kk643w!rx4&#c=o(&asz@h$l#vmxqsy%d0hv3516v&hq8$7fg_')
```

### Solution
```python
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
```

### Tasks
- [ ] Remove fallback secret key from `settings.py`
- [ ] Update `.env.example` with clear instructions
- [ ] Add validation in both `settings.py` and `settings/base.py`
- [ ] Update README quick start to emphasize `.env` setup

---

## 2. High: Add Rate Limiting for Web Views

**Current Issue:** Only API has throttling; web views are unprotected

### Solution: Install django-ratelimit

```bash
pip install django-ratelimit
```

### Implementation

```python
# delights/decorators.py
from django_ratelimit.decorators import ratelimit

# Apply to sensitive views
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def purchase_finalize(request):
    ...

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def user_reset_password(request, pk):
    ...
```

### Tasks
- [ ] Add `django-ratelimit` to requirements.txt
- [ ] Create rate limit decorators for sensitive endpoints
- [ ] Apply to: login, purchase_finalize, user_reset_password, inventory_adjust
- [ ] Add rate limit exceeded template/handler
- [ ] Document rate limits in API.md

---

## 3. High: Add Brute Force Protection

**Current Issue:** No protection against login brute force attacks

### Solution: Install django-axes

```bash
pip install django-axes
```

### Configuration

```python
# settings/base.py
INSTALLED_APPS = [
    ...
    'axes',
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_TEMPLATE = 'registration/lockout.html'
AXES_RESET_ON_SUCCESS = True
```

### Tasks
- [ ] Add `django-axes` to requirements.txt
- [ ] Configure in settings/base.py
- [ ] Create lockout template
- [ ] Add admin view for locked accounts
- [ ] Test lockout and reset functionality

---

## 4. High: Implement Content Security Policy

**Current Issue:** No CSP headers configured

### Solution: Install django-csp

```bash
pip install django-csp
```

### Configuration

```python
# settings/base.py
MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    ...
]

# CSP Configuration
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "cdn.jsdelivr.net", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
```

### Tasks
- [ ] Add `django-csp` to requirements.txt
- [ ] Configure CSP headers in settings
- [ ] Test all pages work with CSP enabled
- [ ] Add CSP report-uri for violation monitoring
- [ ] Document CSP policy

---

## 5. Medium: Session Security Improvements

**Current Issue:** No explicit session regeneration on login

### Solution

```python
# delights/views.py
from django.contrib.auth import login as auth_login
from django.contrib.sessions.models import Session

class LoginView(BaseLoginView):
    def form_valid(self, form):
        # Regenerate session on login to prevent fixation
        if self.request.session.session_key:
            self.request.session.cycle_key()
        return super().form_valid(form)
```

### Additional Session Settings

```python
# settings/prod.py
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

### Tasks
- [ ] Add session regeneration in LoginView
- [ ] Configure session timeout settings
- [ ] Add SameSite cookie attribute
- [ ] Test session behavior across browsers

---

## 6. Medium: Input Validation Enhancement

**Current Issue:** Forms rely solely on Django's built-in validation

### Solution: Add explicit validation

```python
# delights/forms.py
import bleach

class DishForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Sanitize HTML
        return bleach.clean(name, tags=[], strip=True)
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        # Allow limited HTML
        return bleach.clean(
            description, 
            tags=['p', 'br', 'strong', 'em'],
            strip=True
        )
```

### Tasks
- [ ] Add `bleach` to requirements.txt
- [ ] Add input sanitization to all text fields
- [ ] Add validation for numeric ranges
- [ ] Add XSS test cases
- [ ] Document input validation rules

---

## 7. Medium: API Security Headers

**Current Issue:** Missing security headers on API responses

### Solution: Add security middleware

```python
# delights/middleware.py
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=()'
        return response
```

### Tasks
- [ ] Create security headers middleware
- [ ] Add to MIDDLEWARE in settings
- [ ] Test headers with security scanner
- [ ] Document security headers

---

## 8. Low: GitHub Secret Scanning

**Current Issue:** No automated secret scanning in repository

### Solution: Enable GitHub features

1. Go to Repository Settings > Security > Code security and analysis
2. Enable:
   - Dependency graph
   - Dependabot alerts
   - Dependabot security updates
   - Secret scanning
   - Push protection

### Tasks
- [ ] Enable GitHub secret scanning
- [ ] Enable Dependabot alerts
- [ ] Add `.github/dependabot.yml` configuration
- [ ] Review and address any existing alerts

---

## 9. Low: Audit Logging

**Current Issue:** No tracking of sensitive operations

### Solution: Create audit log model

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
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
```

### Tasks
- [ ] Create AuditLog model
- [ ] Create audit logging mixin/decorator
- [ ] Apply to sensitive operations
- [ ] Add admin view for audit logs
- [ ] Add retention policy for old logs

---

## Testing Checklist

After implementing security improvements:

- [ ] Run Bandit security scan: `bandit -r delights/`
- [ ] Run Safety check: `safety check`
- [ ] Test rate limiting with curl
- [ ] Test brute force protection
- [ ] Verify CSP headers with browser dev tools
- [ ] Run OWASP ZAP scan
- [ ] Test session fixation prevention
- [ ] Verify all secrets are in environment variables

---

## Dependencies to Add

```txt
# requirements.txt additions
django-ratelimit>=4.1.0
django-axes>=6.3.0
django-csp>=3.8
bleach>=6.1.0
```

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Critical fixes (secret key, rate limiting) | 1 sprint |
| Phase 2 | High priority (axes, CSP, session) | 1 sprint |
| Phase 3 | Medium/Low (audit logging, headers) | 1 sprint |

---

## Success Metrics

- [ ] Bandit scan passes with no high/medium issues
- [ ] All secrets removed from codebase
- [ ] Rate limiting active on sensitive endpoints
- [ ] CSP headers present on all responses
- [ ] Audit logs capturing sensitive operations
- [ ] GitHub security features enabled
