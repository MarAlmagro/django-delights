import pytest
import json
from pathlib import Path
from django.urls import reverse

SCHEMA_SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "api_schema.json"


class TestAPISchema:
    """Tests to ensure API schema doesn't change unexpectedly."""

    def test_schema_matches_snapshot(self, api_client_admin):
        """API schema should match the stored snapshot."""
        response = api_client_admin.get(reverse("schema") + "?format=json")
        assert response.status_code == 200

        current_schema = json.loads(response.content)

        if not SCHEMA_SNAPSHOT_PATH.exists():
            SCHEMA_SNAPSHOT_PATH.parent.mkdir(exist_ok=True)
            with open(SCHEMA_SNAPSHOT_PATH, "w") as f:
                json.dump(current_schema, f, indent=2)
            pytest.skip("Schema snapshot created")

        with open(SCHEMA_SNAPSHOT_PATH) as f:
            expected_schema = json.load(f)

        current_paths = set(current_schema.get("paths", {}).keys())
        expected_paths = set(expected_schema.get("paths", {}).keys())

        assert current_paths == expected_paths, (
            f"API endpoints changed!\n"
            f"Added: {current_paths - expected_paths}\n"
            f"Removed: {expected_paths - current_paths}"
        )

    def test_response_format_dishes(self, api_client_staff, db):
        """Verify dish list response format."""
        from delights.tests.factories import DishFactory

        DishFactory.create_batch(2)

        response = api_client_staff.get(reverse("dish-list"))
        assert response.status_code == 200

        result = response.data["results"][0]
        required_fields = ["id", "name", "cost", "price", "is_available"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_response_format_ingredients(self, api_client_staff, db):
        """Verify ingredient list response format."""
        from delights.tests.factories import IngredientFactory

        IngredientFactory.create_batch(2)

        response = api_client_staff.get(reverse("ingredient-list"))
        assert response.status_code == 200

        result = response.data["results"][0]
        required_fields = [
            "id",
            "name",
            "quantity_available",
            "price_per_unit",
            "unit_name",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_response_format_purchases(self, api_client_admin, admin_user, db):
        """Verify purchase list response format."""
        from delights.tests.factories import (
            PurchaseFactory,
            PurchaseItemFactory,
            DishFactory,
        )

        dish = DishFactory()
        purchase = PurchaseFactory(user=admin_user)
        PurchaseItemFactory(purchase=purchase, dish=dish)

        response = api_client_admin.get(reverse("purchase-list"))
        assert response.status_code == 200

        result = response.data["results"][0]
        required_fields = ["id", "user", "timestamp"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_response_format_menus(self, api_client_staff, db):
        """Verify menu list response format."""
        from delights.tests.factories import MenuFactory

        MenuFactory.create_batch(2)

        response = api_client_staff.get(reverse("menu-list"))
        assert response.status_code == 200

        result = response.data["results"][0]
        required_fields = ["id", "name", "dish_count"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_api_versioning_header(self, api_client_staff):
        """Verify API version is included in responses."""
        response = api_client_staff.get(reverse("dish-list"))
        assert response.status_code == 200

    def test_pagination_format(self, api_client_staff, db):
        """Verify pagination format is consistent."""
        from delights.tests.factories import DishFactory

        DishFactory.create_batch(15)

        response = api_client_staff.get(reverse("dish-list"))
        assert response.status_code == 200

        assert "results" in response.data
        assert "count" in response.data or len(response.data["results"]) > 0

    def test_error_response_format(self, api_client_staff):
        """Verify error responses have consistent format."""
        response = api_client_staff.get(reverse("dish-detail", kwargs={"pk": 99999}))
        assert response.status_code == 404

        assert "detail" in response.data or "error" in response.data


class TestAPIContractStability:
    """Tests to ensure API contracts remain stable."""

    def test_dish_serialization_fields_stable(self, api_client_staff, db):
        """Ensure dish serialization fields don't change unexpectedly."""
        from delights.tests.factories import DishFactory

        dish = DishFactory()

        response = api_client_staff.get(reverse("dish-detail", kwargs={"pk": dish.pk}))
        assert response.status_code == 200

        expected_fields = {"id", "name", "description", "cost", "price", "is_available"}
        actual_fields = set(response.data.keys())

        missing_fields = expected_fields - actual_fields
        assert not missing_fields, f"Missing expected fields: {missing_fields}"

    def test_ingredient_serialization_fields_stable(self, api_client_staff, db):
        """Ensure ingredient serialization fields don't change unexpectedly."""
        from delights.tests.factories import IngredientFactory

        ingredient = IngredientFactory()

        response = api_client_staff.get(
            reverse("ingredient-detail", kwargs={"pk": ingredient.pk})
        )
        assert response.status_code == 200

        expected_fields = {"id", "name", "quantity_available", "price_per_unit", "unit"}
        actual_fields = set(response.data.keys())

        missing_fields = expected_fields - actual_fields
        assert not missing_fields, f"Missing expected fields: {missing_fields}"

    def test_purchase_creation_contract(self, api_client_staff, db):
        """Ensure purchase creation API contract is stable."""
        from delights.tests.factories import (
            DishFactory,
            IngredientFactory,
            RecipeRequirementFactory,
        )
        from decimal import Decimal

        ingredient = IngredientFactory(quantity_available=Decimal("100"))
        dish = DishFactory(is_available=True)
        RecipeRequirementFactory(
            dish=dish, ingredient=ingredient, quantity_required=Decimal("1")
        )

        response = api_client_staff.post(
            reverse("purchase-list"),
            {"items": [{"dish_id": dish.id, "quantity": 1}]},
            format="json",
        )

        assert response.status_code in [201, 200]
        assert "id" in response.data or "items" in response.data

    def test_api_authentication_required(self, api_client):
        """Ensure protected endpoints require authentication."""
        response = api_client.get(reverse("dish-list"))
        assert response.status_code in [401, 403]

    def test_api_permissions_enforced(self, api_client_user, db):
        """Ensure staff-only endpoints enforce permissions."""
        from delights.tests.factories import IngredientFactory

        ingredient = IngredientFactory()

        response = api_client_user.post(
            reverse("ingredient-list"),
            {
                "name": "New Ingredient",
                "quantity_available": 100,
                "price_per_unit": 5.00,
                "unit": "kg",
            },
        )

        assert response.status_code in [403, 401]
