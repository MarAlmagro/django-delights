# Code Quality & Best Practices Improvement Plan

**Priority:** Medium  
**Estimated Effort:** 2 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses code quality improvements identified during the comprehensive project review, focusing on architecture, maintainability, and Django best practices.

---

## 1. High: Extract Business Logic to Service Layer

**Current Issue:** Business logic (cost calculation, availability) is in `views.py`

### Current Structure
```
delights/
├── views.py          # 867 lines with business logic mixed in
├── models.py         # Data models only
```

### Proposed Structure
```
delights/
├── services/
│   ├── __init__.py
│   ├── pricing.py        # Cost and price calculations
│   ├── availability.py   # Availability checks and updates
│   ├── inventory.py      # Inventory management
│   └── purchases.py      # Purchase workflow logic
├── views.py              # HTTP handling only
├── models.py             # Data models with basic methods
```

### Implementation

```python
# delights/services/pricing.py
"""
Pricing service for cost and price calculations.
"""
from decimal import Decimal
from django.conf import settings

from delights.models import Dish, Menu


def calculate_dish_cost(dish: Dish) -> Decimal:
    """
    Calculate dish cost from recipe requirements.
    
    Args:
        dish: The dish to calculate cost for
        
    Returns:
        Total cost as Decimal
    """
    total_cost = Decimal('0')
    for requirement in dish.recipe_requirements.select_related('ingredient'):
        total_cost += (
            requirement.ingredient.price_per_unit * requirement.quantity_required
        )
    return total_cost


def calculate_menu_cost(menu: Menu) -> Decimal:
    """
    Calculate menu cost from constituent dishes.
    
    Args:
        menu: The menu to calculate cost for
        
    Returns:
        Total cost as Decimal
    """
    return sum(
        (dish.cost for dish in menu.dishes.all()),
        Decimal('0')
    )


def calculate_suggested_price(cost: Decimal, margin: Decimal = None) -> Decimal:
    """
    Calculate suggested selling price with margin.
    
    Args:
        cost: Base cost
        margin: Profit margin (default from settings)
        
    Returns:
        Suggested price as Decimal
    """
    if margin is None:
        margin = Decimal(str(settings.GLOBAL_MARGIN))
    return cost * (1 + margin)
```

```python
# delights/services/availability.py
"""
Availability service for checking and updating availability status.
"""
from delights.models import Dish, Ingredient, Menu


def check_dish_availability(dish: Dish) -> bool:
    """
    Check if dish is available based on ingredient stock.
    
    A dish is available if:
    - It has at least one recipe requirement
    - All required ingredients have sufficient quantity
    
    Args:
        dish: The dish to check
        
    Returns:
        True if available, False otherwise
    """
    requirements = dish.recipe_requirements.select_related('ingredient')
    
    if not requirements.exists():
        return False
    
    for requirement in requirements:
        if requirement.ingredient.quantity_available < requirement.quantity_required:
            return False
    
    return True


def check_menu_availability(menu: Menu) -> bool:
    """
    Check if menu is available based on dish availability.
    
    A menu is available if:
    - It has at least one dish
    - All dishes are available
    
    Args:
        menu: The menu to check
        
    Returns:
        True if available, False otherwise
    """
    dishes = menu.dishes.all()
    
    if not dishes.exists():
        return False
    
    return all(dish.is_available for dish in dishes)


def update_dish_availability(dish: Dish) -> None:
    """
    Update dish cost and availability status.
    
    Args:
        dish: The dish to update
    """
    from delights.services.pricing import calculate_dish_cost
    
    dish.cost = calculate_dish_cost(dish)
    dish.is_available = check_dish_availability(dish)
    dish.save(update_fields=['cost', 'is_available'])


def update_dishes_for_ingredient(ingredient: Ingredient) -> None:
    """
    Update all dishes that use the specified ingredient.
    
    Args:
        ingredient: The ingredient that changed
    """
    dishes = Dish.objects.filter(
        recipe_requirements__ingredient=ingredient
    ).distinct()
    
    for dish in dishes:
        update_dish_availability(dish)


def update_menu_availability(menu: Menu) -> None:
    """
    Update menu cost and availability status.
    
    Args:
        menu: The menu to update
    """
    from delights.services.pricing import calculate_menu_cost
    
    menu.cost = calculate_menu_cost(menu)
    menu.is_available = check_menu_availability(menu)
    menu.save(update_fields=['cost', 'is_available'])


def update_menus_for_dish(dish: Dish) -> None:
    """
    Update all menus that contain the specified dish.
    
    Args:
        dish: The dish that changed
    """
    menus = Menu.objects.filter(dishes=dish)
    
    for menu in menus:
        update_menu_availability(menu)
```

### Tasks
- [ ] Create `delights/services/` package
- [ ] Create `pricing.py` with cost/price functions
- [ ] Create `availability.py` with availability functions
- [ ] Create `inventory.py` with inventory functions
- [ ] Create `purchases.py` with purchase workflow
- [ ] Update views to use services
- [ ] Update API views to use services
- [ ] Add unit tests for services
- [ ] Update imports throughout codebase

---

## 2. High: Use Settings for GLOBAL_MARGIN

**Current Issue:** `GLOBAL_MARGIN` hardcoded in `views.py`

### Current Code (views.py line 182)
```python
GLOBAL_MARGIN = 0.20  # 20% margin
```

### Solution

```python
# delights/services/pricing.py
from django.conf import settings

def get_global_margin():
    """Get global margin from settings."""
    return Decimal(str(getattr(settings, 'GLOBAL_MARGIN', 0.20)))
```

### Update Views
```python
# delights/views.py
from delights.services.pricing import get_global_margin, calculate_suggested_price

# Replace hardcoded GLOBAL_MARGIN with:
margin = get_global_margin()
dish.price = calculate_suggested_price(dish.cost, margin)
```

### Tasks
- [ ] Remove `GLOBAL_MARGIN` constant from views.py
- [ ] Use `settings.GLOBAL_MARGIN` everywhere
- [ ] Add `get_global_margin()` helper function
- [ ] Update all usages in views and API

---

## 3. Medium: Add Model Methods

**Current Issue:** Models lack computed properties and validation

### Enhanced Models

```python
# delights/models.py

class Dish(models.Model):
    # ... existing fields ...

    @property
    def calculated_cost(self) -> Decimal:
        """Calculate cost from recipe requirements."""
        total = Decimal('0')
        for req in self.recipe_requirements.select_related('ingredient'):
            total += req.ingredient.price_per_unit * req.quantity_required
        return total

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.cost == 0:
            return Decimal('0')
        return ((self.price - self.cost) / self.cost) * 100

    @property
    def is_profitable(self) -> bool:
        """Check if dish is profitable."""
        return self.price > self.cost

    def can_make(self, quantity: int = 1) -> bool:
        """Check if we can make the specified quantity."""
        for req in self.recipe_requirements.select_related('ingredient'):
            needed = req.quantity_required * quantity
            if req.ingredient.quantity_available < needed:
                return False
        return True

    def get_missing_ingredients(self) -> list:
        """Get list of ingredients with insufficient quantity."""
        missing = []
        for req in self.recipe_requirements.select_related('ingredient'):
            if req.ingredient.quantity_available < req.quantity_required:
                missing.append({
                    'ingredient': req.ingredient,
                    'required': req.quantity_required,
                    'available': req.ingredient.quantity_available,
                    'shortage': req.quantity_required - req.ingredient.quantity_available,
                })
        return missing

    def clean(self):
        """Validate model data."""
        from django.core.exceptions import ValidationError
        
        if self.price < 0:
            raise ValidationError({'price': 'Price cannot be negative.'})
        if self.cost < 0:
            raise ValidationError({'cost': 'Cost cannot be negative.'})


class Ingredient(models.Model):
    # ... existing fields ...

    @property
    def is_low_stock(self) -> bool:
        """Check if ingredient is below low stock threshold."""
        from django.conf import settings
        threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
        return self.quantity_available < threshold

    @property
    def total_value(self) -> Decimal:
        """Calculate total inventory value."""
        return self.price_per_unit * self.quantity_available

    def adjust_quantity(self, amount: Decimal) -> None:
        """
        Adjust quantity by the specified amount.
        
        Args:
            amount: Positive to add, negative to subtract
        """
        self.quantity_available += amount
        if self.quantity_available < 0:
            self.quantity_available = Decimal('0')
        self.save(update_fields=['quantity_available'])

    def clean(self):
        """Validate model data."""
        from django.core.exceptions import ValidationError
        
        if self.price_per_unit < 0:
            raise ValidationError({'price_per_unit': 'Price cannot be negative.'})
        if self.quantity_available < 0:
            raise ValidationError({'quantity_available': 'Quantity cannot be negative.'})


class Purchase(models.Model):
    # ... existing fields ...

    @property
    def item_count(self) -> int:
        """Get total number of items in purchase."""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def is_completed(self) -> bool:
        """Check if purchase is completed."""
        return self.status == self.STATUS_COMPLETED

    @property
    def is_cancelled(self) -> bool:
        """Check if purchase is cancelled."""
        return self.status == self.STATUS_CANCELLED

    def calculate_total(self) -> Decimal:
        """Calculate total from items."""
        return self.items.aggregate(
            total=models.Sum('subtotal')
        )['total'] or Decimal('0')
```

### Tasks
- [ ] Add computed properties to Dish model
- [ ] Add computed properties to Ingredient model
- [ ] Add computed properties to Purchase model
- [ ] Add `clean()` validation methods
- [ ] Add helper methods for common operations
- [ ] Update views to use model methods
- [ ] Add tests for model methods

---

## 4. Medium: Consider Django Signals for Cascading Updates

**Current Issue:** Availability updates are manual

### Signal Implementation

```python
# delights/signals.py
"""
Django signals for automatic updates.
"""
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from delights.models import Ingredient, RecipeRequirement, Dish, Menu
from delights.services.availability import (
    update_dish_availability,
    update_dishes_for_ingredient,
    update_menu_availability,
    update_menus_for_dish,
)


@receiver(post_save, sender=Ingredient)
def ingredient_saved(sender, instance, **kwargs):
    """Update dish availability when ingredient changes."""
    # Only update if quantity changed
    if kwargs.get('update_fields') is None or 'quantity_available' in kwargs.get('update_fields', []):
        update_dishes_for_ingredient(instance)


@receiver([post_save, post_delete], sender=RecipeRequirement)
def recipe_requirement_changed(sender, instance, **kwargs):
    """Update dish when recipe requirement changes."""
    update_dish_availability(instance.dish)
    update_menus_for_dish(instance.dish)


@receiver(post_save, sender=Dish)
def dish_saved(sender, instance, **kwargs):
    """Update menus when dish availability changes."""
    if kwargs.get('update_fields') is None or 'is_available' in kwargs.get('update_fields', []):
        update_menus_for_dish(instance)


@receiver(m2m_changed, sender=Menu.dishes.through)
def menu_dishes_changed(sender, instance, action, **kwargs):
    """Update menu when dishes are added/removed."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        update_menu_availability(instance)
```

### Register Signals

```python
# delights/apps.py
from django.apps import AppConfig


class DelightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delights'

    def ready(self):
        import delights.signals  # noqa: F401
```

### Tasks
- [ ] Create `delights/signals.py`
- [ ] Add signal handlers for Ingredient changes
- [ ] Add signal handlers for RecipeRequirement changes
- [ ] Add signal handlers for Dish changes
- [ ] Add signal handlers for Menu M2M changes
- [ ] Update `apps.py` to register signals
- [ ] Remove manual update calls from views
- [ ] Add tests for signal behavior
- [ ] Document signal behavior

---

## 5. Medium: Split Large Views File

**Current Issue:** `views.py` is 867 lines

### Proposed Structure

```
delights/
├── views/
│   ├── __init__.py           # Re-exports all views
│   ├── mixins.py             # Shared mixins (move from mixins.py)
│   ├── units.py              # UnitListView, UnitCreateView, etc.
│   ├── ingredients.py        # IngredientListView, inventory_adjust, etc.
│   ├── dishes.py             # DishListView, manage_recipe_requirements, etc.
│   ├── menus.py              # MenuListView, manage_menu_items, etc.
│   ├── purchases.py          # Purchase workflow views
│   ├── dashboard.py          # DashboardView
│   ├── users.py              # User management views
│   └── auth.py               # LoginView
```

### Example Split

```python
# delights/views/__init__.py
"""
Django Delights views.

This package contains all views for the application,
organized by entity type.
"""

from .auth import LoginView
from .dashboard import DashboardView
from .dishes import (
    DishCreateView,
    DishDetailView,
    DishListView,
    DishUpdateView,
    manage_recipe_requirements,
)
from .ingredients import (
    IngredientCreateView,
    IngredientListView,
    IngredientUpdateView,
    inventory_adjust,
)
from .menus import (
    MenuCreateView,
    MenuDetailView,
    MenuListView,
    MenuUpdateView,
    manage_menu_items,
)
from .purchases import (
    PurchaseDetailView,
    PurchaseListView,
    purchase_confirm,
    purchase_create,
    purchase_finalize,
)
from .units import (
    UnitCreateView,
    UnitListView,
    UnitUpdateView,
    unit_toggle_active,
)
from .users import (
    UserCreateView,
    UserListView,
    UserUpdateView,
    user_reset_password,
    user_toggle_active,
)

__all__ = [
    # Auth
    'LoginView',
    # Dashboard
    'DashboardView',
    # Units
    'UnitListView',
    'UnitCreateView',
    'UnitUpdateView',
    'unit_toggle_active',
    # Ingredients
    'IngredientListView',
    'IngredientCreateView',
    'IngredientUpdateView',
    'inventory_adjust',
    # Dishes
    'DishListView',
    'DishDetailView',
    'DishCreateView',
    'DishUpdateView',
    'manage_recipe_requirements',
    # Menus
    'MenuListView',
    'MenuDetailView',
    'MenuCreateView',
    'MenuUpdateView',
    'manage_menu_items',
    # Purchases
    'PurchaseListView',
    'PurchaseDetailView',
    'purchase_create',
    'purchase_confirm',
    'purchase_finalize',
    # Users
    'UserListView',
    'UserCreateView',
    'UserUpdateView',
    'user_toggle_active',
    'user_reset_password',
]
```

### Tasks
- [ ] Create `delights/views/` package
- [ ] Move unit views to `views/units.py`
- [ ] Move ingredient views to `views/ingredients.py`
- [ ] Move dish views to `views/dishes.py`
- [ ] Move menu views to `views/menus.py`
- [ ] Move purchase views to `views/purchases.py`
- [ ] Move dashboard view to `views/dashboard.py`
- [ ] Move user views to `views/users.py`
- [ ] Move auth views to `views/auth.py`
- [ ] Create `__init__.py` with re-exports
- [ ] Update URL imports
- [ ] Verify all tests pass
- [ ] Delete old `views.py`

---

## 6. Low: Add Type Hints to Views

**Current Issue:** Views lack comprehensive type hints

### Example

```python
# delights/views/dishes.py
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView

class DishListView(LoginRequiredMixin, ListView):
    model = Dish
    template_name: str = "delights/dishes/list.html"
    context_object_name: str = "dishes"

    def get_queryset(self) -> QuerySet[Dish]:
        return Dish.objects.all().order_by('name')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context


@login_required
def manage_recipe_requirements(request: HttpRequest, pk: int) -> HttpResponse:
    """Manage recipe requirements for a dish."""
    dish: Dish = get_object_or_404(Dish, pk=pk)
    # ...
```

### Tasks
- [ ] Add type hints to all view functions
- [ ] Add type hints to all view classes
- [ ] Add type hints to helper functions
- [ ] Run mypy to verify types
- [ ] Fix any type errors

---

## 7. Low: Improve Form Validation

**Current Issue:** Forms could have more validation

### Enhanced Forms

```python
# delights/forms.py
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Unit, Ingredient, Dish, RecipeRequirement, Menu


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'description', 'price']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '200',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError('Name must be at least 2 characters.')
        return name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price


class RecipeRequirementForm(forms.ModelForm):
    class Meta:
        model = RecipeRequirement
        fields = ['ingredient', 'quantity_required']
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-select'}),
            'quantity_required': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }),
        }

    def clean_quantity_required(self):
        quantity = self.cleaned_data.get('quantity_required')
        if quantity is not None and quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        ingredient = cleaned_data.get('ingredient')
        
        # Check if ingredient is active
        if ingredient and hasattr(ingredient, 'unit') and not ingredient.unit.is_active:
            raise ValidationError(
                f'Cannot use ingredient "{ingredient.name}" - its unit is inactive.'
            )
        
        return cleaned_data
```

### Tasks
- [ ] Add `clean_*` methods to all forms
- [ ] Add cross-field validation in `clean()`
- [ ] Add HTML5 validation attributes
- [ ] Add custom error messages
- [ ] Test form validation

---

## Dependencies

No new dependencies required for code quality improvements.

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Service layer, settings usage | 1 sprint |
| Phase 2 | Model methods, signals | 0.5 sprint |
| Phase 3 | Split views, type hints | 0.5 sprint |

---

## Success Metrics

- [ ] Business logic extracted to services
- [ ] No hardcoded configuration values
- [ ] Models have computed properties
- [ ] Signals handle cascading updates
- [ ] Views file split into modules
- [ ] Type hints on all public functions
- [ ] All tests pass after refactoring
- [ ] No increase in code complexity
