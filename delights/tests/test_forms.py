"""
Tests for Django Delights forms.

Tests cover form validation, field constraints, and custom clean methods.
"""

from decimal import Decimal

import pytest

from delights.forms import (
    DishForm,
    IngredientForm,
    InventoryAdjustmentForm,
    MenuForm,
    PurchaseCreateForm,
    RecipeRequirementForm,
    UnitForm,
)
from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    UnitFactory,
)


class TestUnitForm:
    """Tests for UnitForm."""

    def test_valid_data(self, db):
        form = UnitForm(data={"name": "kg", "description": "kilogram", "is_active": True})
        assert form.is_valid()

    def test_missing_name(self, db):
        form = UnitForm(data={"name": "", "description": "kilogram", "is_active": True})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_missing_description(self, db):
        form = UnitForm(data={"name": "kg", "description": "", "is_active": True})
        assert not form.is_valid()
        assert "description" in form.errors


class TestIngredientForm:
    """Tests for IngredientForm."""

    def test_valid_data(self, db):
        unit = UnitFactory(is_active=True)
        form = IngredientForm(
            data={"name": "Flour", "unit": unit.id, "price_per_unit": "0.50"}
        )
        assert form.is_valid()

    def test_only_active_units_shown(self, db):
        active = UnitFactory(is_active=True, name="active")
        inactive = UnitFactory(is_active=False, name="inactive")
        form = IngredientForm()
        unit_qs = form.fields["unit"].queryset
        assert active in unit_qs
        assert inactive not in unit_qs

    def test_missing_unit(self, db):
        form = IngredientForm(data={"name": "Flour", "price_per_unit": "0.50"})
        assert not form.is_valid()
        assert "unit" in form.errors

    def test_missing_price(self, db):
        unit = UnitFactory(is_active=True)
        form = IngredientForm(data={"name": "Flour", "unit": unit.id})
        assert not form.is_valid()
        assert "price_per_unit" in form.errors


class TestDishForm:
    """Tests for DishForm."""

    def test_valid_data(self, db):
        form = DishForm(
            data={"name": "Pizza", "description": "Delicious", "price": "10.00"}
        )
        assert form.is_valid()

    def test_missing_name(self, db):
        form = DishForm(data={"name": "", "description": "Delicious", "price": "10.00"})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_missing_price(self, db):
        form = DishForm(data={"name": "Pizza", "description": "Delicious"})
        assert not form.is_valid()
        assert "price" in form.errors

    def test_blank_description_allowed(self, db):
        form = DishForm(data={"name": "Pizza", "description": "", "price": "10.00"})
        assert form.is_valid()


class TestRecipeRequirementForm:
    """Tests for RecipeRequirementForm."""

    def test_valid_data(self, db):
        ingredient = IngredientFactory()
        form = RecipeRequirementForm(
            data={"ingredient": ingredient.id, "quantity_required": "10.00"}
        )
        assert form.is_valid()

    def test_missing_ingredient(self, db):
        form = RecipeRequirementForm(data={"quantity_required": "10.00"})
        assert not form.is_valid()
        assert "ingredient" in form.errors

    def test_missing_quantity(self, db):
        ingredient = IngredientFactory()
        form = RecipeRequirementForm(data={"ingredient": ingredient.id})
        assert not form.is_valid()
        assert "quantity_required" in form.errors


class TestInventoryAdjustmentForm:
    """Tests for InventoryAdjustmentForm."""

    def test_valid_positive_adjustment(self, db):
        form = InventoryAdjustmentForm(data={"adjustment": "50.00"})
        assert form.is_valid()

    def test_valid_negative_adjustment(self, db):
        form = InventoryAdjustmentForm(data={"adjustment": "-25.00"})
        assert form.is_valid()

    def test_missing_adjustment(self, db):
        form = InventoryAdjustmentForm(data={})
        assert not form.is_valid()
        assert "adjustment" in form.errors

    def test_zero_adjustment(self, db):
        form = InventoryAdjustmentForm(data={"adjustment": "0.00"})
        assert form.is_valid()


class TestMenuForm:
    """Tests for MenuForm."""

    def test_valid_data(self, db):
        form = MenuForm(
            data={"name": "Lunch", "description": "Lunch special", "price": "15.00"}
        )
        assert form.is_valid()

    def test_missing_name(self, db):
        form = MenuForm(data={"name": "", "description": "Lunch", "price": "15.00"})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_missing_price(self, db):
        form = MenuForm(data={"name": "Lunch", "description": "Special"})
        assert not form.is_valid()
        assert "price" in form.errors


class TestPurchaseCreateForm:
    """Tests for PurchaseCreateForm."""

    def test_form_creates_fields_for_available_dishes(self, db):
        dish1 = DishFactory(is_available=True)
        dish2 = DishFactory(is_available=False)
        form = PurchaseCreateForm()
        assert f"dish_{dish1.pk}" in form.fields
        assert f"dish_{dish2.pk}" not in form.fields

    def test_valid_selection(self, db):
        dish = DishFactory(is_available=True)
        form = PurchaseCreateForm(data={f"dish_{dish.pk}": 2})
        assert form.is_valid()

    def test_no_selection_invalid(self, db):
        DishFactory(is_available=True)
        form = PurchaseCreateForm(data={})
        assert not form.is_valid()

    def test_zero_quantity_treated_as_no_selection(self, db):
        dish = DishFactory(is_available=True)
        form = PurchaseCreateForm(data={f"dish_{dish.pk}": 0})
        assert not form.is_valid()
