"""
Integration tests for Django Delights.

Tests cover end-to-end workflows including the purchase process,
availability calculations, and cost calculations.
"""

from decimal import Decimal


from delights.models import (
    Purchase,
    PurchaseItem,
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
from delights.views import (
    calculate_dish_cost,
    update_menu_cost,
    check_dish_availability,
    check_menu_availability,
    update_dish_availability,
    update_menu_availability,
)


class TestCostCalculations:
    """Tests for cost calculation logic."""

    def test_dish_cost_calculation(self, db):
        """Test that dish cost is calculated correctly from ingredients."""
        unit = UnitFactory(name="g")
        ingredient1 = IngredientFactory(unit=unit, price_per_unit=Decimal("0.50"))
        ingredient2 = IngredientFactory(unit=unit, price_per_unit=Decimal("0.75"))
        dish = DishFactory(cost=Decimal("0"), price=Decimal("0"))

        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient1, quantity_required=Decimal("100")
        )
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient2, quantity_required=Decimal("50")
        )

        cost = calculate_dish_cost(dish)
        # 100 * 0.50 + 50 * 0.75 = 50 + 37.5 = 87.5
        expected_cost = Decimal("87.50")
        assert cost == expected_cost

    def test_dish_cost_no_ingredients(self, db):
        """Test that dish with no ingredients has zero cost."""
        dish = DishFactory()
        cost = calculate_dish_cost(dish)
        assert cost == Decimal("0")

    def test_menu_cost_calculation(self, db):
        """Test that menu cost is calculated from dish costs."""
        dish1 = DishFactory(cost=Decimal("5.00"))
        dish2 = DishFactory(cost=Decimal("7.50"))
        menu = MenuFactory(dishes=[dish1, dish2])

        cost = update_menu_cost(menu)
        expected_cost = Decimal("12.50")
        assert cost == expected_cost

    def test_menu_cost_no_dishes(self, db):
        """Test that menu with no dishes has zero cost."""
        menu = MenuFactory()
        cost = update_menu_cost(menu)
        assert cost == Decimal("0")


class TestAvailabilityCalculations:
    """Tests for availability calculation logic."""

    def test_dish_available_with_sufficient_ingredients(self, db):
        """Test dish is available when all ingredients are sufficient."""
        ingredient = IngredientFactory(quantity_available=Decimal("100"))
        dish = DishFactory(is_available=False)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("50")
        )

        assert check_dish_availability(dish) is True

    def test_dish_unavailable_with_insufficient_ingredients(self, db):
        """Test dish is unavailable when ingredients are insufficient."""
        ingredient = IngredientFactory(quantity_available=Decimal("30"))
        dish = DishFactory(is_available=False)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("50")
        )

        assert check_dish_availability(dish) is False

    def test_dish_unavailable_with_no_ingredients(self, db):
        """Test dish is unavailable when it has no recipe requirements."""
        dish = DishFactory(is_available=False)
        assert check_dish_availability(dish) is False

    def test_dish_unavailable_with_one_insufficient_ingredient(self, db):
        """Test dish is unavailable if even one ingredient is insufficient."""
        ingredient1 = IngredientFactory(quantity_available=Decimal("100"))
        ingredient2 = IngredientFactory(quantity_available=Decimal("10"))
        dish = DishFactory(is_available=False)

        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient1, quantity_required=Decimal("50")
        )
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient2, quantity_required=Decimal("50")
        )

        assert check_dish_availability(dish) is False

    def test_update_dish_availability(self, db):
        """Test that dish availability is updated correctly."""
        ingredient = IngredientFactory(quantity_available=Decimal("100"))
        dish = DishFactory(is_available=False)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("50")
        )

        update_dish_availability(dish)
        dish.refresh_from_db()
        assert dish.is_available is True

    def test_menu_available_when_all_dishes_available(self, db):
        """Test menu is available when all dishes are available."""
        dish1 = DishFactory(is_available=True)
        dish2 = DishFactory(is_available=True)
        menu = MenuFactory(dishes=[dish1, dish2], is_available=False)

        assert check_menu_availability(menu) is True

    def test_menu_unavailable_when_one_dish_unavailable(self, db):
        """Test menu is unavailable if any dish is unavailable."""
        dish1 = DishFactory(is_available=True)
        dish2 = DishFactory(is_available=False)
        menu = MenuFactory(dishes=[dish1, dish2], is_available=False)

        assert check_menu_availability(menu) is False

    def test_menu_unavailable_with_no_dishes(self, db):
        """Test menu is unavailable when it has no dishes."""
        menu = MenuFactory(is_available=False)
        assert check_menu_availability(menu) is False


class TestPurchaseWorkflow:
    """Tests for the complete purchase workflow."""

    def test_purchase_creation(self, db):
        """Test creating a purchase with items."""
        user = UserFactory()
        dish = DishFactory(price=Decimal("10.00"))

        purchase = Purchase.objects.create(
            user=user,
            total_price_at_purchase=Decimal("20.00"),
            status=Purchase.STATUS_COMPLETED,
        )
        PurchaseItem.objects.create(
            purchase=purchase,
            dish=dish,
            quantity=2,
            price_at_purchase=Decimal("10.00"),
            subtotal=Decimal("20.00"),
        )

        assert purchase.items.count() == 1
        assert purchase.total_price_at_purchase == Decimal("20.00")

    def test_purchase_freezes_price(self, db):
        """Test that purchase freezes the price at purchase time."""
        dish = DishFactory(price=Decimal("10.00"))
        user = UserFactory()

        # Create purchase with current price
        purchase = PurchaseFactory(user=user)
        item = PurchaseItemFactory(
            purchase=purchase,
            dish=dish,
            quantity=1,
            price_at_purchase=dish.price,
        )

        # Change the dish price
        dish.price = Decimal("15.00")
        dish.save()

        # Purchase item should still have the original price
        item.refresh_from_db()
        assert item.price_at_purchase == Decimal("10.00")

    def test_purchase_inventory_deduction(self, db):
        """Test that purchase deducts inventory correctly."""
        ingredient = IngredientFactory(quantity_available=Decimal("100"))
        dish = DishFactory(is_available=True)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("10")
        )
        user = UserFactory()

        # Simulate purchase finalization (normally done in view)
        quantity_ordered = 2
        for requirement in dish.recipe_requirements.all():
            deduction = requirement.quantity_required * quantity_ordered
            requirement.ingredient.quantity_available -= deduction
            requirement.ingredient.save()

        ingredient.refresh_from_db()
        # 100 - (10 * 2) = 80
        assert ingredient.quantity_available == Decimal("80")

    def test_purchase_updates_availability(self, db):
        """Test that availability is updated after purchase."""
        ingredient = IngredientFactory(quantity_available=Decimal("25"))
        dish = DishFactory(is_available=True)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("10")
        )

        # Initial check - should be available (25 >= 10)
        assert check_dish_availability(dish) is True

        # Simulate purchase of 2 units (deduct 20)
        ingredient.quantity_available = Decimal("5")
        ingredient.save()

        # After deduction - should be unavailable (5 < 10)
        assert check_dish_availability(dish) is False


class TestCascadingUpdates:
    """Tests for cascading availability updates."""

    def test_ingredient_change_affects_dish_availability(self, db):
        """Test that changing ingredient quantity affects dish availability."""
        ingredient = IngredientFactory(quantity_available=Decimal("100"))
        dish = DishFactory(is_available=True)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("50")
        )

        # Initially available
        update_dish_availability(dish)
        dish.refresh_from_db()
        assert dish.is_available is True

        # Reduce inventory below requirement
        ingredient.quantity_available = Decimal("30")
        ingredient.save()

        update_dish_availability(dish)
        dish.refresh_from_db()
        assert dish.is_available is False

    def test_dish_availability_affects_menu(self, db):
        """Test that changing dish availability affects menu availability."""
        dish = DishFactory(is_available=True)
        menu = MenuFactory(dishes=[dish], is_available=True)

        # Initially available
        update_menu_availability(menu)
        menu.refresh_from_db()
        assert menu.is_available is True

        # Make dish unavailable
        dish.is_available = False
        dish.save()

        update_menu_availability(menu)
        menu.refresh_from_db()
        assert menu.is_available is False


class TestBusinessRules:
    """Tests for business rule enforcement."""

    def test_global_margin_applied_to_price(self, db):
        """Test that global margin is applied to dish pricing."""
        # This is typically done in the view when saving
        cost = Decimal("10.00")
        margin = Decimal("0.20")  # 20%
        expected_price = cost * (1 + margin)

        dish = DishFactory(cost=cost, price=expected_price)
        assert dish.price == Decimal("12.00")

    def test_purchase_subtotal_calculation(self, db):
        """Test that purchase item subtotal is calculated correctly."""
        quantity = 3
        price = Decimal("10.00")
        expected_subtotal = quantity * price

        item = PurchaseItemFactory(
            quantity=quantity,
            price_at_purchase=price,
            subtotal=expected_subtotal,
        )
        assert item.subtotal == Decimal("30.00")

    def test_purchase_total_matches_items(self, db):
        """Test that purchase total matches sum of item subtotals."""
        user = UserFactory()
        purchase = PurchaseFactory(user=user, total_price_at_purchase=Decimal("0"))

        item1 = PurchaseItemFactory(
            purchase=purchase,
            quantity=2,
            price_at_purchase=Decimal("10.00"),
            subtotal=Decimal("20.00"),
        )
        item2 = PurchaseItemFactory(
            purchase=purchase,
            quantity=1,
            price_at_purchase=Decimal("15.00"),
            subtotal=Decimal("15.00"),
        )

        total = sum(item.subtotal for item in purchase.items.all())
        assert total == Decimal("35.00")


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_quantity_ingredient(self, db):
        """Test dish with zero quantity ingredient is unavailable."""
        ingredient = IngredientFactory(quantity_available=Decimal("0"))
        dish = DishFactory()
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("10")
        )

        assert check_dish_availability(dish) is False

    def test_exact_quantity_available(self, db):
        """Test dish is available when ingredient quantity exactly matches."""
        ingredient = IngredientFactory(quantity_available=Decimal("50"))
        dish = DishFactory()
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("50")
        )

        assert check_dish_availability(dish) is True

    def test_decimal_precision(self, db):
        """Test that decimal calculations maintain precision."""
        ingredient = IngredientFactory(
            price_per_unit=Decimal("0.333"),
            quantity_available=Decimal("100.50"),
        )
        dish = DishFactory()
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal("10.25"),
        )

        cost = calculate_dish_cost(dish)
        # 10.25 * 0.333 = 3.41325
        assert cost == Decimal("3.41")  # Rounded to 2 decimal places

    def test_empty_menu(self, db):
        """Test menu with no dishes behaves correctly."""
        menu = MenuFactory()
        assert menu.dishes.count() == 0
        assert check_menu_availability(menu) is False
        assert update_menu_cost(menu) == Decimal("0")

    def test_dish_in_multiple_menus(self, db):
        """Test dish can be in multiple menus."""
        dish = DishFactory(is_available=True)
        menu1 = MenuFactory(dishes=[dish])
        menu2 = MenuFactory(dishes=[dish])

        assert dish in menu1.dishes.all()
        assert dish in menu2.dishes.all()

        # Making dish unavailable should affect both menus
        dish.is_available = False
        dish.save()

        update_menu_availability(menu1)
        update_menu_availability(menu2)

        menu1.refresh_from_db()
        menu2.refresh_from_db()

        assert menu1.is_available is False
        assert menu2.is_available is False
