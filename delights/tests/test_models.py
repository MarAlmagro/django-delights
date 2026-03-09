"""
Unit tests for Django Delights models.

Tests model creation, validation, string representations,
and model relationships.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError

from delights.models import (
    Dish,
    Ingredient,
    Menu,
    Purchase,
    PurchaseItem,
    RecipeRequirement,
    Unit,
)
from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    MenuFactory,
    PurchaseFactory,
    PurchaseItemFactory,
    RecipeRequirementFactory,
    UnitFactory,
    UserFactory,
)


class TestUnitModel:
    """Tests for the Unit model."""

    def test_unit_creation(self, db):
        """Test creating a unit with valid data."""
        unit = UnitFactory(name="kg", description="kilogram")
        assert unit.name == "kg"
        assert unit.description == "kilogram"
        assert unit.is_active is True

    def test_unit_str_representation(self, db):
        """Test unit string representation."""
        unit = UnitFactory(name="g", description="gram")
        assert str(unit) == "g"

    def test_unit_unique_name(self, db):
        """Test that unit names must be unique."""
        Unit.objects.create(name="unique_unit", description="first")
        with pytest.raises(IntegrityError):
            Unit.objects.create(name="unique_unit", description="second")

    def test_unit_inactive(self, db):
        """Test creating an inactive unit."""
        unit = UnitFactory(is_active=False)
        assert unit.is_active is False

    def test_unit_ordering(self, db):
        """Test that units are ordered by name."""
        UnitFactory(name="z_unit")
        UnitFactory(name="a_unit")
        UnitFactory(name="m_unit")
        units = list(Unit.objects.all())
        assert units[0].name == "a_unit"
        assert units[1].name == "m_unit"
        assert units[2].name == "z_unit"


class TestIngredientModel:
    """Tests for the Ingredient model."""

    def test_ingredient_creation(self, db, unit_gram):
        """Test creating an ingredient with valid data."""
        ingredient = IngredientFactory(
            name="Flour",
            unit=unit_gram,
            price_per_unit=Decimal("0.50"),
            quantity_available=Decimal("1000.00"),
        )
        assert ingredient.name == "Flour"
        assert ingredient.unit == unit_gram
        assert ingredient.price_per_unit == Decimal("0.50")
        assert ingredient.quantity_available == Decimal("1000.00")

    def test_ingredient_str_representation(self, db, unit_gram):
        """Test ingredient string representation."""
        ingredient = IngredientFactory(
            name="Sugar",
            unit=unit_gram,
            quantity_available=Decimal("500.00"),
        )
        assert str(ingredient) == "Sugar (500.00 g)"

    def test_ingredient_default_quantity(self, db):
        """Test that default quantity is 0."""
        ingredient = Ingredient.objects.create(
            name="Test",
            unit=UnitFactory(),
            price_per_unit=Decimal("1.00"),
        )
        assert ingredient.quantity_available == Decimal("0")

    def test_ingredient_unit_protection(self, db):
        """Test that deleting a unit with ingredients raises error."""
        unit = UnitFactory()
        IngredientFactory(unit=unit)
        with pytest.raises(Exception):  # ProtectedError
            unit.delete()

    def test_ingredient_ordering(self, db):
        """Test that ingredients are ordered by name."""
        IngredientFactory(name="Zucchini")
        IngredientFactory(name="Apple")
        IngredientFactory(name="Milk")
        ingredients = list(Ingredient.objects.all())
        assert ingredients[0].name == "Apple"
        assert ingredients[1].name == "Milk"
        assert ingredients[2].name == "Zucchini"


class TestDishModel:
    """Tests for the Dish model."""

    def test_dish_creation(self, db):
        """Test creating a dish with valid data."""
        dish = DishFactory(
            name="Pizza",
            description="Delicious pizza",
            cost=Decimal("5.00"),
            price=Decimal("10.00"),
            is_available=True,
        )
        assert dish.name == "Pizza"
        assert dish.description == "Delicious pizza"
        assert dish.cost == Decimal("5.00")
        assert dish.price == Decimal("10.00")
        assert dish.is_available is True

    def test_dish_str_representation(self, db):
        """Test dish string representation."""
        dish = DishFactory(name="Pasta")
        assert str(dish) == "Pasta"

    def test_dish_default_values(self, db):
        """Test dish default values."""
        dish = Dish.objects.create(
            name="Test Dish",
            price=Decimal("10.00"),
        )
        assert dish.description == ""
        assert dish.cost == Decimal("0")
        assert dish.is_available is False

    def test_dish_ordering(self, db):
        """Test that dishes are ordered by name."""
        DishFactory(name="Zebra Cake")
        DishFactory(name="Apple Pie")
        DishFactory(name="Muffin")
        dishes = list(Dish.objects.all())
        assert dishes[0].name == "Apple Pie"
        assert dishes[1].name == "Muffin"
        assert dishes[2].name == "Zebra Cake"


class TestRecipeRequirementModel:
    """Tests for the RecipeRequirement model."""

    def test_recipe_requirement_creation(self, db):
        """Test creating a recipe requirement."""
        dish = DishFactory()
        ingredient = IngredientFactory()
        requirement = RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal("100.00"),
        )
        assert requirement.dish == dish
        assert requirement.ingredient == ingredient
        assert requirement.quantity_required == Decimal("100.00")

    def test_recipe_requirement_str_representation(self, db):
        """Test recipe requirement string representation."""
        unit = UnitFactory(name="g")
        ingredient = IngredientFactory(name="Flour", unit=unit)
        dish = DishFactory(name="Bread")
        requirement = RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal("500.00"),
        )
        assert str(requirement) == "Bread - Flour (500.00 g)"

    def test_recipe_requirement_unique_together(self, db):
        """Test that dish-ingredient combination is unique."""
        dish = DishFactory()
        ingredient = IngredientFactory()
        RecipeRequirementFactory(dish=dish, ingredient=ingredient)
        with pytest.raises(IntegrityError):
            RecipeRequirementFactory(dish=dish, ingredient=ingredient)

    def test_recipe_requirement_cascade_delete_dish(self, db):
        """Test that requirements are deleted when dish is deleted."""
        dish = DishFactory()
        RecipeRequirementFactory(dish=dish)
        RecipeRequirementFactory(dish=dish)
        dish_id = dish.pk
        assert RecipeRequirement.objects.filter(dish_id=dish_id).count() == 2
        dish.delete()
        assert RecipeRequirement.objects.filter(dish_id=dish_id).count() == 0

    def test_recipe_requirement_cascade_delete_ingredient(self, db):
        """Test that requirements are deleted when ingredient is deleted."""
        ingredient = IngredientFactory()
        RecipeRequirementFactory(ingredient=ingredient)
        RecipeRequirementFactory(ingredient=ingredient)
        ingredient_id = ingredient.pk
        assert (
            RecipeRequirement.objects.filter(ingredient_id=ingredient_id).count() == 2
        )
        ingredient.delete()
        assert (
            RecipeRequirement.objects.filter(ingredient_id=ingredient_id).count() == 0
        )


class TestMenuModel:
    """Tests for the Menu model."""

    def test_menu_creation(self, db):
        """Test creating a menu with valid data."""
        menu = MenuFactory(
            name="Lunch Special",
            description="Great lunch deal",
            cost=Decimal("10.00"),
            price=Decimal("15.00"),
            is_available=True,
        )
        assert menu.name == "Lunch Special"
        assert menu.description == "Great lunch deal"
        assert menu.cost == Decimal("10.00")
        assert menu.price == Decimal("15.00")
        assert menu.is_available is True

    def test_menu_str_representation(self, db):
        """Test menu string representation."""
        menu = MenuFactory(name="Dinner Combo")
        assert str(menu) == "Dinner Combo"

    def test_menu_with_dishes(self, db):
        """Test adding dishes to a menu."""
        dish1 = DishFactory(name="Appetizer")
        dish2 = DishFactory(name="Main Course")
        menu = MenuFactory(dishes=[dish1, dish2])
        assert menu.dishes.count() == 2
        assert dish1 in menu.dishes.all()
        assert dish2 in menu.dishes.all()

    def test_menu_dish_relationship(self, db):
        """Test the reverse relationship from dish to menus."""
        dish = DishFactory()
        menu1 = MenuFactory(dishes=[dish])
        menu2 = MenuFactory(dishes=[dish])
        assert dish.menus.count() == 2
        assert menu1 in dish.menus.all()
        assert menu2 in dish.menus.all()

    def test_menu_ordering(self, db):
        """Test that menus are ordered by name."""
        MenuFactory(name="Z Menu")
        MenuFactory(name="A Menu")
        MenuFactory(name="M Menu")
        menus = list(Menu.objects.all())
        assert menus[0].name == "A Menu"
        assert menus[1].name == "M Menu"
        assert menus[2].name == "Z Menu"


class TestPurchaseModel:
    """Tests for the Purchase model."""

    def test_purchase_creation(self, db):
        """Test creating a purchase with valid data."""
        user = UserFactory()
        purchase = PurchaseFactory(
            user=user,
            total_price_at_purchase=Decimal("25.00"),
            status=Purchase.STATUS_COMPLETED,
            notes="Test purchase",
        )
        assert purchase.user == user
        assert purchase.total_price_at_purchase == Decimal("25.00")
        assert purchase.status == Purchase.STATUS_COMPLETED
        assert purchase.notes == "Test purchase"
        assert purchase.timestamp is not None

    def test_purchase_str_representation(self, db):
        """Test purchase string representation."""
        user = UserFactory(username="testuser")
        purchase = PurchaseFactory(user=user)
        expected = f"Purchase #{purchase.id} by testuser on {purchase.timestamp.strftime('%Y-%m-%d %H:%M')}"
        assert str(purchase) == expected

    def test_purchase_status_choices(self, db):
        """Test purchase status choices."""
        user = UserFactory()
        completed = PurchaseFactory(user=user, status=Purchase.STATUS_COMPLETED)
        cancelled = PurchaseFactory(user=user, status=Purchase.STATUS_CANCELLED)
        assert completed.status == "completed"
        assert cancelled.status == "cancelled"

    def test_purchase_user_protection(self, db):
        """Test that deleting a user with purchases raises error."""
        user = UserFactory()
        PurchaseFactory(user=user)
        with pytest.raises(Exception):  # ProtectedError
            user.delete()

    def test_purchase_ordering(self, db):
        """Test that purchases are ordered by timestamp descending."""
        user = UserFactory()
        purchase1 = PurchaseFactory(user=user)
        purchase2 = PurchaseFactory(user=user)
        purchase3 = PurchaseFactory(user=user)
        purchases = list(Purchase.objects.all())
        # Most recent first
        assert purchases[0] == purchase3
        assert purchases[1] == purchase2
        assert purchases[2] == purchase1


class TestPurchaseItemModel:
    """Tests for the PurchaseItem model."""

    def test_purchase_item_creation(self, db):
        """Test creating a purchase item with valid data."""
        purchase = PurchaseFactory()
        dish = DishFactory()
        item = PurchaseItemFactory(
            purchase=purchase,
            dish=dish,
            quantity=2,
            price_at_purchase=Decimal("10.00"),
            subtotal=Decimal("20.00"),
        )
        assert item.purchase == purchase
        assert item.dish == dish
        assert item.quantity == 2
        assert item.price_at_purchase == Decimal("10.00")
        assert item.subtotal == Decimal("20.00")

    def test_purchase_item_str_representation(self, db):
        """Test purchase item string representation."""
        purchase = PurchaseFactory()
        dish = DishFactory(name="Burger")
        item = PurchaseItemFactory(
            purchase=purchase,
            dish=dish,
            quantity=3,
            price_at_purchase=Decimal("8.50"),
        )
        expected = f"3x Burger @ 8.50 (Purchase #{purchase.id})"
        assert str(item) == expected

    def test_purchase_item_cascade_delete(self, db):
        """Test that items are deleted when purchase is deleted."""
        purchase = PurchaseFactory()
        PurchaseItemFactory(purchase=purchase)
        PurchaseItemFactory(purchase=purchase)
        purchase_id = purchase.pk
        assert PurchaseItem.objects.filter(purchase_id=purchase_id).count() == 2
        purchase.delete()
        assert PurchaseItem.objects.filter(purchase_id=purchase_id).count() == 0

    def test_purchase_item_dish_protection(self, db):
        """Test that deleting a dish with purchase items raises error."""
        dish = DishFactory()
        PurchaseItemFactory(dish=dish)
        with pytest.raises(Exception):  # ProtectedError
            dish.delete()

    def test_purchase_items_relationship(self, db):
        """Test the reverse relationship from purchase to items."""
        purchase = PurchaseFactory()
        item1 = PurchaseItemFactory(purchase=purchase)
        item2 = PurchaseItemFactory(purchase=purchase)
        assert purchase.items.count() == 2
        assert item1 in purchase.items.all()
        assert item2 in purchase.items.all()
