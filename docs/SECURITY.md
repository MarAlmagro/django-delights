# Security Implementation Guide

This document outlines the security features implemented in Django Delights and provides guidance for maintaining security best practices.

## Implemented Security Features

### 1. Secret Key Management ✅

**Status:** Implemented  
**Priority:** Critical

- Removed insecure fallback secret key from settings
- SECRET_KEY must be set in environment variables
- Application will not start without a valid SECRET_KEY

**Configuration:**
```python
# django_delights/settings/base.py
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
```

**Setup:**
```bash
# Generate a new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Add to .env file
SECRET_KEY=your-generated-secret-key-here
```

---

### 2. Rate Limiting ✅

**Status:** Implemented  
**Priority:** High  
**Package:** `django-ratelimit>=4.1.0`

Rate limiting protects against brute force attacks and API abuse.

**Protected Endpoints:**
- `purchase_finalize`: 10 requests/minute per IP
- `inventory_adjust`: 10 requests/minute per IP
- `user_reset_password`: 5 requests/minute per IP

**Implementation:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def purchase_finalize(request):
    ...
```

**Customization:**
- Modify rate limits in `delights/views.py`
- Available keys: 'ip', 'user', 'header:x-real-ip'
- Rate format: 'count/period' (e.g., '10/m', '100/h', '1000/d')

---

### 3. Brute Force Protection ✅

**Status:** Implemented  
**Priority:** High  
**Package:** `django-axes>=6.3.0`

Protects login endpoints from brute force attacks.

**Configuration:**
```python
# django_delights/settings/base.py
AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = timedelta(minutes=30)  # 30-minute lockout
AXES_RESET_ON_SUCCESS = True  # Reset counter on successful login
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
```

**Features:**
- Locks account after 5 failed login attempts
- 30-minute cooldown period
- Tracks by combination of username and IP
- Custom lockout template at `templates/registration/lockout.html`

**Admin Management:**
- View locked accounts in Django admin under "Axes"
- Manually unlock accounts if needed

---

### 4. Content Security Policy (CSP) ✅

**Status:** Implemented  
**Priority:** High  
**Package:** `django-csp>=3.8`

Prevents XSS attacks by controlling resource loading.

**Configuration:**
```python
# django_delights/settings/base.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "cdn.jsdelivr.net", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
```

**Allowed Resources:**
- Scripts/Styles: Self-hosted and cdn.jsdelivr.net
- Images: Self-hosted and data URIs
- Forms: Submit only to same origin
- Frames: Blocked (prevents clickjacking)

---

### 5. Session Security ✅

**Status:** Implemented  
**Priority:** Medium

**Features:**
- Session regeneration on login (prevents session fixation)
- HttpOnly cookies (prevents XSS cookie theft)
- SameSite=Lax (CSRF protection)

**Configuration:**
```python
# django_delights/settings/base.py
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
```

**LoginView Implementation:**
```python
def form_valid(self, form):
    if self.request.session.session_key:
        self.request.session.cycle_key()
    return super().form_valid(form)
```

---

### 6. Input Validation & Sanitization ✅

**Status:** Implemented  
**Priority:** Medium  
**Package:** `bleach>=6.1.0`

Prevents XSS attacks through HTML sanitization.

**Implementation:**
```python
# delights/forms.py
import bleach

def clean_name(self):
    name = self.cleaned_data.get("name")
    if name:
        name = bleach.clean(name.strip(), tags=[], strip=True)
    return name

def clean_description(self):
    description = self.cleaned_data.get("description")
    if description:
        description = bleach.clean(
            description,
            tags=["p", "br", "strong", "em"],
            strip=True
        )
    return description
```

**Sanitized Fields:**
- All name fields: Strip all HTML
- Description fields: Allow limited safe HTML tags (p, br, strong, em)

---

### 7. Security Headers ✅

**Status:** Implemented  
**Priority:** Medium

Custom middleware adds security headers to all responses.

**Headers Added:**
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer info
- `Permissions-Policy: geolocation=(), microphone=()` - Restricts browser features

**Implementation:**
```python
# delights/middleware.py
class SecurityHeadersMiddleware:
    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=()'
        return response
```

---

### 8. Audit Logging ✅

**Status:** Implemented  
**Priority:** Low

Tracks sensitive operations for security monitoring and compliance.

**Model:**
```python
# delights/models.py
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

**Usage:**
```python
from delights.utils import log_audit
from delights.models import AuditLog

# Log a purchase
log_audit(
    user=request.user,
    action=AuditLog.ACTION_PURCHASE,
    model_name='Purchase',
    object_id=purchase.id,
    changes={'total': str(purchase.total)},
    request=request
)
```

**Admin Interface:**
- View audit logs in Django admin
- Filter by action, model, timestamp
- Read-only (cannot be modified)
- Only superusers can delete logs

---

## Security Checklist

### Before Deployment

- [ ] Set strong SECRET_KEY in production environment
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Enable HTTPS and set secure cookie flags
- [ ] Review and adjust rate limits for production traffic
- [ ] Set up monitoring for locked accounts
- [ ] Review CSP policy and adjust for your CDN/resources
- [ ] Configure database backups including audit logs
- [ ] Set up log aggregation for security events

### Production Settings

```python
# django_delights/settings/prod.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# HTTPS Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session Settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

---

## Testing Security Features

### 1. Test Rate Limiting

```bash
# Test with curl
for i in {1..15}; do
  curl -X POST http://localhost:8000/purchases/finalize/ \
    -H "Cookie: sessionid=your-session-id"
  echo "Request $i"
done
```

### 2. Test Brute Force Protection

```bash
# Attempt multiple failed logins
for i in {1..6}; do
  curl -X POST http://localhost:8000/accounts/login/ \
    -d "username=testuser&password=wrongpassword"
done
```

### 3. Test CSP Headers

```bash
# Check CSP headers
curl -I http://localhost:8000/
```

### 4. Security Scanning

```bash
# Install security tools
pip install bandit safety

# Run Bandit security scan
bandit -r delights/

# Check for vulnerable dependencies
safety check
```

---

## Monitoring & Maintenance

### Regular Tasks

1. **Review Audit Logs** (Weekly)
   - Check for suspicious activity
   - Monitor failed login attempts
   - Review sensitive operations

2. **Update Dependencies** (Monthly)
   ```bash
   pip list --outdated
   safety check
   ```

3. **Review Locked Accounts** (Daily)
   - Check Axes admin for locked accounts
   - Investigate patterns of lockouts

4. **Security Scans** (Weekly)
   ```bash
   bandit -r delights/
   ```

### Alerts to Configure

- Multiple failed login attempts from same IP
- Unusual number of rate limit violations
- Changes to user permissions
- Large inventory adjustments
- High-value purchases

---

## Additional Recommendations

### Not Yet Implemented

1. **GitHub Secret Scanning**
   - Enable in repository settings
   - Configure Dependabot alerts

2. **Two-Factor Authentication**
   - Consider `django-otp` for admin users
   - Especially important for superuser accounts

3. **API Key Management**
   - If exposing public APIs, implement API key rotation
   - Use `django-rest-framework-api-key`

4. **Database Encryption**
   - Consider encrypting sensitive fields
   - Use `django-encrypted-model-fields`

5. **Penetration Testing**
   - Run OWASP ZAP scans regularly
   - Consider professional security audit

---

## Incident Response

### If Security Breach Detected

1. **Immediate Actions:**
   - Rotate SECRET_KEY
   - Invalidate all sessions
   - Review audit logs
   - Check for unauthorized changes

2. **Investigation:**
   - Identify entry point
   - Assess data exposure
   - Document timeline

3. **Remediation:**
   - Patch vulnerabilities
   - Update dependencies
   - Strengthen affected areas

4. **Communication:**
   - Notify affected users
   - Document lessons learned
   - Update security procedures

---

## Support & Resources

- Django Security Documentation: https://docs.djangoproject.com/en/stable/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security Releases: https://www.djangoproject.com/weblog/
- Security Mailing List: security@djangoproject.com

---

**Last Updated:** 2026-03-10  
**Security Implementation Version:** 1.0
