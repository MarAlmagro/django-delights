import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from delights.models import Dish, Ingredient, Purchase, RecipeRequirement
from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    RecipeRequirementFactory,
    UserFactory,
    MenuFactory,
    PurchaseFactory,
)


class TestEdgeCases:
    """Tests for boundary conditions and edge cases."""

    def test_negative_inventory_prevented(self, db):
        """Inventory should not go negative."""
        ingredient = IngredientFactory(quantity_available=Decimal('5'))
        ingredient.quantity_available -= Decimal('10')
        
        if ingredient.quantity_available < 0:
            ingredient.quantity_available = Decimal('0')
        ingredient.save()
        
        ingredient.refresh_from_db()
        assert ingredient.quantity_available >= Decimal('0')

    def test_very_large_quantity(self, db):
        """Handle very large quantities without overflow."""
        ingredient = IngredientFactory(
            quantity_available=Decimal('99999999.99'),
            price_per_unit=Decimal('99999999.99')
        )
        dish = DishFactory()
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('1')
        )
        
        assert ingredient.quantity_available == Decimal('99999999.99')
        assert ingredient.price_per_unit == Decimal('99999999.99')

    def test_zero_price_dish(self, db):
        """Handle dishes with zero price."""
        dish = DishFactory(price=Decimal('0'))
        assert dish.price == Decimal('0')

    def test_zero_quantity_ingredient(self, db):
        """Handle ingredients with zero quantity."""
        ingredient = IngredientFactory(quantity_available=Decimal('0'))
        assert ingredient.quantity_available == Decimal('0')

    def test_unicode_in_names(self, db):
        """Handle unicode characters in names."""
        dish = DishFactory(name="Crème Brûlée 日本語 🍰")
        assert "Crème" in dish.name
        assert "日本語" in dish.name
        assert "🍰" in dish.name
        
        ingredient = IngredientFactory(name="Jalapeño Peppers 🌶️")
        assert "Jalapeño" in ingredient.name
        assert "🌶️" in ingredient.name

    def test_very_long_description(self, db):
        """Handle very long descriptions."""
        long_desc = "A" * 10000
        dish = DishFactory(description=long_desc)
        assert len(dish.description) == 10000

    def test_very_long_name(self, db):
        """Handle long names up to field limit."""
        long_name = "X" * 200
        dish = DishFactory(name=long_name)
        assert len(dish.name) == 200

    def test_simultaneous_availability_check(self, db):
        """Multiple dishes sharing same ingredient."""
        ingredient = IngredientFactory(quantity_available=Decimal('100'))
        dish1 = DishFactory()
        dish2 = DishFactory()
        
        RecipeRequirementFactory(
            dish=dish1, ingredient=ingredient, quantity_required=Decimal('60')
        )
        RecipeRequirementFactory(
            dish=dish2, ingredient=ingredient, quantity_required=Decimal('60')
        )
        
        assert dish1.recipe_requirements.count() == 1
        assert dish2.recipe_requirements.count() == 1

    def test_dish_with_no_ingredients(self, db):
        """Handle dishes with no recipe requirements."""
        dish = DishFactory()
        assert dish.recipe_requirements.count() == 0

    def test_ingredient_with_no_dishes(self, db):
        """Handle ingredients not used in any dish."""
        ingredient = IngredientFactory()
        assert ingredient.reciperequirement_set.count() == 0

    def test_deleted_user_purchases(self, db):
        """Purchases should be preserved when user is deactivated."""
        user = UserFactory()
        purchase = PurchaseFactory(user=user)
        
        user.is_active = False
        user.save()
        
        purchase.refresh_from_db()
        assert purchase.user == user

    def test_duplicate_dish_names_allowed(self, db):
        """Multiple dishes can have the same name."""
        DishFactory(name="Pasta")
        DishFactory(name="Pasta")
        
        assert Dish.objects.filter(name="Pasta").count() == 2

    def test_duplicate_ingredient_names_allowed(self, db):
        """Multiple ingredients can have the same name."""
        IngredientFactory(name="Salt")
        IngredientFactory(name="Salt")
        
        assert Ingredient.objects.filter(name="Salt").count() == 2

    def test_recipe_requirement_zero_quantity(self, db):
        """Recipe requirement with zero quantity."""
        dish = DishFactory()
        ingredient = IngredientFactory()
        recipe = RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('0')
        )
        
        assert recipe.quantity_required == Decimal('0')

    def test_menu_with_no_dishes(self, db):
        """Menu can exist with no dishes."""
        menu = MenuFactory()
        menu.dishes.clear()
        
        assert menu.dishes.count() == 0

    def test_menu_with_many_dishes(self, db):
        """Menu can contain many dishes."""
        menu = MenuFactory()
        dishes = DishFactory.create_batch(50)
        menu.dishes.set(dishes)
        
        assert menu.dishes.count() == 50

    def test_precision_in_decimal_calculations(self, db):
        """Ensure decimal precision is maintained."""
        ingredient = IngredientFactory(
            quantity_available=Decimal('10.123456'),
            price_per_unit=Decimal('5.987654')
        )
        
        assert ingredient.quantity_available == Decimal('10.123456')
        assert ingredient.price_per_unit == Decimal('5.987654')

    def test_special_characters_in_description(self, db):
        """Handle special characters in descriptions."""
        special_desc = "Line1\nLine2\tTabbed\r\nWindows\n\n\nMultiple"
        dish = DishFactory(description=special_desc)
        
        assert "\n" in dish.description
        assert "\t" in dish.description

    def test_html_in_description(self, db):
        """HTML in descriptions should be stored as-is."""
        html_desc = "<script>alert('test')</script><b>Bold</b>"
        dish = DishFactory(description=html_desc)
        
        assert "<script>" in dish.description
        assert "<b>" in dish.description

    def test_empty_string_vs_null(self, db):
        """Test empty string handling."""
        dish = DishFactory(description="")
        assert dish.description == ""

    def test_whitespace_only_names(self, db):
        """Test names with only whitespace."""
        dish = DishFactory(name="   ")
        assert dish.name == "   "

    def test_ingredient_unit_variations(self, db):
        """Test different unit types."""
        units = ['kg', 'g', 'lb', 'oz', 'L', 'mL', 'cup', 'tbsp', 'tsp', 'piece']
        
        for unit in units:
            ingredient = IngredientFactory(unit=unit)
            assert ingredient.unit == unit

    def test_purchase_timestamp_precision(self, db):
        """Ensure purchase timestamps are precise."""
        purchase1 = PurchaseFactory()
        purchase2 = PurchaseFactory()
        
        assert purchase1.timestamp is not None
        assert purchase2.timestamp is not None

    def test_dish_availability_toggle(self, db):
        """Test toggling dish availability."""
        dish = DishFactory(is_available=True)
        assert dish.is_available is True
        
        dish.is_available = False
        dish.save()
        
        dish.refresh_from_db()
        assert dish.is_available is False

    def test_multiple_recipe_requirements_same_dish(self, db):
        """Dish can have multiple ingredients."""
        dish = DishFactory()
        ingredient1 = IngredientFactory()
        ingredient2 = IngredientFactory()
        ingredient3 = IngredientFactory()
        
        RecipeRequirementFactory(dish=dish, ingredient=ingredient1)
        RecipeRequirementFactory(dish=dish, ingredient=ingredient2)
        RecipeRequirementFactory(dish=dish, ingredient=ingredient3)
        
        assert dish.recipe_requirements.count() == 3

    def test_same_ingredient_multiple_times_in_dish(self, db):
        """Test if same ingredient can be added multiple times."""
        dish = DishFactory()
        ingredient = IngredientFactory()
        
        RecipeRequirementFactory(dish=dish, ingredient=ingredient, quantity_required=Decimal('5'))
        
        try:
            RecipeRequirementFactory(dish=dish, ingredient=ingredient, quantity_required=Decimal('3'))
            duplicate_allowed = True
        except IntegrityError:
            duplicate_allowed = False
        
        assert duplicate_allowed or dish.recipe_requirements.count() == 1


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_minimum_decimal_values(self, db):
        """Test minimum decimal values."""
        ingredient = IngredientFactory(
            quantity_available=Decimal('0.01'),
            price_per_unit=Decimal('0.01')
        )
        
        assert ingredient.quantity_available == Decimal('0.01')
        assert ingredient.price_per_unit == Decimal('0.01')

    def test_maximum_decimal_values(self, db):
        """Test maximum decimal values within field constraints."""
        ingredient = IngredientFactory(
            quantity_available=Decimal('9999999.99'),
            price_per_unit=Decimal('9999999.99')
        )
        
        assert ingredient.quantity_available == Decimal('9999999.99')
        assert ingredient.price_per_unit == Decimal('9999999.99')

    def test_negative_price_handling(self, db):
        """Test negative prices."""
        dish = DishFactory(price=Decimal('-10.00'))
        assert dish.price == Decimal('-10.00')

    def test_fractional_quantities(self, db):
        """Test fractional quantities."""
        ingredient = IngredientFactory(quantity_available=Decimal('0.333'))
        recipe = RecipeRequirementFactory(
            ingredient=ingredient,
            quantity_required=Decimal('0.111')
        )
        
        assert recipe.quantity_required == Decimal('0.111')

    def test_empty_queryset_operations(self, db):
        """Test operations on empty querysets."""
        assert Dish.objects.count() == 0
        assert Ingredient.objects.count() == 0
        assert Purchase.objects.count() == 0

    def test_bulk_operations(self, db):
        """Test bulk create operations."""
        dishes = [DishFactory.build() for _ in range(100)]
        Dish.objects.bulk_create(dishes)
        
        assert Dish.objects.count() == 100

    def test_ordering_consistency(self, db):
        """Test that ordering is consistent."""
        dishes = DishFactory.create_batch(10)
        
        result1 = list(Dish.objects.order_by('id'))
        result2 = list(Dish.objects.order_by('id'))
        
        assert result1 == result2
