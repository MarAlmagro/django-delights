"""
Custom exceptions for Django Delights application.

This module defines domain-specific exceptions for better error handling
and more informative error messages.
"""


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


class InventoryError(Exception):
    """Base exception for inventory-related errors."""
    pass


class NegativeInventoryError(InventoryError):
    """Raised when attempting to set negative inventory."""
    
    def __init__(self, ingredient_name, attempted_quantity):
        self.ingredient_name = ingredient_name
        self.attempted_quantity = attempted_quantity
        super().__init__(
            f"Cannot set negative inventory for {ingredient_name}: {attempted_quantity}"
        )
