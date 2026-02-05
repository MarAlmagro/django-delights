"""
Pytest configuration and fixtures for Django Delights tests.

This module provides shared fixtures and configuration for the test suite.
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from delights.models import (
    Dish,
    Ingredient,
    Menu,
    Purchase,
    PurchaseItem,
    RecipeRequirement,
    Unit,
)


@pytest.fixture
def unit_gram(db):
    """Create a gram unit."""
    return Unit.objects.create(name="g", description="gram", is_active=True)


@pytest.fixture
def unit_liter(db):
    """Create a liter unit."""
    return Unit.objects.create(name="l", description="liter", is_active=True)


@pytest.fixture
def unit_each(db):
    """Create an 'each' unit for countable items."""
    return Unit.objects.create(name="ea", description="each", is_active=True)


@pytest.fixture
def ingredient_flour(db, unit_gram):
    """Create a flour ingredient."""
    return Ingredient.objects.create(
        name="Flour",
        unit=unit_gram,
        price_per_unit=Decimal("0.50"),
        quantity_available=Decimal("1000.00"),
    )


@pytest.fixture
def ingredient_sugar(db, unit_gram):
    """Create a sugar ingredient."""
    return Ingredient.objects.create(
        name="Sugar",
        unit=unit_gram,
        price_per_unit=Decimal("0.75"),
        quantity_available=Decimal("500.00"),
    )


@pytest.fixture
def ingredient_milk(db, unit_liter):
    """Create a milk ingredient."""
    return Ingredient.objects.create(
        name="Milk",
        unit=unit_liter,
        price_per_unit=Decimal("2.00"),
        quantity_available=Decimal("10.00"),
    )


@pytest.fixture
def dish_cookie(db):
    """Create a cookie dish without recipe requirements."""
    return Dish.objects.create(
        name="Cookie",
        description="A delicious chocolate chip cookie",
        cost=Decimal("0.00"),
        price=Decimal("2.50"),
        is_available=False,
    )


@pytest.fixture
def dish_with_recipe(db, dish_cookie, ingredient_flour, ingredient_sugar):
    """Create a dish with recipe requirements."""
    RecipeRequirement.objects.create(
        dish=dish_cookie,
        ingredient=ingredient_flour,
        quantity_required=Decimal("100.00"),
    )
    RecipeRequirement.objects.create(
        dish=dish_cookie,
        ingredient=ingredient_sugar,
        quantity_required=Decimal("50.00"),
    )
    return dish_cookie


@pytest.fixture
def menu_combo(db, dish_cookie):
    """Create a combo menu."""
    menu = Menu.objects.create(
        name="Cookie Combo",
        description="A combo with cookies",
        cost=Decimal("0.00"),
        price=Decimal("5.00"),
        is_available=False,
    )
    menu.dishes.add(dish_cookie)
    return menu


@pytest.fixture
def admin_user(db):
    """Create an admin user (superuser)."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user (non-superuser)."""
    user = User.objects.create_user(
        username="staff",
        email="staff@example.com",
        password="staffpass123",
    )
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def regular_user(db):
    """Create a regular user."""
    return User.objects.create_user(
        username="user",
        email="user@example.com",
        password="userpass123",
    )


@pytest.fixture
def purchase(db, admin_user, dish_cookie):
    """Create a completed purchase."""
    purchase = Purchase.objects.create(
        user=admin_user,
        total_price_at_purchase=Decimal("2.50"),
        status=Purchase.STATUS_COMPLETED,
    )
    PurchaseItem.objects.create(
        purchase=purchase,
        dish=dish_cookie,
        quantity=1,
        price_at_purchase=Decimal("2.50"),
        subtotal=Decimal("2.50"),
    )
    return purchase


@pytest.fixture
def client_logged_in_admin(client, admin_user):
    """Return a client logged in as admin."""
    client.login(username="admin", password="adminpass123")
    return client


@pytest.fixture
def client_logged_in_staff(client, staff_user):
    """Return a client logged in as staff."""
    client.login(username="staff", password="staffpass123")
    return client


@pytest.fixture
def api_client():
    """Return a DRF API test client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def api_client_admin(api_client, admin_user):
    """Return an API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def api_client_staff(api_client, staff_user):
    """Return an API client authenticated as staff."""
    api_client.force_authenticate(user=staff_user)
    return api_client
