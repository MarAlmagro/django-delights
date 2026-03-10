"""
Performance tests for Django Delights.

These tests verify query optimization and performance improvements.
"""

import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.cache import cache

from delights.models import (
    Unit,
    Ingredient,
    Dish,
    RecipeRequirement,
    Purchase,
    PurchaseItem,
)


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="testpass123"
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    return User.objects.create_user(
        username="staff", email="staff@test.com", password="testpass123", is_staff=True
    )


@pytest.fixture
def client_logged_in_admin(client, admin_user):
    """Return a client logged in as admin."""
    client.login(username="admin", password="testpass123")
    return client


@pytest.fixture
def client_logged_in_staff(client, staff_user):
    """Return a client logged in as staff."""
    client.login(username="staff", password="testpass123")
    return client


@pytest.fixture
def sample_data(db, admin_user):
    """Create sample data for testing."""
    # Create units
    unit_g = Unit.objects.create(name="g", description="gram")
    unit_ml = Unit.objects.create(name="ml", description="milliliter")

    # Create ingredients
    flour = Ingredient.objects.create(
        name="Flour",
        unit=unit_g,
        price_per_unit=Decimal("0.01"),
        quantity_available=Decimal("1000"),
    )
    water = Ingredient.objects.create(
        name="Water",
        unit=unit_ml,
        price_per_unit=Decimal("0.001"),
        quantity_available=Decimal("2000"),
    )

    # Create dishes
    bread = Dish.objects.create(
        name="Bread", price=Decimal("5.00"), cost=Decimal("2.50"), is_available=True
    )
    RecipeRequirement.objects.create(
        dish=bread, ingredient=flour, quantity_required=Decimal("200")
    )
    RecipeRequirement.objects.create(
        dish=bread, ingredient=water, quantity_required=Decimal("100")
    )

    # Create purchases
    purchase = Purchase.objects.create(
        user=admin_user,
        total_price_at_purchase=Decimal("10.00"),
        status=Purchase.STATUS_COMPLETED,
    )
    PurchaseItem.objects.create(
        purchase=purchase,
        dish=bread,
        quantity=2,
        price_at_purchase=Decimal("5.00"),
        subtotal=Decimal("10.00"),
    )

    return {
        "unit_g": unit_g,
        "unit_ml": unit_ml,
        "flour": flour,
        "water": water,
        "bread": bread,
        "purchase": purchase,
    }


@pytest.mark.django_db
class TestDashboardPerformance:
    """Test dashboard query performance."""

    def test_dashboard_query_count(
        self, client_logged_in_admin, sample_data, django_assert_num_queries
    ):
        """Dashboard should execute limited queries with caching."""
        # Clear cache first
        cache.clear()

        # First request - should hit database
        with django_assert_num_queries(10):  # Allow up to 10 queries
            response = client_logged_in_admin.get("/dashboard/")
            assert response.status_code == 200

        # Second request - should use cache
        with django_assert_num_queries(2):  # Only session and user queries
            response = client_logged_in_admin.get("/dashboard/")
            assert response.status_code == 200

    def test_dashboard_cache_invalidation(self, client_logged_in_admin, sample_data):
        """Dashboard cache should invalidate on purchase changes."""
        cache.clear()

        # Prime the cache
        response = client_logged_in_admin.get("/dashboard/")
        assert response.status_code == 200
        assert cache.get("dashboard_metrics") is not None

        # Create a new purchase - should invalidate cache
        Purchase.objects.create(
            user=User.objects.get(username="admin"),
            total_price_at_purchase=Decimal("20.00"),
            status=Purchase.STATUS_COMPLETED,
        )

        # Cache should be cleared
        assert cache.get("dashboard_metrics") is None


@pytest.mark.django_db
class TestListViewPerformance:
    """Test list view query performance."""

    def test_ingredient_list_query_count(
        self, client_logged_in_staff, sample_data, django_assert_num_queries
    ):
        """Ingredient list should use select_related for units."""
        # Create more ingredients
        unit = sample_data["unit_g"]
        for i in range(10):
            Ingredient.objects.create(
                name=f"Ingredient {i}",
                unit=unit,
                price_per_unit=Decimal("1.00"),
                quantity_available=Decimal("100"),
            )

        # Should use select_related to avoid N+1
        with django_assert_num_queries(
            5
        ):  # Session, user, count, ingredients with unit
            response = client_logged_in_staff.get("/ingredients/")
            assert response.status_code == 200

    def test_dish_list_pagination(self, client_logged_in_staff, sample_data):
        """Dish list should be paginated."""
        # Create many dishes
        for i in range(25):
            Dish.objects.create(
                name=f"Dish {i}",
                price=Decimal("10.00"),
                cost=Decimal("5.00"),
                is_available=True,
            )

        response = client_logged_in_staff.get("/dishes/")
        assert response.status_code == 200

        # Should have pagination context
        assert "is_paginated" in response.context
        assert response.context["is_paginated"] is True
        assert response.context["paginator"].per_page == 20

    def test_purchase_list_query_optimization(
        self, client_logged_in_admin, sample_data, django_assert_num_queries
    ):
        """Purchase list should use select_related and prefetch_related."""
        # Create more purchases
        admin = User.objects.get(username="admin")
        dish = sample_data["bread"]

        for _ in range(5):
            purchase = Purchase.objects.create(
                user=admin,
                total_price_at_purchase=Decimal("15.00"),
                status=Purchase.STATUS_COMPLETED,
            )
            PurchaseItem.objects.create(
                purchase=purchase,
                dish=dish,
                quantity=3,
                price_at_purchase=Decimal("5.00"),
                subtotal=Decimal("15.00"),
            )

        # Should optimize queries with select_related and prefetch_related
        with django_assert_num_queries(
            6
        ):  # Session, user, count, purchases, users, items
            response = client_logged_in_admin.get("/purchases/")
            assert response.status_code == 200


@pytest.mark.django_db
class TestDatabaseIndexes:
    """Test that database indexes are properly created."""

    def test_dish_is_available_index(self, db):
        """Dish.is_available should have an index."""
        from django.db import connection

        with connection.cursor() as cursor:
            # Get table info
            cursor.execute("PRAGMA index_list('delights_dish')")
            indexes = cursor.fetchall()

            # Check if there's an index on is_available
            index_names = [idx[1] for idx in indexes]
            assert any("is_available" in name for name in index_names)

    def test_ingredient_quantity_index(self, db):
        """Ingredient.quantity_available should have an index."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA index_list('delights_ingredient')")
            indexes = cursor.fetchall()

            index_names = [idx[1] for idx in indexes]
            assert any("quantity_available" in name for name in index_names)

    def test_purchase_composite_indexes(self, db):
        """Purchase should have composite indexes."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA index_list('delights_purchase')")
            indexes = cursor.fetchall()

            # Should have indexes for status, timestamp, and composite indexes
            index_names = [idx[1] for idx in indexes]
            assert (
                len(
                    [
                        name
                        for name in index_names
                        if "status" in name or "timestamp" in name
                    ]
                )
                >= 2
            )


@pytest.mark.django_db
class TestBulkUpdateOptimization:
    """Test bulk update optimizations in availability service."""

    def test_update_dishes_for_ingredient_uses_bulk(
        self, sample_data, django_assert_num_queries
    ):
        """update_dishes_for_ingredient should use bulk_update."""
        from delights.services.availability import update_dishes_for_ingredient

        # Create multiple dishes using the same ingredient
        flour = sample_data["flour"]
        dishes = []
        for idx in range(5):
            dish = Dish.objects.create(
                name=f"Bread {idx}",
                price=Decimal("5.00"),
                cost=Decimal("2.50"),
                is_available=True,
            )
            RecipeRequirement.objects.create(
                dish=dish, ingredient=flour, quantity_required=Decimal("200")
            )
            dishes.append(dish)

        # Update should use bulk_update (fewer queries than individual saves)
        with django_assert_num_queries(
            5
        ):  # Query dishes, prefetch, pricing queries, bulk update
            update_dishes_for_ingredient(flour)
