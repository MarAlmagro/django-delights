"""
Tests for enhanced model methods and properties.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from delights.models import Dish, Ingredient, Purchase


@pytest.mark.django_db
class TestIngredientEnhancements:
    """Test enhanced Ingredient model methods."""

    def test_is_low_stock_true(self, ingredient):
        """Test is_low_stock property when stock is low."""
        ingredient.quantity_available = Decimal('5')
        ingredient.save()
        assert ingredient.is_low_stock is True

    def test_is_low_stock_false(self, ingredient):
        """Test is_low_stock property when stock is sufficient."""
        ingredient.quantity_available = Decimal('100')
        ingredient.save()
        assert ingredient.is_low_stock is False

    def test_total_value(self, ingredient):
        """Test total_value property calculation."""
        ingredient.price_per_unit = Decimal('2.50')
        ingredient.quantity_available = Decimal('10')
        ingredient.save()
        assert ingredient.total_value == Decimal('25.00')

    def test_adjust_quantity(self, ingredient):
        """Test adjust_quantity method."""
        original = ingredient.quantity_available
        ingredient.adjust_quantity(Decimal('10'))
        assert ingredient.quantity_available == original + Decimal('10')

    def test_clean_negative_price(self, ingredient):
        """Test clean method rejects negative price."""
        ingredient.price_per_unit = Decimal('-1')
        with pytest.raises(ValidationError):
            ingredient.clean()

    def test_clean_negative_quantity(self, ingredient):
        """Test clean method rejects negative quantity."""
        ingredient.quantity_available = Decimal('-1')
        with pytest.raises(ValidationError):
            ingredient.clean()


@pytest.mark.django_db
class TestDishEnhancements:
    """Test enhanced Dish model methods."""

    def test_calculated_cost(self, dish_with_requirements):
        """Test calculated_cost property."""
        cost = dish_with_requirements.calculated_cost
        assert cost > 0
        assert isinstance(cost, Decimal)

    def test_profit_margin(self, dish_with_requirements):
        """Test profit_margin property calculation."""
        dish_with_requirements.cost = Decimal('10')
        dish_with_requirements.price = Decimal('12')
        dish_with_requirements.save()
        margin = dish_with_requirements.profit_margin
        assert margin == Decimal('20')  # 20% margin

    def test_profit_margin_zero_cost(self, dish):
        """Test profit_margin when cost is zero."""
        dish.cost = Decimal('0')
        dish.price = Decimal('10')
        dish.save()
        assert dish.profit_margin == Decimal('0')

    def test_is_profitable_true(self, dish):
        """Test is_profitable when price > cost."""
        dish.cost = Decimal('10')
        dish.price = Decimal('15')
        dish.save()
        assert dish.is_profitable is True

    def test_is_profitable_false(self, dish):
        """Test is_profitable when price <= cost."""
        dish.cost = Decimal('10')
        dish.price = Decimal('10')
        dish.save()
        assert dish.is_profitable is False

    def test_can_make(self, dish_with_requirements):
        """Test can_make method with sufficient ingredients."""
        assert dish_with_requirements.can_make(1) is True

    def test_can_make_insufficient(self, dish_with_requirements, ingredient):
        """Test can_make method with insufficient ingredients."""
        ingredient.quantity_available = Decimal('0')
        ingredient.save()
        assert dish_with_requirements.can_make(1) is False

    def test_get_missing_ingredients(self, dish_with_requirements, ingredient):
        """Test get_missing_ingredients method."""
        ingredient.quantity_available = Decimal('0')
        ingredient.save()
        missing = dish_with_requirements.get_missing_ingredients()
        assert len(missing) > 0
        assert missing[0]['ingredient'] == ingredient

    def test_clean_negative_price(self, dish):
        """Test clean method rejects negative price."""
        dish.price = Decimal('-1')
        with pytest.raises(ValidationError):
            dish.clean()

    def test_clean_negative_cost(self, dish):
        """Test clean method rejects negative cost."""
        dish.cost = Decimal('-1')
        with pytest.raises(ValidationError):
            dish.clean()


@pytest.mark.django_db
class TestPurchaseEnhancements:
    """Test enhanced Purchase model methods."""

    def test_item_count(self, purchase_with_items):
        """Test item_count property."""
        count = purchase_with_items.item_count
        assert count > 0

    def test_is_completed(self, purchase):
        """Test is_completed property."""
        purchase.status = Purchase.STATUS_COMPLETED
        purchase.save()
        assert purchase.is_completed is True

    def test_is_cancelled(self, purchase):
        """Test is_cancelled property."""
        purchase.status = Purchase.STATUS_CANCELLED
        purchase.save()
        assert purchase.is_cancelled is True

    def test_total_property(self, purchase):
        """Test total property getter."""
        purchase.total_price_at_purchase = Decimal('100')
        purchase.save()
        assert purchase.total == Decimal('100')

    def test_total_property_setter(self, purchase):
        """Test total property setter."""
        purchase.total = Decimal('150')
        assert purchase.total_price_at_purchase == Decimal('150')

    def test_calculate_total(self, purchase_with_items):
        """Test calculate_total method."""
        total = purchase_with_items.calculate_total()
        assert total > 0
        assert isinstance(total, Decimal)
