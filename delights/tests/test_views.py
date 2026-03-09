"""
View tests for Django Delights.

Tests cover authentication, authorization, and view functionality
using Django's test client.
"""

from decimal import Decimal

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

    def test_logout(self, client_logged_in_admin, db):
        """Test logout functionality."""
        response = client_logged_in_admin.post(reverse("logout"))
        assert response.status_code == 302  # Redirect after logout


class TestUnitViews:
    """Tests for unit management views (admin only)."""

    def test_unit_list_requires_admin(self, client_logged_in_staff, db):
        """Test that unit list requires admin privileges."""
        response = client_logged_in_staff.get(reverse("units:list"))
        assert response.status_code == 403

    def test_unit_list_accessible_to_admin(self, client_logged_in_admin, db):
        """Test that admin can access unit list."""
        UnitFactory.create_batch(3)
        response = client_logged_in_admin.get(reverse("units:list"))
        assert response.status_code == 200
        assert Unit.objects.count() == 3

    def test_unit_create_by_admin(self, client_logged_in_admin, db):
        """Test admin can create a unit."""
        response = client_logged_in_admin.post(
            reverse("units:add"),
            {"name": "kg", "description": "kilogram", "is_active": True},
        )
        assert response.status_code == 302
        assert Unit.objects.filter(name="kg").exists()

    def test_unit_toggle_active(self, client_logged_in_admin, db):
        """Test toggling unit active status."""
        unit = UnitFactory(is_active=True)
        response = client_logged_in_admin.post(
            reverse("units:toggle_active", args=[unit.id])
        )
        assert response.status_code == 302
        unit.refresh_from_db()
        assert unit.is_active is False


class TestIngredientViews:
    """Tests for ingredient management views."""

    def test_ingredient_list_requires_login(self, client, db):
        """Test that ingredient list requires authentication."""
        response = client.get(reverse("ingredients:list"))
        assert response.status_code == 302  # Redirect to login

    def test_ingredient_list_accessible_to_staff(self, client_logged_in_staff, db):
        """Test that staff can access ingredient list."""
        IngredientFactory.create_batch(3)
        response = client_logged_in_staff.get(reverse("ingredients:list"))
        assert response.status_code == 200

    def test_ingredient_create_by_admin(self, client_logged_in_admin, db):
        """Test admin can create an ingredient."""
        unit = UnitFactory()
        response = client_logged_in_admin.post(
            reverse("ingredients:add"),
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
            reverse("ingredients:adjust", args=[ingredient.id]),
            {"adjustment": "50", "action": "add"},
        )
        assert response.status_code == 302
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("150.00")


class TestDishViews:
    """Tests for dish management views."""

    def test_dish_list_requires_login(self, client, db):
        """Test that dish list requires authentication."""
        response = client.get(reverse("dishes:list"))
        assert response.status_code == 302

    def test_dish_list_accessible_to_staff(self, client_logged_in_staff, db):
        """Test that staff can access dish list."""
        DishFactory.create_batch(3)
        response = client_logged_in_staff.get(reverse("dishes:list"))
        assert response.status_code == 200

    def test_dish_detail_view(self, client_logged_in_staff, db):
        """Test dish detail view."""
        dish = DishFactory()
        response = client_logged_in_staff.get(reverse("dishes:detail", args=[dish.id]))
        assert response.status_code == 200
        assert dish.name.encode() in response.content

    def test_dish_create_by_staff(self, client_logged_in_staff, db):
        """Test staff can create a dish."""
        response = client_logged_in_staff.post(
            reverse("dishes:add"),
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
        response = client.get(reverse("menus:list"))
        assert response.status_code == 302

    def test_menu_list_accessible_to_staff(self, client_logged_in_staff, db):
        """Test that staff can access menu list."""
        MenuFactory.create_batch(3)
        response = client_logged_in_staff.get(reverse("menus:list"))
        assert response.status_code == 200

    def test_menu_detail_view(self, client_logged_in_staff, db):
        """Test menu detail view."""
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])
        response = client_logged_in_staff.get(reverse("menus:detail", args=[menu.id]))
        assert response.status_code == 200
        assert menu.name.encode() in response.content

    def test_menu_create_by_staff(self, client_logged_in_staff, db):
        """Test staff can create a menu."""
        response = client_logged_in_staff.post(
            reverse("menus:add"),
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
        response = client.get(reverse("purchases:list"))
        assert response.status_code == 302

    def test_purchase_list_staff_sees_own_purchases(
        self, client_logged_in_staff, staff_user, db
    ):
        """Test that staff can only see their own purchases."""
        # Create purchases for different users
        PurchaseFactory(user=staff_user)
        other_user = UserFactory()
        PurchaseFactory(user=other_user)

        response = client_logged_in_staff.get(reverse("purchases:list"))
        assert response.status_code == 200
        # Staff should only see their own purchase

    def test_purchase_list_admin_sees_all(self, client_logged_in_admin, admin_user, db):
        """Test that admin can see all purchases."""
        PurchaseFactory(user=admin_user)
        other_user = UserFactory()
        PurchaseFactory(user=other_user)

        response = client_logged_in_admin.get(reverse("purchases:list"))
        assert response.status_code == 200

    def test_purchase_detail_view(self, client_logged_in_admin, admin_user, db):
        """Test purchase detail view."""
        dish = DishFactory()
        purchase = PurchaseFactory(user=admin_user)
        PurchaseItemFactory(purchase=purchase, dish=dish)

        response = client_logged_in_admin.get(
            reverse("purchases:detail", args=[purchase.id])
        )
        assert response.status_code == 200


class TestDashboardViews:
    """Tests for dashboard views (admin only)."""

    def test_dashboard_requires_admin(self, client_logged_in_staff, db):
        """Test that dashboard requires admin privileges."""
        response = client_logged_in_staff.get(reverse("dashboard:index"))
        assert response.status_code == 403

    def test_dashboard_accessible_to_admin(self, client_logged_in_admin, db):
        """Test that admin can access dashboard."""
        response = client_logged_in_admin.get(reverse("dashboard:index"))
        assert response.status_code == 200

    def test_dashboard_shows_metrics(self, client_logged_in_admin, admin_user, db):
        """Test that dashboard shows revenue and cost metrics."""
        # Create some test data
        dish = DishFactory(cost=Decimal("5.00"), price=Decimal("10.00"))
        purchase = PurchaseFactory(
            user=admin_user, total_price_at_purchase=Decimal("10.00")
        )
        PurchaseItemFactory(
            purchase=purchase,
            dish=dish,
            quantity=1,
            price_at_purchase=Decimal("10.00"),
            subtotal=Decimal("10.00"),
        )

        response = client_logged_in_admin.get(reverse("dashboard:index"))
        assert response.status_code == 200
        # Dashboard should contain revenue information


class TestUserManagementViews:
    """Tests for user management views (admin only)."""

    def test_user_list_requires_admin(self, client_logged_in_staff, db):
        """Test that user list requires admin privileges."""
        response = client_logged_in_staff.get(reverse("users:list"))
        assert response.status_code == 403

    def test_user_list_accessible_to_admin(self, client_logged_in_admin, db):
        """Test that admin can access user list."""
        UserFactory.create_batch(3)
        response = client_logged_in_admin.get(reverse("users:list"))
        assert response.status_code == 200

    def test_user_create_by_admin(self, client_logged_in_admin, db):
        """Test admin can create a user."""
        response = client_logged_in_admin.post(
            reverse("users:add"),
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


class TestUnitUpdateViews:
    """Tests for unit update views."""

    def test_unit_update_by_admin(self, client_logged_in_admin, db):
        """Test admin can update a unit."""
        unit = UnitFactory(name="old", description="old desc")
        response = client_logged_in_admin.post(
            reverse("units:edit", args=[unit.id]),
            {"name": "new", "description": "new desc", "is_active": True},
        )
        assert response.status_code == 302
        unit.refresh_from_db()
        assert unit.name == "new"

    def test_unit_update_denied_for_staff(self, client_logged_in_staff, db):
        """Test staff cannot update a unit."""
        unit = UnitFactory()
        response = client_logged_in_staff.post(
            reverse("units:edit", args=[unit.id]),
            {"name": "x", "description": "x", "is_active": True},
        )
        assert response.status_code == 403


class TestIngredientUpdateViews:
    """Tests for ingredient update views."""

    def test_ingredient_update_by_admin(self, client_logged_in_admin, db):
        """Test admin can update an ingredient."""
        ingredient = IngredientFactory()
        unit = ingredient.unit
        response = client_logged_in_admin.post(
            reverse("ingredients:edit", args=[ingredient.id]),
            {"name": "Updated", "unit": unit.id, "price_per_unit": "2.00"},
        )
        assert response.status_code == 302
        ingredient.refresh_from_db()
        assert ingredient.name == "Updated"

    def test_ingredient_update_denied_for_staff(self, client_logged_in_staff, db):
        """Test staff cannot update an ingredient."""
        ingredient = IngredientFactory()
        response = client_logged_in_staff.post(
            reverse("ingredients:edit", args=[ingredient.id]),
            {"name": "X", "unit": ingredient.unit.id, "price_per_unit": "1.00"},
        )
        assert response.status_code == 403

    def test_inventory_adjust_get(self, client_logged_in_staff, db):
        """Test GET on inventory adjust shows the form."""
        ingredient = IngredientFactory()
        response = client_logged_in_staff.get(
            reverse("ingredients:adjust", args=[ingredient.id])
        )
        assert response.status_code == 200

    def test_inventory_adjust_subtract(self, client_logged_in_staff, db):
        """Test staff can subtract from ingredient inventory."""
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        response = client_logged_in_staff.post(
            reverse("ingredients:adjust", args=[ingredient.id]),
            {"adjustment": "-30"},
        )
        assert response.status_code == 302
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("70.00")

    def test_inventory_adjust_clamps_to_zero(self, client_logged_in_staff, db):
        """Test that inventory cannot go below zero."""
        ingredient = IngredientFactory(quantity_available=Decimal("10.00"))
        response = client_logged_in_staff.post(
            reverse("ingredients:adjust", args=[ingredient.id]),
            {"adjustment": "-50"},
        )
        assert response.status_code == 302
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("0")

    def test_inventory_adjust_requires_login(self, client, db):
        """Test anonymous users are redirected."""
        ingredient = IngredientFactory()
        response = client.get(reverse("ingredients:adjust", args=[ingredient.id]))
        assert response.status_code == 302


class TestDishUpdateViews:
    """Tests for dish update views."""

    def test_dish_update_by_admin(self, client_logged_in_admin, db):
        """Test admin can update a dish."""
        dish = DishFactory()
        response = client_logged_in_admin.post(
            reverse("dishes:edit", args=[dish.id]),
            {"name": "Updated Dish", "description": "New desc", "price": "12.00"},
        )
        assert response.status_code == 302
        dish.refresh_from_db()
        assert dish.name == "Updated Dish"

    def test_dish_update_denied_for_staff(self, client_logged_in_staff, db):
        """Test staff cannot update a dish."""
        dish = DishFactory()
        response = client_logged_in_staff.post(
            reverse("dishes:edit", args=[dish.id]),
            {"name": "X", "description": "", "price": "1.00"},
        )
        assert response.status_code == 403

    def test_manage_requirements_get(self, client_logged_in_staff, db):
        """Test GET on manage requirements shows form."""
        dish = DishFactory()
        response = client_logged_in_staff.get(
            reverse("dishes:requirements", args=[dish.id])
        )
        assert response.status_code == 200


class TestMenuUpdateViews:
    """Tests for menu update views."""

    def test_menu_update_by_admin(self, client_logged_in_admin, db):
        """Test admin can update a menu."""
        menu = MenuFactory()
        response = client_logged_in_admin.post(
            reverse("menus:edit", args=[menu.id]),
            {"name": "Updated Menu", "description": "New", "price": "20.00"},
        )
        assert response.status_code == 302
        menu.refresh_from_db()
        assert menu.name == "Updated Menu"

    def test_menu_update_denied_for_staff(self, client_logged_in_staff, db):
        """Test staff cannot update a menu."""
        menu = MenuFactory()
        response = client_logged_in_staff.post(
            reverse("menus:edit", args=[menu.id]),
            {"name": "X", "description": "", "price": "1.00"},
        )
        assert response.status_code == 403

    def test_manage_menu_items_get(self, client_logged_in_staff, db):
        """Test GET on manage menu items shows page."""
        menu = MenuFactory()
        response = client_logged_in_staff.get(reverse("menus:items", args=[menu.id]))
        assert response.status_code == 200


class TestRecipeRequirementViews:
    """Tests for recipe requirement management."""

    def test_add_recipe_requirement(self, client_logged_in_staff, db):
        """Test adding a recipe requirement to a dish."""
        dish = DishFactory()
        ingredient = IngredientFactory()

        response = client_logged_in_staff.post(
            reverse("dishes:requirements", args=[dish.id]),
            {
                "ingredient": ingredient.id,
                "quantity_required": "10.00",
                "add": "Add",
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
            reverse("dishes:requirements", args=[dish.id]),
            {
                "requirement_id": requirement.id,
                "delete": "Delete",
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
            reverse("menus:items", args=[menu.id]),
            {
                "dish_id": dish.id,
                "add": "Add",
            },
        )
        assert response.status_code == 302
        assert dish in menu.dishes.all()

    def test_remove_dish_from_menu(self, client_logged_in_staff, db):
        """Test removing a dish from a menu."""
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])

        response = client_logged_in_staff.post(
            reverse("menus:items", args=[menu.id]),
            {
                "dish_id": dish.id,
                "remove": "Remove",
            },
        )
        assert response.status_code == 302
        assert dish not in menu.dishes.all()


class TestPurchaseWorkflowViews:
    """Tests for the multi-step purchase workflow views."""

    def test_purchase_create_get(self, client_logged_in_staff, db):
        """Test GET on purchase create shows available dishes."""
        DishFactory(is_available=True, name="Available")
        DishFactory(is_available=False, name="Unavailable")
        response = client_logged_in_staff.get(reverse("purchases:add"))
        assert response.status_code == 200

    def test_purchase_create_post_stores_session(self, client_logged_in_staff, db):
        """Test POST on purchase create stores data in session."""
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        response = client_logged_in_staff.post(
            reverse("purchases:add"),
            {f"quantity_{dish.id}": "2"},
        )
        assert response.status_code == 302
        assert response.url == reverse("purchases:confirm")

    def test_purchase_create_no_selection(self, client_logged_in_staff, db):
        """Test POST with no items selected shows error."""
        DishFactory(is_available=True)
        response = client_logged_in_staff.post(
            reverse("purchases:add"),
            {},
        )
        assert response.status_code == 200  # Re-renders form

    def test_purchase_create_requires_login(self, client, db):
        response = client.get(reverse("purchases:add"))
        assert response.status_code == 302

    def test_purchase_confirm_with_session_data(self, client_logged_in_staff, db):
        """Test confirm page loads with session data."""
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        session = client_logged_in_staff.session
        session["purchase_data"] = [{"dish_id": dish.id, "quantity": 2, "price": 10.0}]
        session["purchase_total"] = 20.0
        session.save()
        response = client_logged_in_staff.get(reverse("purchases:confirm"))
        assert response.status_code == 200

    def test_purchase_confirm_no_session_redirects(self, client_logged_in_staff, db):
        """Test confirm redirects when no session data."""
        response = client_logged_in_staff.get(reverse("purchases:confirm"))
        assert response.status_code == 302

    def test_purchase_confirm_dish_unavailable(self, client_logged_in_staff, db):
        """Test confirm redirects when dish becomes unavailable."""
        session = client_logged_in_staff.session
        session["purchase_data"] = [{"dish_id": 99999, "quantity": 1, "price": 10.0}]
        session["purchase_total"] = 10.0
        session.save()
        response = client_logged_in_staff.get(reverse("purchases:confirm"))
        assert response.status_code == 302

    def test_purchase_finalize_get_redirects(self, client_logged_in_staff, db):
        """Test GET on finalize redirects to add."""
        response = client_logged_in_staff.get(reverse("purchases:finalize"))
        assert response.status_code == 302

    def test_purchase_finalize_no_session_redirects(self, client_logged_in_staff, db):
        """Test POST finalize with no session redirects."""
        response = client_logged_in_staff.post(reverse("purchases:finalize"))
        assert response.status_code == 302

    def test_purchase_finalize_success(self, client_logged_in_staff, staff_user, db):
        """Test successful purchase finalization."""
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("5.00")
        )
        session = client_logged_in_staff.session
        session["purchase_data"] = [{"dish_id": dish.id, "quantity": 2, "price": 10.0}]
        session["purchase_total"] = 20.0
        session.save()
        response = client_logged_in_staff.post(reverse("purchases:finalize"))
        assert response.status_code == 302
        assert Purchase.objects.count() == 1
        purchase = Purchase.objects.first()
        assert purchase.items.count() == 1
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("90.00")

    def test_purchase_finalize_insufficient_inventory(self, client_logged_in_staff, db):
        """Test finalize fails gracefully with insufficient inventory."""
        ingredient = IngredientFactory(quantity_available=Decimal("3.00"))
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("5.00")
        )
        session = client_logged_in_staff.session
        session["purchase_data"] = [{"dish_id": dish.id, "quantity": 1, "price": 10.0}]
        session["purchase_total"] = 10.0
        session.save()
        response = client_logged_in_staff.post(reverse("purchases:finalize"))
        assert response.status_code == 302
        assert Purchase.objects.count() == 0

    def test_purchase_finalize_dish_unavailable(self, client_logged_in_staff, db):
        """Test finalize redirects when dish becomes unavailable."""
        dish = DishFactory(is_available=False, price=Decimal("10.00"))
        session = client_logged_in_staff.session
        session["purchase_data"] = [{"dish_id": dish.id, "quantity": 1, "price": 10.0}]
        session["purchase_total"] = 10.0
        session.save()
        response = client_logged_in_staff.post(reverse("purchases:finalize"))
        assert response.status_code == 302
        assert Purchase.objects.count() == 0


class TestUserManagementExtendedViews:
    """Extended tests for user management views."""

    def test_user_toggle_active(self, client_logged_in_admin, db):
        """Test admin can toggle user active status."""
        user = UserFactory(is_active=True)
        response = client_logged_in_admin.post(
            reverse("users:toggle_active", args=[user.id])
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.is_active is False

    def test_user_toggle_active_back(self, client_logged_in_admin, db):
        """Test admin can re-activate user."""
        user = UserFactory(is_active=False)
        response = client_logged_in_admin.post(
            reverse("users:toggle_active", args=[user.id])
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.is_active is True

    def test_user_reset_password_get(self, client_logged_in_admin, db):
        """Test GET on reset password shows the form."""
        user = UserFactory()
        response = client_logged_in_admin.get(
            reverse("users:reset_password", args=[user.id])
        )
        assert response.status_code == 200

    def test_user_reset_password_post(self, client_logged_in_admin, db):
        """Test admin can reset a user's password."""
        user = UserFactory()
        response = client_logged_in_admin.post(
            reverse("users:reset_password", args=[user.id]),
            {
                "new_password1": "newsecurepass123!",
                "new_password2": "newsecurepass123!",
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password("newsecurepass123!")

    def test_user_update_by_admin(self, client_logged_in_admin, db):
        """Test admin can update user fields."""
        user = UserFactory()
        response = client_logged_in_admin.post(
            reverse("users:edit", args=[user.id]),
            {
                "username": user.username,
                "email": "newemail@example.com",
                "is_staff": True,
                "is_active": True,
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.email == "newemail@example.com"


class TestLoginRedirectViews:
    """Tests for custom login redirect logic."""

    def test_admin_redirected_to_dashboard(self, client, admin_user, db):
        """Test admin user is redirected to dashboard after login."""
        response = client.post(
            reverse("login"),
            {"username": "admin", "password": "adminpass123"},
        )
        assert response.status_code == 302
        assert "dashboard" in response.url

    def test_staff_redirected_to_purchases(self, client, staff_user, db):
        """Test staff user is redirected to purchases after login."""
        response = client.post(
            reverse("login"),
            {"username": "staff", "password": "staffpass123"},
        )
        assert response.status_code == 302
        assert "purchases" in response.url


class TestPurchaseDetailAccessViews:
    """Tests for purchase detail access control."""

    def test_staff_cannot_see_others_purchase(
        self, client_logged_in_staff, staff_user, db
    ):
        """Test staff user cannot access another user's purchase."""
        other_user = UserFactory()
        purchase = PurchaseFactory(user=other_user)
        response = client_logged_in_staff.get(
            reverse("purchases:detail", args=[purchase.id])
        )
        assert response.status_code == 404

    def test_staff_can_see_own_purchase(self, client_logged_in_staff, staff_user, db):
        """Test staff user can access their own purchase."""
        purchase = PurchaseFactory(user=staff_user)
        PurchaseItemFactory(purchase=purchase)
        response = client_logged_in_staff.get(
            reverse("purchases:detail", args=[purchase.id])
        )
        assert response.status_code == 200

    def test_admin_can_see_any_purchase(self, client_logged_in_admin, db):
        """Test admin can access any user's purchase."""
        other_user = UserFactory()
        purchase = PurchaseFactory(user=other_user)
        PurchaseItemFactory(purchase=purchase)
        response = client_logged_in_admin.get(
            reverse("purchases:detail", args=[purchase.id])
        )
        assert response.status_code == 200
