"""
Purchase service for purchase workflow logic.
"""

from decimal import Decimal
from typing import Dict, Any

from django.contrib.auth.models import User
from django.db import transaction

from delights.models import Purchase, PurchaseItem, Dish, Menu


def create_purchase(user: User) -> Purchase:
    """
    Create a new purchase for the user.

    Args:
        user: The user making the purchase

    Returns:
        New Purchase instance
    """
    return Purchase.objects.create(user=user, status=Purchase.STATUS_PENDING)


def add_dish_to_purchase(
    purchase: Purchase, dish: Dish, quantity: int = 1
) -> PurchaseItem:
    """
    Add a dish to a purchase.

    Args:
        purchase: The purchase to add to
        dish: The dish to add
        quantity: Quantity to add

    Returns:
        Created or updated PurchaseItem
    """
    # Check if item already exists
    item, created = PurchaseItem.objects.get_or_create(
        purchase=purchase,
        dish=dish,
        defaults={
            "quantity": quantity,
            "unit_price": dish.price,
            "subtotal": dish.price * quantity,
        },
    )

    if not created:
        # Update existing item
        item.quantity += quantity
        item.subtotal = item.unit_price * item.quantity
        item.save(update_fields=["quantity", "subtotal"])

    return item


def add_menu_to_purchase(
    purchase: Purchase, menu: Menu, quantity: int = 1
) -> PurchaseItem:
    """
    Add a menu to a purchase.

    Args:
        purchase: The purchase to add to
        menu: The menu to add
        quantity: Quantity to add

    Returns:
        Created or updated PurchaseItem
    """
    # Check if item already exists
    item, created = PurchaseItem.objects.get_or_create(
        purchase=purchase,
        menu=menu,
        defaults={
            "quantity": quantity,
            "unit_price": menu.price,
            "subtotal": menu.price * quantity,
        },
    )

    if not created:
        # Update existing item
        item.quantity += quantity
        item.subtotal = item.unit_price * item.quantity
        item.save(update_fields=["quantity", "subtotal"])

    return item


def calculate_purchase_total(purchase: Purchase) -> Decimal:
    """
    Calculate total for a purchase.

    Args:
        purchase: The purchase to calculate

    Returns:
        Total as Decimal
    """
    from django.db.models import Sum

    result = purchase.items.aggregate(total=Sum("subtotal"))
    return result["total"] or Decimal("0")


def _check_item_availability(item) -> bool:
    """Check if a purchase item is available."""
    if item.dish:
        return item.dish.is_available
    elif item.menu:
        return item.menu.is_available
    return True


def _deduct_ingredients_for_item(item) -> bool:
    """Deduct ingredients for a purchase item."""
    from delights.services.inventory import deduct_ingredients_for_dish

    if item.dish:
        return deduct_ingredients_for_dish(item.dish, item.quantity)
    elif item.menu:
        for dish in item.menu.dishes.all():
            if not deduct_ingredients_for_dish(dish, item.quantity):
                return False
    return True


def finalize_purchase(purchase: Purchase) -> bool:
    """
    Finalize a purchase and deduct ingredients.

    Args:
        purchase: The purchase to finalize

    Returns:
        True if successful, False if insufficient ingredients
    """
    with transaction.atomic():
        # Check availability for all items
        for item in purchase.items.select_related("dish", "menu"):
            if not _check_item_availability(item):
                return False

        # Deduct ingredients
        for item in purchase.items.select_related("dish", "menu"):
            if not _deduct_ingredients_for_item(item):
                return False

        # Update purchase total and status
        purchase.total = calculate_purchase_total(purchase)
        purchase.status = Purchase.STATUS_COMPLETED
        purchase.save(update_fields=["total", "status"])

    return True


def get_purchase_summary(purchase: Purchase) -> Dict[str, Any]:
    """
    Get summary information for a purchase.

    Args:
        purchase: The purchase to summarize

    Returns:
        Dictionary with purchase summary
    """
    items = purchase.items.select_related("dish", "menu").all()

    return {
        "purchase": purchase,
        "items": items,
        "item_count": sum(item.quantity for item in items),
        "total": calculate_purchase_total(purchase),
    }
