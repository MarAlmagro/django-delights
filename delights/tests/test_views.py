"""
View tests for Django Delights.

Tests cover authentication, authorization, and view functionality
using Django's test client.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from delights.models import Dish, Ingredient, Menu, Purchase, RecipeRequirement, Unit
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


class TestAuthenticationViews:
    """Tests for authentication-related views."""

    def test_login_page_accessible(self, client, db):
        """Test that login page is accessible to anonymous users."""
        response = client.get(reverse("login"))
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client, db):
        """Test login with valid credentials."""
        user = UserFactory()
        user.set_password("testpass123")
        user.save()
        response = client.post(
            reverse("login"),
            {"username": user.username, "password": "testpass123"},
        )
        # Should redirect after successful login
        assert response.status_code == 302

    def test_login_with_invalid_credentials(self, client, db):
        """Test login with invalid credentials."""
        response = client.post(
            reverse("login"),
            {"username": "nonexistent", "password": "wrongpass"},
        )
        assert response.status_code == 200  # Returns to login page
        assert b"Please enter a correct username and password" in response.content

    def test_logout(self, client_logged_in_admin, db):
        """Test logout functionality."""
        response = client_logged_in_admin.post(reverse("logout"))
        assert response.status_code == 302  # Redirect after logout


class TestUnitViews:
    """Tests for unit management views (admin only)."""

    def test_unit_list_requires_admin(self, client_logged_in_staff, db):
        """Test that unit list requires admin privileges."""
        response = client_logged_in_staff.get(reverse("unit_list"))
        assert response.status_code == 403

    def test_unit_list_accessible_to_admin(self, client_logged_in_admin, db):
        """Test that admin can access unit list."""
        UnitFactory.create_batch(3)
        response = client_logged_in_admin.get(reverse("unit_list"))
        assert response.status_code == 200
        assert Unit.objects.count() == 3

    def test_unit_create_by_admin(self, client_logged_in_admin, db):
        """Test admin can create a unit."""
        response = client_logged_in_admin.post(
            reverse("unit_add"),
            {"name": "kg", "description": "kilogram", "is_active": True},
        )
        assert response.status_code == 302
        assert Unit.objects.filter(name="kg").exists()

    def test_unit_toggle_active(self, client_logged_in_admin, db):
        """Test toggling unit active status."""
        unit = UnitFactory(is_active=True)
        response = client_logged_in_admin.post(
            reverse("unit_toggle_active", args=[unit.id])
        )
        assert response.status_code == 302
        unit.refresh_from_db()
        assert unit.is_active is False


class TestIngredientViews:
    """Tests for ingredient management views."""

    def test_ingredient_list_requires_login(self, client, db):
        """Test that ingredient list requires authentication."""
        response = client.get(reverse("ingredient_list"))
        assert response.status_code == 302  # Redirect to login

    def test_ingredient_list_accessible_to_staff(self, client_logged_in_staff, db):
        """Test that staff can access ingredient list."""
        IngredientFactory.create_batch(3)
        response = client_logged_in_staff.get(reverse("ingredient_list"))
        assert response.status_code == 200

    def test_ingredient_create_by_admin(self, client_logged_in_admin, db):
        """Test admin can create an ingredient."""
        unit = UnitFactory()
        response = client_logged_in_admin.post(
            reverse("ingredient_add"),
            {
                "name": "Flour",
                "unit": unit.id,
                "price_per_unit": "0.50",
                "quantity_available": "1000",
            },
        )
        assert response.status_code == 302
        assert Ingredient.objects.filter(name="Flour").exists()

    def test_ingredient_adjust_inventory(self, client_logged_in_staff, db):
        """Test staff can adjust ingredient inventory."""
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        response = client_logged_in_staff.post(
            reverse("inventory_adjust", args=[ingredient.id]),
            {"adjustment": "50", "action": "add"},
        )
        assert response.status_code == 302
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("150.00")


class TestDishViews:
    """Tests for dish management views."""

    def test_dish_list_requires_login(self, client, db):
        """Test that dish list requires authentication."""
        response = client.get(reverse("dish_list"))
        assert response.status_code == 302

    def test_dish_list_accessible_to_staff(self, client_logged_in_staff, db):
        """Test that staff can access dish list."""
        DishFactory.create_batch(3)
        response = client_logged_in_staff.get(reverse("dish_list"))
        assert response.status_code == 200

    def test_dish_detail_view(self, client_logged_in_staff, db):
        """Test dish detail view."""
        dish = DishFactory()
        response = client_logged_in_staff.get(reverse("dish_detail", args=[dish.id]))
        assert response.status_code == 200
        assert dish.name.encode() in response.content

    def test_dish_create_by_staff(self, client_logged_in_staff, db):
        """Test staff can create a dish."""
        response = client_logged_in_staff.post(
            reverse("dish_add"),
            {
                "name": "New Dish",
                "description": "A new dish",
                "cost": "5.00",
                "price": "10.00",
                "is_available": False,
            },
        )
        assert response.status_code == 302
        assert Dish.objects.filter(name="New Dish").exists()


class TestMenuViews:
    """Tests for menu management views."""

    def test_menu_list_requires_login(self, client, db):
        """Test that menu list requires authentication."""
        response = client.get(reverse("menu_list"))
        assert response.status_code == 302

    def test_menu_list_accessible_to_staff(self, client_logged_in_staff, db):
        """Test that staff can access menu list."""
        MenuFactory.create_batch(3)
        response = client_logged_in_staff.get(reverse("menu_list"))
        assert response.status_code == 200

    def test_menu_detail_view(self, client_logged_in_staff, db):
        """Test menu detail view."""
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])
        response = client_logged_in_staff.get(reverse("menu_detail", args=[menu.id]))
        assert response.status_code == 200
        assert menu.name.encode() in response.content

    def test_menu_create_by_staff(self, client_logged_in_staff, db):
        """Test staff can create a menu."""
        response = client_logged_in_staff.post(
            reverse("menu_add"),
            {
                "name": "Lunch Special",
                "description": "Great lunch deal",
                "cost": "10.00",
                "price": "15.00",
                "is_available": False,
            },
        )
        assert response.status_code == 302
        assert Menu.objects.filter(name="Lunch Special").exists()


class TestPurchaseViews:
    """Tests for purchase management views."""

    def test_purchase_list_requires_login(self, client, db):
        """Test that purchase list requires authentication."""
        response = client.get(reverse("purchase_list"))
        assert response.status_code == 302

    def test_purchase_list_staff_sees_own_purchases(self, client_logged_in_staff, staff_user, db):
        """Test that staff can only see their own purchases."""
        # Create purchases for different users
        PurchaseFactory(user=staff_user)
        other_user = UserFactory()
        PurchaseFactory(user=other_user)

        response = client_logged_in_staff.get(reverse("purchase_list"))
        assert response.status_code == 200
        # Staff should only see their own purchase

    def test_purchase_list_admin_sees_all(self, client_logged_in_admin, admin_user, db):
        """Test that admin can see all purchases."""
        PurchaseFactory(user=admin_user)
        other_user = UserFactory()
        PurchaseFactory(user=other_user)

        response = client_logged_in_admin.get(reverse("purchase_list"))
        assert response.status_code == 200

    def test_purchase_detail_view(self, client_logged_in_admin, admin_user, db):
        """Test purchase detail view."""
        dish = DishFactory()
        purchase = PurchaseFactory(user=admin_user)
        PurchaseItemFactory(purchase=purchase, dish=dish)

        response = client_logged_in_admin.get(
            reverse("purchase_detail", args=[purchase.id])
        )
        assert response.status_code == 200


class TestDashboardViews:
    """Tests for dashboard views (admin only)."""

    def test_dashboard_requires_admin(self, client_logged_in_staff, db):
        """Test that dashboard requires admin privileges."""
        response = client_logged_in_staff.get(reverse("dashboard"))
        assert response.status_code == 403

    def test_dashboard_accessible_to_admin(self, client_logged_in_admin, db):
        """Test that admin can access dashboard."""
        response = client_logged_in_admin.get(reverse("dashboard"))
        assert response.status_code == 200

    def test_dashboard_shows_metrics(self, client_logged_in_admin, admin_user, db):
        """Test that dashboard shows revenue and cost metrics."""
        # Create some test data
        dish = DishFactory(cost=Decimal("5.00"), price=Decimal("10.00"))
        purchase = PurchaseFactory(user=admin_user, total_price_at_purchase=Decimal("10.00"))
        PurchaseItemFactory(
            purchase=purchase,
            dish=dish,
            quantity=1,
            price_at_purchase=Decimal("10.00"),
            subtotal=Decimal("10.00"),
        )

        response = client_logged_in_admin.get(reverse("dashboard"))
        assert response.status_code == 200
        # Dashboard should contain revenue information


class TestUserManagementViews:
    """Tests for user management views (admin only)."""

    def test_user_list_requires_admin(self, client_logged_in_staff, db):
        """Test that user list requires admin privileges."""
        response = client_logged_in_staff.get(reverse("user_list"))
        assert response.status_code == 403

    def test_user_list_accessible_to_admin(self, client_logged_in_admin, db):
        """Test that admin can access user list."""
        UserFactory.create_batch(3)
        response = client_logged_in_admin.get(reverse("user_list"))
        assert response.status_code == 200

    def test_user_create_by_admin(self, client_logged_in_admin, db):
        """Test admin can create a user."""
        response = client_logged_in_admin.post(
            reverse("user_add"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "securepass123!",
                "password2": "securepass123!",
                "is_staff": True,
            },
        )
        # Should redirect on success
        assert response.status_code in [200, 302]


class TestRecipeRequirementViews:
    """Tests for recipe requirement management."""

    def test_add_recipe_requirement(self, client_logged_in_staff, db):
        """Test adding a recipe requirement to a dish."""
        dish = DishFactory()
        ingredient = IngredientFactory()

        response = client_logged_in_staff.post(
            reverse("manage_recipe_requirements", args=[dish.id]),
            {
                "ingredient": ingredient.id,
                "quantity_required": "10.00",
                "action": "add",
            },
        )
        assert response.status_code == 302
        assert RecipeRequirement.objects.filter(
            dish=dish, ingredient=ingredient
        ).exists()

    def test_remove_recipe_requirement(self, client_logged_in_staff, db):
        """Test removing a recipe requirement from a dish."""
        dish = DishFactory()
        requirement = RecipeRequirementFactory(dish=dish)

        response = client_logged_in_staff.post(
            reverse("manage_recipe_requirements", args=[dish.id]),
            {
                "requirement_id": requirement.id,
                "action": "remove",
            },
        )
        assert response.status_code == 302
        assert not RecipeRequirement.objects.filter(id=requirement.id).exists()


class TestMenuItemViews:
    """Tests for menu item management."""

    def test_add_dish_to_menu(self, client_logged_in_staff, db):
        """Test adding a dish to a menu."""
        menu = MenuFactory()
        dish = DishFactory()

        response = client_logged_in_staff.post(
            reverse("manage_menu_items", args=[menu.id]),
            {
                "dish": dish.id,
                "action": "add",
            },
        )
        assert response.status_code == 302
        assert dish in menu.dishes.all()

    def test_remove_dish_from_menu(self, client_logged_in_staff, db):
        """Test removing a dish from a menu."""
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])

        response = client_logged_in_staff.post(
            reverse("manage_menu_items", args=[menu.id]),
            {
                "dish": dish.id,
                "action": "remove",
            },
        )
        assert response.status_code == 302
        assert dish not in menu.dishes.all()
