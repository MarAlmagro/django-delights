"""
Tests for service layer functions.
"""
import pytest
from decimal import Decimal
from django.conf import settings

from delights.models import Unit, Ingredient, Dish, RecipeRequirement, Menu
from delights.services.pricing import (
    calculate_dish_cost,
    calculate_menu_cost,
    calculate_suggested_price,
    get_global_margin,
)
from delights.services.availability import (
    check_dish_availability,
    check_menu_availability,
    update_dish_availability,
    update_dishes_for_ingredient,
    update_menu_availability,
    update_menus_for_dish,
)
from delights.services.inventory import (
    adjust_ingredient_quantity,
    check_low_stock_ingredients,
    get_inventory_value,
)


@pytest.mark.django_db
class TestPricingService:
    """Test pricing service functions."""

    def test_get_global_margin(self):
        """Test getting global margin from settings."""
        margin = get_global_margin()
        assert margin == Decimal('0.20')
        assert isinstance(margin, Decimal)

    def test_calculate_dish_cost(self, dish_with_requirements):
        """Test calculating dish cost from recipe requirements."""
        cost = calculate_dish_cost(dish_with_requirements)
        assert cost > 0
        assert isinstance(cost, Decimal)

    def test_calculate_suggested_price(self):
        """Test calculating suggested price with margin."""
        cost = Decimal('10.00')
        price = calculate_suggested_price(cost)
        expected = cost * Decimal('1.20')  # 20% margin
        assert price == expected

    def test_calculate_suggested_price_custom_margin(self):
        """Test calculating suggested price with custom margin."""
        cost = Decimal('10.00')
        margin = Decimal('0.30')  # 30% margin
        price = calculate_suggested_price(cost, margin)
        expected = cost * Decimal('1.30')
        assert price == expected

    def test_calculate_menu_cost(self, menu_with_dishes):
        """Test calculating menu cost from dishes."""
        cost = calculate_menu_cost(menu_with_dishes)
        assert cost > 0
        assert isinstance(cost, Decimal)


@pytest.mark.django_db
class TestAvailabilityService:
    """Test availability service functions."""

    def test_check_dish_availability_true(self, dish_with_requirements):
        """Test checking dish availability when ingredients are sufficient."""
        available = check_dish_availability(dish_with_requirements)
        assert available is True

    def test_check_dish_availability_false_no_requirements(self, dish):
        """Test checking dish availability when no requirements exist."""
        available = check_dish_availability(dish)
        assert available is False

    def test_check_dish_availability_false_insufficient_stock(
        self, dish_with_requirements, ingredient
    ):
        """Test checking dish availability when stock is insufficient."""
        ingredient.quantity_available = Decimal('0')
        ingredient.save()
        available = check_dish_availability(dish_with_requirements)
        assert available is False

    def test_update_dish_availability(self, dish_with_requirements):
        """Test updating dish cost and availability."""
        dish_with_requirements.cost = Decimal('0')
        dish_with_requirements.is_available = False
        dish_with_requirements.save()

        update_dish_availability(dish_with_requirements)
        dish_with_requirements.refresh_from_db()

        assert dish_with_requirements.cost > 0
        assert dish_with_requirements.is_available is True

    def test_update_dishes_for_ingredient(self, dish_with_requirements, ingredient):
        """Test updating all dishes when ingredient changes."""
        dish_with_requirements.cost = Decimal('0')
        dish_with_requirements.save()

        update_dishes_for_ingredient(ingredient)
        dish_with_requirements.refresh_from_db()

        assert dish_with_requirements.cost > 0

    def test_check_menu_availability_true(self, menu_with_dishes):
        """Test checking menu availability when all dishes are available."""
        available = check_menu_availability(menu_with_dishes)
        assert available is True

    def test_check_menu_availability_false_no_dishes(self, menu):
        """Test checking menu availability when no dishes exist."""
        available = check_menu_availability(menu)
        assert available is False

    def test_update_menu_availability(self, menu_with_dishes):
        """Test updating menu cost and availability."""
        menu_with_dishes.cost = Decimal('0')
        menu_with_dishes.is_available = False
        menu_with_dishes.save()

        update_menu_availability(menu_with_dishes)
        menu_with_dishes.refresh_from_db()

        assert menu_with_dishes.cost > 0
        assert menu_with_dishes.is_available is True


@pytest.mark.django_db
class TestInventoryService:
    """Test inventory service functions."""

    def test_adjust_ingredient_quantity_positive(self, ingredient):
        """Test adjusting ingredient quantity with positive amount."""
        original = ingredient.quantity_available
        adjust_ingredient_quantity(ingredient, Decimal('10'))
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == original + Decimal('10')

    def test_adjust_ingredient_quantity_negative(self, ingredient):
        """Test adjusting ingredient quantity with negative amount."""
        original = ingredient.quantity_available
        adjust_ingredient_quantity(ingredient, Decimal('-5'))
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == original - Decimal('5')

    def test_adjust_ingredient_quantity_floor_at_zero(self, ingredient):
        """Test that quantity cannot go below zero."""
        adjust_ingredient_quantity(ingredient, Decimal('-1000'))
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal('0')

    def test_check_low_stock_ingredients(self, ingredient):
        """Test checking for low stock ingredients."""
        ingredient.quantity_available = Decimal('5')
        ingredient.save()

        low_stock = check_low_stock_ingredients()
        assert ingredient in low_stock

    def test_get_inventory_value(self, ingredient):
        """Test calculating total inventory value."""
        result = get_inventory_value()
        assert 'total_value' in result
        assert 'total_count' in result
        assert result['total_value'] > 0
