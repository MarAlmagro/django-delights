"""
Factory Boy factories for Django Delights models.

These factories provide a convenient way to create test data with
sensible defaults and the ability to customize as needed.

Usage:
    from delights.tests.factories import DishFactory, IngredientFactory

    # Create with defaults
    dish = DishFactory()

    # Create with custom values
    dish = DishFactory(name="Custom Dish", price=Decimal("10.00"))

    # Create multiple
    dishes = DishFactory.create_batch(5)
"""

from decimal import Decimal

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from delights.models import (
    Dish,
    Ingredient,
    Menu,
    Purchase,
    PurchaseItem,
    RecipeRequirement,
    Unit,
)


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to handle password properly."""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class AdminUserFactory(UserFactory):
    """Factory for creating admin (superuser) instances."""

    is_staff = True
    is_superuser = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to use create_superuser."""
        manager = cls._get_manager(model_class)
        # Remove is_active as create_superuser doesn't accept it directly
        kwargs.pop("is_active", None)
        return manager.create_superuser(*args, **kwargs)


class StaffUserFactory(UserFactory):
    """Factory for creating staff (non-superuser) instances."""

    is_staff = True
    is_superuser = False


class UnitFactory(DjangoModelFactory):
    """Factory for creating Unit instances."""

    class Meta:
        model = Unit
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"unit{n}")
    description = factory.LazyAttribute(lambda obj: f"Description for {obj.name}")
    is_active = True


class GramUnitFactory(UnitFactory):
    """Factory for creating gram units."""

    name = "g"
    description = "gram"


class LiterUnitFactory(UnitFactory):
    """Factory for creating liter units."""

    name = "l"
    description = "liter"


class EachUnitFactory(UnitFactory):
    """Factory for creating 'each' units."""

    name = "ea"
    description = "each"


class IngredientFactory(DjangoModelFactory):
    """Factory for creating Ingredient instances."""

    class Meta:
        model = Ingredient

    name = factory.Sequence(lambda n: f"Ingredient {n}")
    unit = factory.SubFactory(GramUnitFactory)
    price_per_unit = Decimal("1.00")
    quantity_available = Decimal("100.00")


class DishFactory(DjangoModelFactory):
    """Factory for creating Dish instances."""

    class Meta:
        model = Dish

    name = factory.Sequence(lambda n: f"Dish {n}")
    description = factory.LazyAttribute(lambda obj: f"Description of {obj.name}")
    cost = Decimal("5.00")
    price = Decimal("7.50")
    is_available = True


class RecipeRequirementFactory(DjangoModelFactory):
    """Factory for creating RecipeRequirement instances."""

    class Meta:
        model = RecipeRequirement

    dish = factory.SubFactory(DishFactory)
    ingredient = factory.SubFactory(IngredientFactory)
    quantity_required = Decimal("10.00")


class MenuFactory(DjangoModelFactory):
    """Factory for creating Menu instances."""

    class Meta:
        model = Menu

    name = factory.Sequence(lambda n: f"Menu {n}")
    description = factory.LazyAttribute(lambda obj: f"Description of {obj.name}")
    cost = Decimal("15.00")
    price = Decimal("20.00")
    is_available = True

    @factory.post_generation
    def dishes(self, create, extracted, **kwargs):
        """Handle many-to-many dishes relationship."""
        if not create:
            return

        if extracted:
            for dish in extracted:
                self.dishes.add(dish)


class PurchaseFactory(DjangoModelFactory):
    """Factory for creating Purchase instances."""

    class Meta:
        model = Purchase

    user = factory.SubFactory(UserFactory)
    total_price_at_purchase = Decimal("10.00")
    status = Purchase.STATUS_COMPLETED
    notes = ""


class PurchaseItemFactory(DjangoModelFactory):
    """Factory for creating PurchaseItem instances."""

    class Meta:
        model = PurchaseItem

    purchase = factory.SubFactory(PurchaseFactory)
    dish = factory.SubFactory(DishFactory)
    quantity = 1
    price_at_purchase = Decimal("7.50")
    subtotal = factory.LazyAttribute(
        lambda obj: obj.quantity * obj.price_at_purchase
    )


class DishWithRecipeFactory(DishFactory):
    """Factory for creating a Dish with recipe requirements."""

    @factory.post_generation
    def ingredients(self, create, extracted, **kwargs):
        """Create recipe requirements for the dish."""
        if not create:
            return

        if extracted:
            # If ingredients are provided, create requirements for each
            for ingredient in extracted:
                RecipeRequirementFactory(
                    dish=self,
                    ingredient=ingredient,
                    quantity_required=Decimal("10.00"),
                )
        else:
            # Create default recipe with 2 ingredients
            RecipeRequirementFactory(
                dish=self,
                ingredient=IngredientFactory(name=f"{self.name} Ingredient 1"),
                quantity_required=Decimal("10.00"),
            )
            RecipeRequirementFactory(
                dish=self,
                ingredient=IngredientFactory(name=f"{self.name} Ingredient 2"),
                quantity_required=Decimal("5.00"),
            )


class CompletePurchaseFactory(PurchaseFactory):
    """Factory for creating a complete purchase with items."""

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        """Create purchase items."""
        if not create:
            return

        if extracted:
            total = Decimal("0.00")
            for item_data in extracted:
                item = PurchaseItemFactory(purchase=self, **item_data)
                total += item.subtotal
            self.total_price_at_purchase = total
            self.save()
        else:
            # Create a default item
            dish = DishFactory()
            item = PurchaseItemFactory(
                purchase=self,
                dish=dish,
                quantity=1,
                price_at_purchase=dish.price,
            )
            self.total_price_at_purchase = item.subtotal
            self.save()
