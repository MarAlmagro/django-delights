"""
Django Delights - Service Layer

This package contains business logic extracted from views,
organized by domain responsibility.

Services:
    - pricing: Cost and price calculations
    - availability: Availability checks and updates
    - inventory: Inventory management operations
    - purchases: Purchase workflow logic
"""

from .pricing import (
    calculate_dish_cost,
    calculate_menu_cost,
    calculate_suggested_price,
    get_global_margin,
)
from .availability import (
    check_dish_availability,
    check_menu_availability,
    update_dish_availability,
    update_dishes_for_ingredient,
    update_menu_availability,
    update_menus_for_dish,
)

__all__ = [
    # Pricing
    'calculate_dish_cost',
    'calculate_menu_cost',
    'calculate_suggested_price',
    'get_global_margin',
    # Availability
    'check_dish_availability',
    'check_menu_availability',
    'update_dish_availability',
    'update_dishes_for_ingredient',
    'update_menu_availability',
    'update_menus_for_dish',
]
