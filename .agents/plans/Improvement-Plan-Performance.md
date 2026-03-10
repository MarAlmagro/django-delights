# Performance & Scalability Improvement Plan

**Priority:** High  
**Estimated Effort:** 2 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses performance bottlenecks and scalability improvements identified during the comprehensive project review.

---

## 1. Critical: Add Database Indexes

**Current Issue:** Missing indexes on frequently filtered/sorted columns

### Models to Update

```python
# delights/models.py

class Dish(models.Model):
    # ... existing fields ...
    is_available: models.BooleanField[bool, bool] = models.BooleanField(
        default=False, 
        help_text="Available if all ingredients are sufficient",
        db_index=True  # ADD INDEX
    )

class Ingredient(models.Model):
    # ... existing fields ...
    quantity_available: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        db_index=True  # ADD INDEX
    )

class Purchase(models.Model):
    # ... existing fields ...
    status: models.CharField[str, str] = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_COMPLETED,
        db_index=True  # ADD INDEX
    )
    timestamp: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        db_index=True  # ADD INDEX
    )

    class Meta:
        # ... existing meta ...
        indexes = [
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['user', 'status']),
        ]
```

### Tasks
- [ ] Add `db_index=True` to `Dish.is_available`
- [ ] Add `db_index=True` to `Ingredient.quantity_available`
- [ ] Add `db_index=True` to `Purchase.status`
- [ ] Add `db_index=True` to `Purchase.timestamp`
- [ ] Add composite indexes for common query patterns
- [ ] Generate and apply migration
- [ ] Verify indexes with `EXPLAIN ANALYZE` queries

---

## 2. Critical: Fix N+1 Queries in Dashboard

**File:** `delights/views.py`  
**Current Issue:** Dashboard iterates over PurchaseItems without optimization

### Current Code (Lines 756-760)
```python
total_cost = 0
for purchase_item in PurchaseItem.objects.filter(
    purchase__status="completed"
).select_related("dish"):
    total_cost += purchase_item.quantity * purchase_item.dish.cost
```

### Optimized Solution
```python
from django.db.models import F, Sum

# Use database aggregation instead of Python loop
total_cost = PurchaseItem.objects.filter(
    purchase__status=Purchase.STATUS_COMPLETED
).annotate(
    item_cost=F('quantity') * F('dish__cost')
).aggregate(
    total=Sum('item_cost')
)['total'] or Decimal('0')
```

### Tasks
- [ ] Refactor dashboard cost calculation to use aggregation
- [ ] Add database-level calculation for profit
- [ ] Optimize top dishes query
- [ ] Add query count assertions in tests
- [ ] Profile dashboard view with Django Debug Toolbar

---

## 3. High: Implement Redis Caching for Dashboard

**Current Issue:** Expensive dashboard calculations run on every request

### Solution

```python
# delights/views.py
from django.core.cache import cache
from django.conf import settings

class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "delights/dashboard/index.html"
    CACHE_KEY = "dashboard_metrics"
    CACHE_TIMEOUT = 300  # 5 minutes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Try cache first
        metrics = cache.get(self.CACHE_KEY)
        if metrics is None:
            metrics = self._calculate_metrics()
            cache.set(self.CACHE_KEY, metrics, self.CACHE_TIMEOUT)
        
        context.update(metrics)
        return context

    def _calculate_metrics(self):
        # ... existing calculation logic ...
        return {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'profit': profit,
            'top_dishes': list(top_dishes),
            'low_stock_ingredients': list(low_stock_ingredients),
        }
```

### Cache Invalidation

```python
# delights/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete], sender=Purchase)
def invalidate_dashboard_cache(sender, **kwargs):
    cache.delete('dashboard_metrics')

@receiver([post_save, post_delete], sender=PurchaseItem)
def invalidate_dashboard_cache_on_item(sender, **kwargs):
    cache.delete('dashboard_metrics')
```

### Tasks
- [ ] Add caching to DashboardView
- [ ] Create cache invalidation signals
- [ ] Configure Redis in development docker-compose
- [ ] Add cache hit/miss logging
- [ ] Test cache behavior

---

## 4. High: Optimize Availability Updates

**File:** `delights/views.py`  
**Current Issue:** `update_menu_availability()` updates ALL menus on every change

### Current Code (Lines 232-242)
```python
def update_menu_availability(menu=None):
    if menu:
        menus = [menu]
    else:
        menus = Menu.objects.all()  # Updates ALL menus!
    
    for menu in menus:
        menu.cost = update_menu_cost(menu)
        menu.is_available = check_menu_availability(menu)
        menu.save()
```

### Optimized Solution
```python
def update_menu_availability_for_dish(dish):
    """Update only menus containing the specified dish."""
    affected_menus = Menu.objects.filter(dishes=dish)
    for menu in affected_menus:
        menu.cost = update_menu_cost(menu)
        menu.is_available = check_menu_availability(menu)
        menu.save(update_fields=['cost', 'is_available'])

def update_dish_availability_from_ingredient(ingredient):
    """Update all dishes that use this ingredient."""
    dishes = Dish.objects.filter(
        recipe_requirements__ingredient=ingredient
    ).distinct()
    
    for dish in dishes:
        update_dish_availability(dish)
        # Only update menus for this specific dish
        update_menu_availability_for_dish(dish)
```

### Tasks
- [ ] Create `update_menu_availability_for_dish()` function
- [ ] Refactor `update_dish_availability_from_ingredient()` to use targeted updates
- [ ] Use `update_fields` in save() calls
- [ ] Add bulk_update for multiple dishes
- [ ] Add performance tests

---

## 5. Medium: Split Large Views File

**Current Issue:** `views.py` is 867 lines, hard to maintain

### Proposed Structure
```
delights/
├── views/
│   ├── __init__.py          # Re-exports all views
│   ├── base.py              # Helper functions, constants
│   ├── units.py             # Unit CRUD views
│   ├── ingredients.py       # Ingredient views + inventory
│   ├── dishes.py            # Dish views + recipe management
│   ├── menus.py             # Menu views
│   ├── purchases.py         # Purchase workflow views
│   ├── dashboard.py         # Dashboard view
│   └── users.py             # User management views
```

### Tasks
- [ ] Create `views/` package directory
- [ ] Move helper functions to `views/base.py`
- [ ] Split views by entity
- [ ] Update imports in URL files
- [ ] Verify all tests pass

---

## 6. Medium: Add Database Connection Pooling

**Current Issue:** No connection pooling in development

### Solution

```python
# settings/dev.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 60,  # Keep connections for 60 seconds
    }
}

# settings/prod.py (already has this, verify)
DATABASES = {
    'default': {
        ...
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}
```

### Tasks
- [ ] Add `CONN_MAX_AGE` to dev settings
- [ ] Verify prod settings have connection pooling
- [ ] Consider PgBouncer for high-traffic scenarios
- [ ] Document connection pool settings

---

## 7. Medium: Optimize ORM Queries

### Query Optimization Patterns

```python
# Use only() to limit fields
Dish.objects.filter(is_available=True).only('id', 'name', 'price')

# Use values() for read-only data
Purchase.objects.filter(status='completed').values('id', 'total_price_at_purchase')

# Use bulk operations
Ingredient.objects.filter(id__in=ids).update(quantity_available=F('quantity_available') - amount)

# Use exists() instead of count() for boolean checks
if Dish.objects.filter(is_available=True).exists():
    ...

# Use iterator() for large querysets
for item in PurchaseItem.objects.filter(...).iterator():
    ...
```

### Tasks
- [ ] Audit all ORM queries with Django Debug Toolbar
- [ ] Add `only()` to list views
- [ ] Use `bulk_update()` for batch operations
- [ ] Replace `count() > 0` with `exists()`
- [ ] Add query count tests

---

## 8. Low: Add Query Monitoring

### Solution: Django Debug Toolbar (Development)

```python
# settings/dev.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ['127.0.0.1']
```

### Solution: Query Logging (Production)

```python
# settings/base.py
LOGGING = {
    ...
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
        },
    },
}
```

### Tasks
- [ ] Add Django Debug Toolbar to dev dependencies
- [ ] Configure query logging for production
- [ ] Add slow query alerts (queries > 100ms)
- [ ] Document performance monitoring

---

## 9. Low: Implement Pagination for All List Views

**Current Issue:** Web views don't have pagination

### Solution

```python
# delights/views.py
from django.core.paginator import Paginator

class DishListView(LoginRequiredMixin, ListView):
    model = Dish
    template_name = "delights/dishes/list.html"
    context_object_name = "dishes"
    paginate_by = 20  # ADD PAGINATION
```

### Template Update
```html
{% if is_paginated %}
<nav aria-label="Page navigation">
    <ul class="pagination justify-content-center">
        {% if page_obj.has_previous %}
        <li class="page-item">
            <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a>
        </li>
        {% endif %}
        <li class="page-item active">
            <span class="page-link">Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
        </li>
        {% if page_obj.has_next %}
        <li class="page-item">
            <a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a>
        </li>
        {% endif %}
    </ul>
</nav>
{% endif %}
```

### Tasks
- [ ] Add `paginate_by` to all ListView classes
- [ ] Create pagination partial template
- [ ] Include pagination in all list templates
- [ ] Test pagination with large datasets

---

## Testing & Verification

### Performance Test Script

```python
# tests/test_performance.py
import pytest
from django.test.utils import override_settings

@pytest.mark.slow
class TestQueryPerformance:
    def test_dashboard_query_count(self, client_logged_in_admin, django_assert_num_queries):
        """Dashboard should execute limited queries."""
        with django_assert_num_queries(10):  # Set expected max
            response = client_logged_in_admin.get('/dashboard/')
            assert response.status_code == 200

    def test_dish_list_query_count(self, client_logged_in_staff, django_assert_num_queries):
        """Dish list should not have N+1 queries."""
        DishFactory.create_batch(50)
        with django_assert_num_queries(3):  # 1 count + 1 dishes + 1 user
            response = client_logged_in_staff.get('/dishes/')
            assert response.status_code == 200
```

### Tasks
- [ ] Create performance test file
- [ ] Add query count assertions
- [ ] Set up CI performance regression tests
- [ ] Document performance baselines

---

## Dependencies to Add

```txt
# requirements-dev.txt additions
django-debug-toolbar>=4.3.0
pytest-django>=4.8.0  # for django_assert_num_queries
```

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Database indexes, N+1 fixes | 1 sprint |
| Phase 2 | Caching, availability optimization | 1 sprint |
| Phase 3 | Code organization, monitoring | 1 sprint |

---

## Success Metrics

- [ ] Dashboard loads in < 200ms
- [ ] All list views have < 5 queries
- [ ] No N+1 queries detected
- [ ] Cache hit rate > 80% for dashboard
- [ ] Database indexes verified with EXPLAIN
- [ ] Performance tests in CI pipeline
