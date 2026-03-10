# Accessibility (a11y) & UX Improvement Plan

**Priority:** Medium  
**Estimated Effort:** 2 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses accessibility gaps and UX improvements identified during the comprehensive project review, focusing on WCAG 2.1 AA compliance.

---

## 1. High: Add ARIA Labels and Roles

**Current Issue:** Interactive elements lack ARIA attributes

### Navigation Updates

```html
<!-- templates/delights/base.html -->
<nav class="navbar navbar-expand-lg navbar-dark bg-primary" role="navigation" aria-label="Main navigation">
    <div class="container">
        <a class="navbar-brand" href="/" aria-label="Django Delights Home">Django Delights</a>
        <button class="navbar-toggler" type="button" 
                data-bs-toggle="collapse" 
                data-bs-target="#navbarNav"
                aria-controls="navbarNav"
                aria-expanded="false"
                aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <!-- ... -->
    </div>
</nav>
```

### Form Updates

```html
<!-- Example: templates/delights/dishes/add.html -->
<form method="post" aria-label="Create new dish">
    {% csrf_token %}
    <div class="mb-3">
        <label for="id_name" class="form-label">Dish Name</label>
        <input type="text" 
               class="form-control" 
               id="id_name" 
               name="name"
               aria-required="true"
               aria-describedby="name-help">
        <div id="name-help" class="form-text">Enter a unique name for the dish</div>
    </div>
    <!-- ... -->
</form>
```

### Table Updates

```html
<!-- templates/delights/dishes/list.html -->
<table class="table table-striped" role="table" aria-label="List of dishes">
    <thead>
        <tr>
            <th scope="col">Name</th>
            <th scope="col">Cost</th>
            <th scope="col">Price</th>
            <th scope="col">Availability</th>
            <th scope="col">Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for dish in dishes %}
        <tr>
            <td><a href="{% url 'dishes:detail' dish.pk %}" aria-label="View {{ dish.name }} details">{{ dish.name }}</a></td>
            <!-- ... -->
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Tasks
- [ ] Add `role` and `aria-label` to navigation
- [ ] Add `aria-label` to all forms
- [ ] Add `aria-required` to required fields
- [ ] Add `aria-describedby` for field help text
- [ ] Add `scope="col"` to table headers
- [ ] Add `aria-label` to action buttons
- [ ] Add `aria-live` regions for dynamic content

---

## 2. High: Add Skip Navigation Link

**Current Issue:** No way to skip to main content

### Implementation

```html
<!-- templates/delights/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- ... -->
    <style>
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: #000;
            color: #fff;
            padding: 8px 16px;
            z-index: 9999;
            text-decoration: none;
        }
        .skip-link:focus {
            top: 0;
        }
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>
    
    <nav class="navbar ...">
        <!-- navigation -->
    </nav>

    <main id="main-content" class="container content-wrapper" tabindex="-1">
        <!-- content -->
    </main>
</body>
</html>
```

### Tasks
- [ ] Add skip link to base.html
- [ ] Add `id="main-content"` to main content area
- [ ] Style skip link to be visible on focus
- [ ] Test with keyboard navigation

---

## 3. High: Improve Color Contrast

**Current Issue:** Badge colors may not meet WCAG AA contrast ratio

### Current Badges
```html
<span class="badge bg-success">Available</span>
<span class="badge bg-danger">Unavailable</span>
```

### Improved Badges with Better Contrast

```html
<style>
    /* Custom badge colors with WCAG AA compliant contrast */
    .badge-available {
        background-color: #146c43;  /* Darker green */
        color: #ffffff;
    }
    .badge-unavailable {
        background-color: #b02a37;  /* Darker red */
        color: #ffffff;
    }
    .badge-warning-custom {
        background-color: #997404;  /* Darker yellow */
        color: #ffffff;
    }
</style>

<span class="badge badge-available">Available</span>
<span class="badge badge-unavailable">Unavailable</span>
```

### Tasks
- [ ] Audit all color combinations with contrast checker
- [ ] Create custom badge classes with compliant colors
- [ ] Update all badge usages
- [ ] Verify contrast ratio >= 4.5:1 for normal text
- [ ] Document color palette with contrast ratios

---

## 4. High: Add Focus Indicators

**Current Issue:** Custom focus styles not defined

### Implementation

```css
/* static/css/accessibility.css */

/* Visible focus indicators */
:focus {
    outline: 2px solid #0d6efd;
    outline-offset: 2px;
}

:focus:not(:focus-visible) {
    outline: none;
}

:focus-visible {
    outline: 2px solid #0d6efd;
    outline-offset: 2px;
}

/* Custom focus for specific elements */
.btn:focus-visible {
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.5);
}

.form-control:focus {
    border-color: #0d6efd;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.nav-link:focus-visible {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

/* Table row focus */
tr:focus-within {
    background-color: rgba(13, 110, 253, 0.1);
}
```

### Tasks
- [ ] Create `accessibility.css` file
- [ ] Add visible focus styles for all interactive elements
- [ ] Test keyboard navigation through all pages
- [ ] Ensure focus order is logical

---

## 5. Medium: Add Client-Side Form Validation

**Current Issue:** No client-side validation, relies on server

### Implementation

```html
<!-- templates/delights/dishes/add.html -->
<form method="post" id="dish-form" novalidate aria-label="Create new dish">
    {% csrf_token %}
    <div class="mb-3">
        <label for="id_name" class="form-label">Dish Name <span class="text-danger" aria-hidden="true">*</span></label>
        <input type="text" 
               class="form-control" 
               id="id_name" 
               name="name"
               required
               minlength="2"
               maxlength="200"
               aria-required="true"
               aria-invalid="false">
        <div class="invalid-feedback" role="alert">
            Please enter a dish name (2-200 characters)
        </div>
    </div>
    
    <div class="mb-3">
        <label for="id_price" class="form-label">Price <span class="text-danger" aria-hidden="true">*</span></label>
        <input type="number" 
               class="form-control" 
               id="id_price" 
               name="price"
               required
               min="0"
               step="0.01"
               aria-required="true">
        <div class="invalid-feedback" role="alert">
            Please enter a valid price (0 or greater)
        </div>
    </div>
    
    <button type="submit" class="btn btn-primary">Create Dish</button>
</form>

<script>
document.getElementById('dish-form').addEventListener('submit', function(e) {
    if (!this.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
        
        // Focus first invalid field
        const firstInvalid = this.querySelector(':invalid');
        if (firstInvalid) {
            firstInvalid.focus();
            firstInvalid.setAttribute('aria-invalid', 'true');
        }
    }
    this.classList.add('was-validated');
});

// Update aria-invalid on input
document.querySelectorAll('input, select, textarea').forEach(function(el) {
    el.addEventListener('input', function() {
        this.setAttribute('aria-invalid', !this.checkValidity());
    });
});
</script>
```

### Tasks
- [ ] Add HTML5 validation attributes to all forms
- [ ] Add client-side validation JavaScript
- [ ] Add `aria-invalid` attribute updates
- [ ] Add error message announcements
- [ ] Test with screen readers

---

## 6. Medium: Add Loading States

**Current Issue:** No loading indicators for async operations

### Implementation

```html
<!-- Loading spinner component -->
<div id="loading-overlay" class="d-none" role="status" aria-live="polite">
    <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
    </div>
</div>

<style>
#loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}
</style>

<script>
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('d-none');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('d-none');
}

// Show loading on form submit
document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
        if (this.checkValidity()) {
            showLoading();
        }
    });
});
</script>
```

### Button Loading State

```html
<button type="submit" class="btn btn-primary" id="submit-btn">
    <span class="btn-text">Create Dish</span>
    <span class="btn-loading d-none">
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        <span class="visually-hidden">Processing...</span>
        Processing...
    </span>
</button>

<script>
document.getElementById('submit-btn').addEventListener('click', function() {
    this.querySelector('.btn-text').classList.add('d-none');
    this.querySelector('.btn-loading').classList.remove('d-none');
    this.disabled = true;
});
</script>
```

### Tasks
- [ ] Create loading overlay component
- [ ] Add loading states to form submissions
- [ ] Add button loading states
- [ ] Ensure loading states are announced to screen readers
- [ ] Add timeout handling for long operations

---

## 7. Medium: Improve Alert/Message Accessibility

**Current Issue:** Messages may not be announced to screen readers

### Implementation

```html
<!-- templates/delights/base.html -->
{% if messages %}
<div aria-live="polite" aria-atomic="true" class="messages-container">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show" 
         role="alert"
         aria-live="assertive">
        <span class="visually-hidden">
            {% if message.tags == 'success' %}Success: {% endif %}
            {% if message.tags == 'error' or message.tags == 'danger' %}Error: {% endif %}
            {% if message.tags == 'warning' %}Warning: {% endif %}
        </span>
        {{ message }}
        <button type="button" 
                class="btn-close" 
                data-bs-dismiss="alert"
                aria-label="Close alert"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

### Tasks
- [ ] Add `role="alert"` to all message containers
- [ ] Add `aria-live` regions
- [ ] Add visually hidden prefixes for message types
- [ ] Improve close button accessibility
- [ ] Test with screen readers

---

## 8. Medium: Add Responsive Design Improvements

**Current Issue:** Some elements may not work well on mobile

### Improvements

```css
/* static/css/responsive.css */

/* Mobile-friendly tables */
@media (max-width: 768px) {
    .table-responsive-stack thead {
        display: none;
    }
    
    .table-responsive-stack tr {
        display: block;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
        border-radius: 4px;
    }
    
    .table-responsive-stack td {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        border: none;
        border-bottom: 1px solid #dee2e6;
    }
    
    .table-responsive-stack td::before {
        content: attr(data-label);
        font-weight: bold;
    }
    
    .table-responsive-stack td:last-child {
        border-bottom: none;
    }
}

/* Touch-friendly buttons */
@media (max-width: 768px) {
    .btn {
        min-height: 44px;
        min-width: 44px;
    }
    
    .btn-sm {
        min-height: 44px;
        padding: 0.5rem 1rem;
    }
}

/* Improved form inputs on mobile */
@media (max-width: 768px) {
    .form-control {
        font-size: 16px; /* Prevents zoom on iOS */
    }
}
```

### Tasks
- [ ] Create responsive.css
- [ ] Add responsive table styles
- [ ] Ensure touch targets are 44x44px minimum
- [ ] Test on various screen sizes
- [ ] Add viewport meta tag (already present)

---

## 9. Low: Internationalization for Currency

**Current Issue:** `$` symbol hardcoded

### Implementation

```python
# settings/base.py
USE_L10N = True
USE_THOUSAND_SEPARATOR = True

# Custom template tag
# delights/templatetags/currency.py
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def currency(value):
    """Format value as currency based on locale."""
    if value is None:
        return ''
    symbol = getattr(settings, 'CURRENCY_SYMBOL', '$')
    return f"{symbol}{value:,.2f}"
```

### Template Usage

```html
{% load currency %}
<td>{{ dish.price|currency }}</td>
```

### Tasks
- [ ] Create currency template tag
- [ ] Add CURRENCY_SYMBOL to settings
- [ ] Update all templates to use currency filter
- [ ] Document currency configuration

---

## 10. Low: Screen Reader Testing Checklist

### Manual Testing Checklist

- [ ] **Navigation**: Can navigate entire site using keyboard only
- [ ] **Forms**: All form fields have labels and are announced correctly
- [ ] **Tables**: Table headers are associated with cells
- [ ] **Images**: All images have alt text (when added)
- [ ] **Links**: Link text is descriptive
- [ ] **Buttons**: Button purpose is clear
- [ ] **Errors**: Form errors are announced
- [ ] **Dynamic content**: Updates are announced via aria-live
- [ ] **Modals**: Focus is trapped and returned correctly
- [ ] **Headings**: Heading hierarchy is logical (h1 > h2 > h3)

### Tools to Use

- **WAVE**: Browser extension for accessibility testing
- **axe DevTools**: Automated accessibility testing
- **NVDA**: Free screen reader for Windows
- **VoiceOver**: Built-in screen reader for macOS
- **Lighthouse**: Chrome DevTools accessibility audit

### Tasks
- [ ] Install WAVE browser extension
- [ ] Run Lighthouse accessibility audit
- [ ] Test with NVDA or VoiceOver
- [ ] Document and fix all issues found
- [ ] Add accessibility testing to QA process

---

## Dependencies to Add

```txt
# No new Python dependencies required
# CSS/JS changes only
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `static/css/accessibility.css` | Create |
| `static/css/responsive.css` | Create |
| `templates/delights/base.html` | Modify |
| `templates/delights/*/list.html` | Modify (all list templates) |
| `templates/delights/*/add.html` | Modify (all form templates) |
| `delights/templatetags/currency.py` | Create |

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | ARIA labels, skip link, focus indicators | 1 sprint |
| Phase 2 | Form validation, loading states, messages | 0.5 sprint |
| Phase 3 | Responsive improvements, testing | 0.5 sprint |

---

## Success Metrics

- [ ] Lighthouse accessibility score >= 90
- [ ] WAVE shows 0 errors
- [ ] All pages navigable by keyboard
- [ ] Screen reader testing completed
- [ ] Color contrast ratio >= 4.5:1
- [ ] Touch targets >= 44x44px on mobile
- [ ] No accessibility regressions in CI
