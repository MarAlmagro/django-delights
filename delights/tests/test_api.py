"""
API tests for Django Delights REST API.

Tests cover all API endpoints including health check, CRUD operations,
custom actions, permissions, and business logic.
"""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from delights.models import (
    Ingredient,
    Menu,
    Purchase,
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


# =============================================================================
# Health Check
# =============================================================================


class TestHealthCheckAPI:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, api_client, db):
        url = reverse("api-health")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert "checks" in response.data

    def test_health_check_no_auth_required(self, api_client, db):
        url = reverse("api-health")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Unit API
# =============================================================================


class TestUnitAPI:
    """Tests for the Unit API endpoints."""

    def test_list_units_requires_auth(self, api_client, db):
        url = reverse("unit-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_units_as_staff(self, api_client_staff, db):
        UnitFactory.create_batch(3)
        url = reverse("unit-list")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_list_units_as_admin(self, api_client_admin, db):
        UnitFactory.create_batch(2)
        url = reverse("unit-list")
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_retrieve_unit(self, api_client_admin, db):
        unit = UnitFactory(name="kg", description="kilogram")
        url = reverse("unit-detail", args=[unit.id])
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "kg"
        assert response.data["description"] == "kilogram"

    def test_create_unit_as_admin(self, api_client_admin, db):
        url = reverse("unit-list")
        response = api_client_admin.post(
            url, {"name": "ml", "description": "milliliter", "is_active": True}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Unit.objects.filter(name="ml").exists()

    def test_create_unit_denied_for_staff(self, api_client_staff, db):
        url = reverse("unit-list")
        response = api_client_staff.post(
            url, {"name": "ml", "description": "milliliter", "is_active": True}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_unit_as_admin(self, api_client_admin, db):
        unit = UnitFactory(name="old", description="old desc")
        url = reverse("unit-detail", args=[unit.id])
        response = api_client_admin.put(
            url, {"name": "new", "description": "new desc", "is_active": True}
        )
        assert response.status_code == status.HTTP_200_OK
        unit.refresh_from_db()
        assert unit.name == "new"

    def test_partial_update_unit(self, api_client_admin, db):
        unit = UnitFactory(name="g", description="gram")
        url = reverse("unit-detail", args=[unit.id])
        response = api_client_admin.patch(url, {"description": "grams"})
        assert response.status_code == status.HTTP_200_OK
        unit.refresh_from_db()
        assert unit.description == "grams"

    def test_delete_unit_as_admin(self, api_client_admin, db):
        unit = UnitFactory()
        url = reverse("unit-detail", args=[unit.id])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Unit.objects.filter(id=unit.id).exists()

    def test_toggle_active(self, api_client_admin, db):
        unit = UnitFactory(is_active=True)
        url = reverse("unit-toggle-active", args=[unit.id])
        response = api_client_admin.post(url)
        assert response.status_code == status.HTTP_200_OK
        unit.refresh_from_db()
        assert unit.is_active is False

    def test_toggle_active_back(self, api_client_admin, db):
        unit = UnitFactory(is_active=False)
        url = reverse("unit-toggle-active", args=[unit.id])
        response = api_client_admin.post(url)
        assert response.status_code == status.HTTP_200_OK
        unit.refresh_from_db()
        assert unit.is_active is True


# =============================================================================
# Ingredient API
# =============================================================================


class TestIngredientAPI:
    """Tests for the Ingredient API endpoints."""

    def test_list_ingredients_requires_auth(self, api_client, db):
        url = reverse("ingredient-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_ingredients_as_staff(self, api_client_staff, db):
        IngredientFactory.create_batch(3)
        url = reverse("ingredient-list")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_list_ingredients_uses_list_serializer(self, api_client_staff, db):
        IngredientFactory()
        url = reverse("ingredient-list")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "unit_name" in response.data["results"][0]

    def test_retrieve_ingredient(self, api_client_staff, db):
        ingredient = IngredientFactory(name="Flour")
        url = reverse("ingredient-detail", args=[ingredient.id])
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Flour"
        assert "unit" in response.data

    def test_create_ingredient_as_admin(self, api_client_admin, db):
        unit = UnitFactory()
        url = reverse("ingredient-list")
        response = api_client_admin.post(
            url,
            {
                "name": "Flour",
                "unit_id": unit.id,
                "price_per_unit": "0.50",
                "quantity_available": "100.00",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Ingredient.objects.filter(name="Flour").exists()

    def test_create_ingredient_as_staff(self, api_client_staff, db):
        unit = UnitFactory()
        url = reverse("ingredient-list")
        response = api_client_staff.post(
            url,
            {
                "name": "Sugar",
                "unit_id": unit.id,
                "price_per_unit": "0.75",
                "quantity_available": "200.00",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_ingredient(self, api_client_admin, db):
        ingredient = IngredientFactory()
        url = reverse("ingredient-detail", args=[ingredient.id])
        response = api_client_admin.put(
            url,
            {
                "name": "Updated Flour",
                "unit_id": ingredient.unit.id,
                "price_per_unit": "1.00",
                "quantity_available": "500.00",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        ingredient.refresh_from_db()
        assert ingredient.name == "Updated Flour"

    def test_adjust_inventory_add(self, api_client_staff, db):
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        url = reverse("ingredient-adjust", args=[ingredient.id])
        response = api_client_staff.post(
            url, {"adjustment": "50.00", "action": "add"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("150.00")

    def test_adjust_inventory_subtract(self, api_client_staff, db):
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        url = reverse("ingredient-adjust", args=[ingredient.id])
        response = api_client_staff.post(
            url, {"adjustment": "30.00", "action": "subtract"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("70.00")

    def test_adjust_inventory_subtract_insufficient(self, api_client_staff, db):
        ingredient = IngredientFactory(quantity_available=Decimal("10.00"))
        url = reverse("ingredient-adjust", args=[ingredient.id])
        response = api_client_staff.post(
            url, {"adjustment": "50.00", "action": "subtract"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_adjust_inventory_invalid_amount(self, api_client_staff, db):
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        url = reverse("ingredient-adjust", args=[ingredient.id])
        response = api_client_staff.post(
            url, {"adjustment": "-10.00", "action": "add"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_adjust_inventory_updates_dish_availability(self, api_client_admin, db):
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        dish = DishFactory(is_available=True)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("50.00")
        )
        url = reverse("ingredient-adjust", args=[ingredient.id])
        api_client_admin.post(
            url, {"adjustment": "90.00", "action": "subtract"}, format="json"
        )
        dish.refresh_from_db()
        assert dish.is_available is False


# =============================================================================
# Dish API
# =============================================================================


class TestDishAPI:
    """Tests for the Dish API endpoints."""

    def test_list_dishes_requires_auth(self, api_client, db):
        url = reverse("dish-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_dishes_as_staff(self, api_client_staff, db):
        DishFactory.create_batch(3)
        url = reverse("dish-list")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_retrieve_dish(self, api_client_staff, db):
        dish = DishFactory(name="Pizza")
        url = reverse("dish-detail", args=[dish.id])
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Pizza"
        assert "recipe_requirements" in response.data
        assert "calculated_cost" in response.data

    def test_create_dish_as_staff_without_price_fails(self, api_client_staff, db):
        """Staff cannot create a dish without price (required field)."""
        url = reverse("dish-list")
        response = api_client_staff.post(
            url,
            {"name": "Pasta", "description": "Italian pasta"},
            format="json",
        )
        # price is required by serializer, so 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_dish_with_price_denied_for_staff(self, api_client_staff, db):
        """Staff cannot include price in request data."""
        url = reverse("dish-list")
        response = api_client_staff.post(
            url,
            {"name": "Pasta", "description": "Italian pasta", "price": "12.00"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_dish_as_admin_with_price(self, api_client_admin, db):
        url = reverse("dish-list")
        response = api_client_admin.post(
            url,
            {"name": "Burger", "description": "Beef burger", "price": "15.00"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_dish_as_admin(self, api_client_admin, db):
        dish = DishFactory()
        url = reverse("dish-detail", args=[dish.id])
        response = api_client_admin.put(
            url,
            {
                "name": "Updated Dish",
                "description": "Updated desc",
                "price": "20.00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        dish.refresh_from_db()
        assert dish.name == "Updated Dish"

    def test_partial_update_dish(self, api_client_admin, db):
        dish = DishFactory(name="Old Name")
        url = reverse("dish-detail", args=[dish.id])
        response = api_client_admin.patch(url, {"name": "New Name"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        dish.refresh_from_db()
        assert dish.name == "New Name"

    def test_delete_dish(self, api_client_admin, db):
        dish = DishFactory()
        url = reverse("dish-detail", args=[dish.id])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_available_dishes_action(self, api_client_staff, db):
        DishFactory(is_available=True, name="Available")
        DishFactory(is_available=False, name="Unavailable")
        url = reverse("dish-available")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Available"

    def test_add_requirement(self, api_client_admin, db):
        dish = DishFactory()
        ingredient = IngredientFactory(
            price_per_unit=Decimal("2.00"),
            quantity_available=Decimal("100.00"),
        )
        url = reverse("dish-add-requirement", args=[dish.id])
        response = api_client_admin.post(
            url,
            {"ingredient": ingredient.id, "quantity_required": "10.00"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert RecipeRequirement.objects.filter(
            dish=dish, ingredient=ingredient
        ).exists()

    def test_add_requirement_updates_existing(self, api_client_admin, db):
        dish = DishFactory()
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("5.00")
        )
        url = reverse("dish-add-requirement", args=[dish.id])
        response = api_client_admin.post(
            url,
            {"ingredient": ingredient.id, "quantity_required": "20.00"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        req = RecipeRequirement.objects.get(dish=dish, ingredient=ingredient)
        assert req.quantity_required == Decimal("20.00")

    def test_remove_requirement(self, api_client_admin, db):
        dish = DishFactory()
        req = RecipeRequirementFactory(dish=dish)
        url = reverse("dish-remove-requirement", args=[dish.id, req.id])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert not RecipeRequirement.objects.filter(id=req.id).exists()

    def test_remove_requirement_not_found(self, api_client_admin, db):
        dish = DishFactory()
        url = reverse("dish-remove-requirement", args=[dish.id, 99999])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Menu API
# =============================================================================


class TestMenuAPI:
    """Tests for the Menu API endpoints."""

    def test_list_menus_requires_auth(self, api_client, db):
        url = reverse("menu-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_menus_as_staff(self, api_client_staff, db):
        MenuFactory.create_batch(2)
        url = reverse("menu-list")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert "dish_count" in response.data["results"][0]

    def test_retrieve_menu(self, api_client_staff, db):
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])
        url = reverse("menu-detail", args=[menu.id])
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == menu.name
        assert "dishes" in response.data
        assert "calculated_cost" in response.data

    def test_create_menu_as_admin(self, api_client_admin, db):
        url = reverse("menu-list")
        response = api_client_admin.post(
            url,
            {
                "name": "Lunch Special",
                "description": "Great deal",
                "price": "15.00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        menu = Menu.objects.get(name="Lunch Special")
        assert menu.cost == Decimal("0")
        assert menu.is_available is False

    def test_create_menu_with_dishes(self, api_client_admin, db):
        dish1 = DishFactory(cost=Decimal("5.00"))
        dish2 = DishFactory(cost=Decimal("7.00"))
        url = reverse("menu-list")
        response = api_client_admin.post(
            url,
            {
                "name": "Combo",
                "description": "Two dishes",
                "price": "20.00",
                "dish_ids": [dish1.id, dish2.id],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_menu(self, api_client_admin, db):
        menu = MenuFactory()
        url = reverse("menu-detail", args=[menu.id])
        response = api_client_admin.put(
            url,
            {
                "name": "Updated Menu",
                "description": "Updated",
                "price": "25.00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        menu.refresh_from_db()
        assert menu.name == "Updated Menu"

    def test_add_dish_to_menu(self, api_client_admin, db):
        menu = MenuFactory()
        dish = DishFactory()
        url = reverse("menu-add-dish", args=[menu.id, dish.id])
        response = api_client_admin.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert dish in menu.dishes.all()

    def test_add_nonexistent_dish_to_menu(self, api_client_admin, db):
        menu = MenuFactory()
        url = reverse("menu-add-dish", args=[menu.id, 99999])
        response = api_client_admin.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_dish_from_menu(self, api_client_admin, db):
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])
        url = reverse("menu-remove-dish", args=[menu.id, dish.id])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert dish not in menu.dishes.all()

    def test_remove_nonexistent_dish_from_menu(self, api_client_admin, db):
        menu = MenuFactory()
        url = reverse("menu-remove-dish", args=[menu.id, 99999])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_menu(self, api_client_admin, db):
        menu = MenuFactory()
        url = reverse("menu-detail", args=[menu.id])
        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# Purchase API
# =============================================================================


class TestPurchaseAPI:
    """Tests for the Purchase API endpoints."""

    def test_list_purchases_requires_auth(self, api_client, db):
        url = reverse("purchase-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_purchases_admin_sees_all(self, api_client_admin, admin_user, db):
        other_user = UserFactory()
        PurchaseFactory(user=admin_user)
        PurchaseFactory(user=other_user)
        url = reverse("purchase-list")
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_purchases_staff_sees_own(self, api_client_staff, staff_user, db):
        other_user = UserFactory()
        PurchaseFactory(user=staff_user)
        PurchaseFactory(user=other_user)
        url = reverse("purchase-list")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_retrieve_purchase(self, api_client_admin, admin_user, db):
        purchase = PurchaseFactory(user=admin_user)
        PurchaseItemFactory(purchase=purchase)
        url = reverse("purchase-detail", args=[purchase.id])
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.data
        assert "user" in response.data

    def test_create_purchase_success(self, api_client_admin, db):
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("5.00")
        )
        url = reverse("purchase-list")
        response = api_client_admin.post(
            url,
            {
                "items": [{"dish_id": dish.id, "quantity": 2}],
                "notes": "Test purchase",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Purchase.objects.count() == 1
        purchase = Purchase.objects.first()
        assert purchase.total_price_at_purchase == Decimal("20.00")
        assert purchase.notes == "Test purchase"

    def test_create_purchase_deducts_inventory(self, api_client_admin, db):
        ingredient = IngredientFactory(quantity_available=Decimal("100.00"))
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("10.00")
        )
        url = reverse("purchase-list")
        api_client_admin.post(
            url,
            {"items": [{"dish_id": dish.id, "quantity": 3}]},
            format="json",
        )
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal("70.00")

    def test_create_purchase_unavailable_dish(self, api_client_admin, db):
        dish = DishFactory(is_available=False, price=Decimal("10.00"))
        url = reverse("purchase-list")
        response = api_client_admin.post(
            url,
            {"items": [{"dish_id": dish.id, "quantity": 1}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_purchase_insufficient_ingredients(self, api_client_admin, db):
        ingredient = IngredientFactory(quantity_available=Decimal("5.00"))
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("10.00")
        )
        url = reverse("purchase-list")
        response = api_client_admin.post(
            url,
            {"items": [{"dish_id": dish.id, "quantity": 1}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_create_purchase_empty_items(self, api_client_admin, db):
        url = reverse("purchase-list")
        response = api_client_admin.post(
            url,
            {"items": []},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_purchase_multiple_items(self, api_client_admin, db):
        ingredient1 = IngredientFactory(quantity_available=Decimal("100.00"))
        ingredient2 = IngredientFactory(quantity_available=Decimal("100.00"))
        dish1 = DishFactory(is_available=True, price=Decimal("10.00"))
        dish2 = DishFactory(is_available=True, price=Decimal("15.00"))
        RecipeRequirementFactory(
            dish=dish1, ingredient=ingredient1, quantity_required=Decimal("5.00")
        )
        RecipeRequirementFactory(
            dish=dish2, ingredient=ingredient2, quantity_required=Decimal("3.00")
        )
        url = reverse("purchase-list")
        response = api_client_admin.post(
            url,
            {
                "items": [
                    {"dish_id": dish1.id, "quantity": 2},
                    {"dish_id": dish2.id, "quantity": 1},
                ],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        purchase = Purchase.objects.first()
        assert purchase.items.count() == 2
        assert purchase.total_price_at_purchase == Decimal("35.00")

    def test_purchase_updates_dish_availability(self, api_client_admin, db):
        ingredient = IngredientFactory(quantity_available=Decimal("15.00"))
        dish = DishFactory(is_available=True, price=Decimal("10.00"))
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("10.00")
        )
        url = reverse("purchase-list")
        api_client_admin.post(
            url,
            {"items": [{"dish_id": dish.id, "quantity": 1}]},
            format="json",
        )
        dish.refresh_from_db()
        # Only 5 left, need 10 -> unavailable
        assert dish.is_available is False

    def test_purchase_no_update_or_delete(self, api_client_admin, admin_user, db):
        purchase = PurchaseFactory(user=admin_user)
        url = reverse("purchase-detail", args=[purchase.id])
        response = api_client_admin.put(
            url,
            {"notes": "updated"},
            format="json",
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = api_client_admin.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# =============================================================================
# Dashboard API
# =============================================================================


class TestDashboardAPI:
    """Tests for the Dashboard API endpoint."""

    def test_dashboard_requires_admin(self, api_client_staff, db):
        url = reverse("api-dashboard")
        response = api_client_staff.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_requires_auth(self, api_client, db):
        url = reverse("api-dashboard")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_returns_metrics(self, api_client_admin, admin_user, db):
        dish = DishFactory(cost=Decimal("5.00"), price=Decimal("10.00"))
        purchase = PurchaseFactory(
            user=admin_user,
            total_price_at_purchase=Decimal("20.00"),
            status=Purchase.STATUS_COMPLETED,
        )
        PurchaseItemFactory(
            purchase=purchase,
            dish=dish,
            quantity=2,
            price_at_purchase=Decimal("10.00"),
            subtotal=Decimal("20.00"),
        )
        url = reverse("api-dashboard")
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "total_revenue" in response.data
        assert "total_cost" in response.data
        assert "total_profit" in response.data
        assert "total_purchases" in response.data
        assert "top_dishes" in response.data
        assert "low_stock_ingredients" in response.data

    def test_dashboard_empty_data(self, api_client_admin, db):
        url = reverse("api-dashboard")
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_revenue"] == "0.00"
        assert response.data["total_purchases"] == 0

    def test_dashboard_low_stock_ingredients(self, api_client_admin, db):
        IngredientFactory(name="Low Stock", quantity_available=Decimal("5.00"))
        IngredientFactory(name="High Stock", quantity_available=Decimal("500.00"))
        url = reverse("api-dashboard")
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        low_stock = response.data["low_stock_ingredients"]
        assert len(low_stock) == 1

    def test_dashboard_cancelled_purchases_excluded(
        self, api_client_admin, admin_user, db
    ):
        PurchaseFactory(
            user=admin_user,
            total_price_at_purchase=Decimal("50.00"),
            status=Purchase.STATUS_CANCELLED,
        )
        url = reverse("api-dashboard")
        response = api_client_admin.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_revenue"] == "0.00"
        assert response.data["total_purchases"] == 0
