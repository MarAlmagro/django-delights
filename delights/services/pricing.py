"""
Pricing service for cost and price calculations.
"""
from decimal import Decimal
from django.conf import settings

from delights.models import Dish, Menu


def get_global_margin() -> Decimal:
    """
    Get global margin from settings.
    
    Returns:
        Global profit margin as Decimal (default 0.20 = 20%)
    """
    return Decimal(str(getattr(settings, 'GLOBAL_MARGIN', 0.20)))


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
        margin = get_global_margin()
    return cost * (1 + margin)
