"""
Tests for custom API permissions in Django Delights.

Tests cover all permission classes: IsAdminUser, IsAdminOrReadOnly,
IsStaffOrAdmin, IsOwnerOrAdmin, and CanEditPrice.
"""

import pytest
from django.test import RequestFactory
from rest_framework.test import force_authenticate

from delights.api.permissions import (
    CanEditPrice,
    IsAdminOrReadOnly,
    IsAdminUser,
    IsOwnerOrAdmin,
    IsStaffOrAdmin,
)
from delights.tests.factories import (
    PurchaseFactory,
    UserFactory,
)


@pytest.fixture
def rf():
    """Return a Django RequestFactory."""
    return RequestFactory()


@pytest.fixture
def regular(db):
    return UserFactory(is_staff=False, is_superuser=False)


@pytest.fixture
def staff(db):
    user = UserFactory()
    user.is_staff = True
    user.is_superuser = False
    user.save()
    return user


@pytest.fixture
def superuser(db):
    user = UserFactory()
    user.is_staff = True
    user.is_superuser = True
    user.save()
    return user


class TestIsAdminUser:
    """Tests for IsAdminUser permission."""

    def test_anonymous_denied(self, rf):
        perm = IsAdminUser()
        request = rf.get("/")
        request.user = None
        assert perm.has_permission(request, None) is False

    def test_regular_user_denied(self, rf, regular):
        perm = IsAdminUser()
        request = rf.get("/")
        request.user = regular
        assert perm.has_permission(request, None) is False

    def test_staff_user_denied(self, rf, staff):
        perm = IsAdminUser()
        request = rf.get("/")
        request.user = staff
        assert perm.has_permission(request, None) is False

    def test_superuser_allowed(self, rf, superuser):
        perm = IsAdminUser()
        request = rf.get("/")
        request.user = superuser
        assert perm.has_permission(request, None) is True


class TestIsAdminOrReadOnly:
    """Tests for IsAdminOrReadOnly permission."""

    def test_anonymous_denied(self, rf):
        perm = IsAdminOrReadOnly()
        request = rf.get("/")
        request.user = None
        assert perm.has_permission(request, None) is False

    def test_regular_user_read_allowed(self, rf, regular):
        perm = IsAdminOrReadOnly()
        request = rf.get("/")
        request.user = regular
        assert perm.has_permission(request, None) is True

    def test_regular_user_write_denied(self, rf, regular):
        perm = IsAdminOrReadOnly()
        request = rf.post("/")
        request.user = regular
        assert perm.has_permission(request, None) is False

    def test_staff_user_read_allowed(self, rf, staff):
        perm = IsAdminOrReadOnly()
        request = rf.get("/")
        request.user = staff
        assert perm.has_permission(request, None) is True

    def test_staff_user_write_denied(self, rf, staff):
        perm = IsAdminOrReadOnly()
        request = rf.post("/")
        request.user = staff
        assert perm.has_permission(request, None) is False

    def test_superuser_write_allowed(self, rf, superuser):
        perm = IsAdminOrReadOnly()
        request = rf.post("/")
        request.user = superuser
        assert perm.has_permission(request, None) is True


class TestIsStaffOrAdmin:
    """Tests for IsStaffOrAdmin permission."""

    def test_anonymous_denied(self, rf):
        perm = IsStaffOrAdmin()
        request = rf.get("/")
        request.user = None
        assert perm.has_permission(request, None) is False

    def test_regular_user_denied(self, rf, regular):
        perm = IsStaffOrAdmin()
        request = rf.get("/")
        request.user = regular
        assert perm.has_permission(request, None) is False

    def test_staff_user_allowed(self, rf, staff):
        perm = IsStaffOrAdmin()
        request = rf.get("/")
        request.user = staff
        assert perm.has_permission(request, None) is True

    def test_superuser_allowed(self, rf, superuser):
        perm = IsStaffOrAdmin()
        request = rf.get("/")
        request.user = superuser
        assert perm.has_permission(request, None) is True


class TestIsOwnerOrAdmin:
    """Tests for IsOwnerOrAdmin permission."""

    def test_anonymous_denied(self, rf):
        perm = IsOwnerOrAdmin()
        request = rf.get("/")
        request.user = None
        assert perm.has_permission(request, None) is False

    def test_authenticated_user_has_permission(self, rf, regular):
        perm = IsOwnerOrAdmin()
        request = rf.get("/")
        request.user = regular
        assert perm.has_permission(request, None) is True

    def test_owner_has_object_permission(self, rf, regular):
        perm = IsOwnerOrAdmin()
        request = rf.get("/")
        request.user = regular
        purchase = PurchaseFactory(user=regular)
        assert perm.has_object_permission(request, None, purchase) is True

    def test_non_owner_denied_object_permission(self, rf, regular):
        perm = IsOwnerOrAdmin()
        request = rf.get("/")
        request.user = regular
        other_user = UserFactory()
        purchase = PurchaseFactory(user=other_user)
        assert perm.has_object_permission(request, None, purchase) is False

    def test_superuser_has_object_permission(self, rf, superuser):
        perm = IsOwnerOrAdmin()
        request = rf.get("/")
        request.user = superuser
        other_user = UserFactory()
        purchase = PurchaseFactory(user=other_user)
        assert perm.has_object_permission(request, None, purchase) is True

    def test_object_without_user_field_denied(self, rf, regular):
        perm = IsOwnerOrAdmin()
        request = rf.get("/")
        request.user = regular

        class NoUserObj:
            pass

        assert perm.has_object_permission(request, None, NoUserObj()) is False


class TestCanEditPrice:
    """Tests for CanEditPrice permission."""

    def test_anonymous_denied(self, rf):
        perm = CanEditPrice()
        request = rf.get("/")
        request.user = None
        assert perm.has_permission(request, None) is False

    def test_read_allowed_for_authenticated(self, rf, regular):
        perm = CanEditPrice()
        request = rf.get("/")
        request.user = regular
        assert perm.has_permission(request, None) is True

    def test_staff_write_without_price_allowed(self, rf, staff):
        perm = CanEditPrice()
        request = rf.post("/", data={"name": "Dish"}, content_type="application/json")
        request.user = staff
        request.data = {"name": "Dish"}
        assert perm.has_permission(request, None) is True

    def test_staff_write_with_price_denied(self, rf, staff):
        perm = CanEditPrice()
        request = rf.post(
            "/", data={"name": "Dish", "price": "10.00"},
            content_type="application/json",
        )
        request.user = staff
        request.data = {"name": "Dish", "price": "10.00"}
        assert perm.has_permission(request, None) is False

    def test_admin_write_with_price_allowed(self, rf, superuser):
        perm = CanEditPrice()
        request = rf.post(
            "/", data={"name": "Dish", "price": "10.00"},
            content_type="application/json",
        )
        request.user = superuser
        request.data = {"name": "Dish", "price": "10.00"}
        assert perm.has_permission(request, None) is True

    def test_regular_user_write_denied(self, rf, regular):
        perm = CanEditPrice()
        request = rf.post("/", data={"name": "Dish"}, content_type="application/json")
        request.user = regular
        request.data = {"name": "Dish"}
        assert perm.has_permission(request, None) is False
