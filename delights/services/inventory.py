"""
Inventory service for inventory management operations.
"""
from decimal import Decimal
from typing import Dict, List

from delights.models import Ingredient, Dish


def adjust_ingredient_quantity(ingredient: Ingredient, amount: Decimal) -> None:
    """
    Adjust ingredient quantity by the specified amount.
    
    Args:
        ingredient: The ingredient to adjust
        amount: Positive to add, negative to subtract
    """
    ingredient.quantity_available += amount
    if ingredient.quantity_available < 0:
        ingredient.quantity_available = Decimal('0')
    ingredient.save(update_fields=['quantity_available'])


def check_low_stock_ingredients(threshold: Decimal = None) -> List[Ingredient]:
    """
    Get list of ingredients below the low stock threshold.
    
    Args:
        threshold: Low stock threshold (default from settings)
        
    Returns:
        List of ingredients with low stock
    """
    from django.conf import settings
    
    if threshold is None:
        threshold = Decimal(str(getattr(settings, 'LOW_STOCK_THRESHOLD', 10)))
    
    return list(Ingredient.objects.filter(
        quantity_available__lt=threshold
    ).order_by('quantity_available'))


def get_inventory_value() -> Dict[str, Decimal]:
    """
    Calculate total inventory value.
    
    Returns:
        Dictionary with total value and count
    """
    from django.db.models import Sum, F, DecimalField
    from django.db.models.functions import Coalesce
    
    result = Ingredient.objects.aggregate(
        total_value=Coalesce(
            Sum(F('price_per_unit') * F('quantity_available'), output_field=DecimalField()),
            Decimal('0')
        ),
        count=Coalesce(Sum('quantity_available'), Decimal('0'))
    )
    
    return {
        'total_value': result['total_value'] or Decimal('0'),
        'total_count': result['count'] or Decimal('0'),
    }


def deduct_ingredients_for_dish(dish: Dish, quantity: int = 1) -> bool:
    """
    Deduct ingredients needed to make a dish.
    
    Args:
        dish: The dish to make
        quantity: Number of dishes to make
        
    Returns:
        True if successful, False if insufficient ingredients
    """
    from django.db import transaction
    
    # Check if we have enough ingredients
    for requirement in dish.recipe_requirements.select_related('ingredient'):
        needed = requirement.quantity_required * quantity
        if requirement.ingredient.quantity_available < needed:
            return False
    
    # Deduct ingredients
    with transaction.atomic():
        for requirement in dish.recipe_requirements.select_related('ingredient'):
            needed = requirement.quantity_required * quantity
            requirement.ingredient.quantity_available -= needed
            requirement.ingredient.save(update_fields=['quantity_available'])
    
    return True
