"""
Django Delights - Data Models

This module defines the core data models for the restaurant inventory
and ordering management system.

Models:
    - Unit: Units of measurement (gram, liter, etc.)
    - Ingredient: Raw materials with pricing and inventory
    - Dish: Menu items with auto-calculated cost and availability
    - RecipeRequirement: Links dishes to ingredients with quantities
    - Menu: Composite items containing multiple dishes
    - Purchase: Order records with user and timestamp
    - PurchaseItem: Individual items in a purchase with frozen prices
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class Unit(models.Model):
    """
    Unit of measurement for ingredients.

    Examples: gram (g), kilogram (kg), liter (l), unit (ea)

    Attributes:
        name: Short identifier (e.g., 'g', 'kg', 'l')
        description: Full name (e.g., 'gram', 'kilogram')
        is_active: Soft-delete flag for deactivating units
    """

    name: models.CharField[str, str] = models.CharField(max_length=50, unique=True)
    description: models.CharField[str, str] = models.CharField(max_length=200)
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    # Type hints for reverse relations
    if TYPE_CHECKING:
        ingredients: RelatedManager[Ingredient]

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """
    Ingredient with unit, price per unit, and available quantity.

    Used to track inventory and calculate dish costs.

    Attributes:
        name: Ingredient name (e.g., 'Flour', 'Tomatoes')
        unit: Foreign key to Unit model
        price_per_unit: Cost per unit of measurement
        quantity_available: Current inventory level
    """

    name: models.CharField[str, str] = models.CharField(max_length=200)
    unit: models.ForeignKey[Unit, Unit] = models.ForeignKey(
        Unit, on_delete=models.PROTECT, related_name="ingredients"
    )
    price_per_unit: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Cost per unit of measurement"
    )
    quantity_available: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    # Type hints for reverse relations
    if TYPE_CHECKING:
        recipe_requirements: RelatedManager[RecipeRequirement]

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        ordering = ["name"]

    @property
    def is_low_stock(self) -> bool:
        """Check if ingredient is below low stock threshold."""
        from django.conf import settings

        threshold = getattr(settings, "LOW_STOCK_THRESHOLD", 10)
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
            self.quantity_available = Decimal("0")
        self.save(update_fields=["quantity_available"])

    def clean(self):
        """Validate model data."""
        from django.core.exceptions import ValidationError

        if self.price_per_unit < 0:
            raise ValidationError({"price_per_unit": "Price cannot be negative."})
        if self.quantity_available < 0:
            raise ValidationError(
                {"quantity_available": "Quantity cannot be negative."}
            )

    def __str__(self) -> str:
        return f"{self.name} ({self.quantity_available} {self.unit.name})"


class Dish(models.Model):
    """
    Dish/MenuItem with cost, price, and availability.

    Cost is auto-calculated from recipe requirements.
    Availability is determined by ingredient stock levels.

    Attributes:
        name: Dish name (e.g., 'Margherita Pizza')
        description: Optional description
        cost: Auto-calculated from ingredient costs
        price: Selling price (cost + margin)
        is_available: True if all required ingredients are in stock
    """

    name: models.CharField[str, str] = models.CharField(max_length=200)
    description: models.TextField[str, str] = models.TextField(blank=True)
    cost: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Auto-calculated from ingredients",
    )
    price: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Selling price"
    )
    is_available: models.BooleanField[bool, bool] = models.BooleanField(
        default=False, help_text="Available if all ingredients are sufficient"
    )

    # Type hints for reverse relations
    if TYPE_CHECKING:
        recipe_requirements: RelatedManager[RecipeRequirement]
        menus: RelatedManager[Menu]
        purchase_items: RelatedManager[PurchaseItem]

    class Meta:
        verbose_name = "Dish"
        verbose_name_plural = "Dishes"
        ordering = ["name"]

    @property
    def calculated_cost(self) -> Decimal:
        """Calculate cost from recipe requirements."""
        total = Decimal("0")
        for req in self.recipe_requirements.select_related("ingredient"):
            total += req.ingredient.price_per_unit * req.quantity_required
        return total

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.cost == 0:
            return Decimal("0")
        return ((self.price - self.cost) / self.cost) * 100

    @property
    def is_profitable(self) -> bool:
        """Check if dish is profitable."""
        return self.price > self.cost

    def can_make(self, quantity: int = 1) -> bool:
        """Check if we can make the specified quantity."""
        for req in self.recipe_requirements.select_related("ingredient"):
            needed = req.quantity_required * quantity
            if req.ingredient.quantity_available < needed:
                return False
        return True

    def get_missing_ingredients(self) -> list:
        """Get list of ingredients with insufficient quantity."""
        missing = []
        for req in self.recipe_requirements.select_related("ingredient"):
            if req.ingredient.quantity_available < req.quantity_required:
                missing.append(
                    {
                        "ingredient": req.ingredient,
                        "required": req.quantity_required,
                        "available": req.ingredient.quantity_available,
                        "shortage": req.quantity_required
                        - req.ingredient.quantity_available,
                    }
                )
        return missing

    def clean(self):
        """Validate model data."""
        from django.core.exceptions import ValidationError

        if self.price < 0:
            raise ValidationError({"price": "Price cannot be negative."})
        if self.cost < 0:
            raise ValidationError({"cost": "Cost cannot be negative."})

    def __str__(self) -> str:
        return self.name


class RecipeRequirement(models.Model):
    """
    Recipe requirement linking Dish to Ingredient with quantity needed.

    Defines the ingredients and quantities required to make a dish.

    Attributes:
        dish: Foreign key to Dish
        ingredient: Foreign key to Ingredient
        quantity_required: Amount of ingredient needed (in ingredient's unit)
    """

    dish: models.ForeignKey[Dish, Dish] = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name="recipe_requirements"
    )
    ingredient: models.ForeignKey[Ingredient, Ingredient] = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="recipe_requirements"
    )
    quantity_required: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantity needed (matches ingredient unit)",
    )

    class Meta:
        verbose_name = "Recipe Requirement"
        verbose_name_plural = "Recipe Requirements"
        unique_together = [["dish", "ingredient"]]
        ordering = ["dish", "ingredient"]

    def __str__(self) -> str:
        return (
            f"{self.dish.name} - {self.ingredient.name} "
            f"({self.quantity_required} {self.ingredient.unit.name})"
        )


class Menu(models.Model):
    """
    Menu as a composite item containing multiple Dishes.

    Represents a combo meal or set menu.

    Attributes:
        name: Menu name (e.g., 'Family Dinner')
        description: Optional description
        dishes: Many-to-many relation to Dish
        cost: Auto-calculated from dish costs
        price: Selling price
        is_available: True if all constituent dishes are available
    """

    name: models.CharField[str, str] = models.CharField(max_length=200)
    description: models.TextField[str, str] = models.TextField(blank=True)
    dishes: models.ManyToManyField[Dish, Dish] = models.ManyToManyField(
        Dish, related_name="menus"
    )
    cost: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Auto-calculated from dishes",
    )
    price: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Selling price"
    )
    is_available: models.BooleanField[bool, bool] = models.BooleanField(
        default=False, help_text="Available if all dishes are available"
    )

    class Meta:
        verbose_name = "Menu"
        verbose_name_plural = "Menus"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Purchase(models.Model):
    """
    Purchase order with user, timestamp, total price, and status.

    Represents a completed or cancelled order.

    Attributes:
        user: Foreign key to User who made the purchase
        timestamp: Auto-set creation time
        total_price_at_purchase: Total price frozen at purchase time
        status: 'completed' or 'cancelled'
        notes: Optional notes about the purchase
    """

    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user: models.ForeignKey[User, User] = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="purchases"
    )
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    total_price_at_purchase: models.DecimalField[Decimal, Decimal] = (
        models.DecimalField(max_digits=10, decimal_places=2, default=0)
    )
    status: models.CharField[str, str] = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_COMPLETED
    )
    notes: models.TextField[str, str] = models.TextField(blank=True)

    # Type hints for reverse relations
    if TYPE_CHECKING:
        items: RelatedManager[PurchaseItem]

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ["-timestamp"]

    STATUS_PENDING = "pending"

    @property
    def item_count(self) -> int:
        """Get total number of items in purchase."""
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    @property
    def is_completed(self) -> bool:
        """Check if purchase is completed."""
        return self.status == self.STATUS_COMPLETED

    @property
    def is_cancelled(self) -> bool:
        """Check if purchase is cancelled."""
        return self.status == self.STATUS_CANCELLED

    @property
    def total(self) -> Decimal:
        """Alias for total_price_at_purchase."""
        return self.total_price_at_purchase

    @total.setter
    def total(self, value: Decimal) -> None:
        """Set total_price_at_purchase."""
        self.total_price_at_purchase = value

    def calculate_total(self) -> Decimal:
        """Calculate total from items."""
        return self.items.aggregate(total=models.Sum("subtotal"))["total"] or Decimal(
            "0"
        )

    def __str__(self) -> str:
        return (
            f"Purchase #{self.id} by {self.user.username} "
            f"on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        )


class PurchaseItem(models.Model):
    """
    Individual item in a purchase with frozen price.

    Stores the price at purchase time to ensure historical accuracy.

    Attributes:
        purchase: Foreign key to Purchase
        dish: Foreign key to Dish that was purchased
        quantity: Number of units purchased
        price_at_purchase: Unit price frozen at purchase time
        subtotal: Auto-calculated: quantity * price_at_purchase
    """

    purchase: models.ForeignKey[Purchase, Purchase] = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name="items"
    )
    dish: models.ForeignKey[Dish, Dish] = models.ForeignKey(
        Dish, on_delete=models.PROTECT, related_name="purchase_items"
    )
    quantity: models.PositiveIntegerField[int, int] = models.PositiveIntegerField()
    price_at_purchase: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit at time of purchase",
    )
    subtotal: models.DecimalField[Decimal, Decimal] = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Auto-calculated: quantity * price_at_purchase",
    )

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"
        ordering = ["purchase", "dish"]

    def __str__(self) -> str:
        return (
            f"{self.quantity}x {self.dish.name} @ {self.price_at_purchase} "
            f"(Purchase #{self.purchase.id})"
        )
