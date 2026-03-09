"""
Django REST Framework serializers for Django Delights.

Serializers convert model instances to JSON and validate incoming data.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import serializers

from delights.models import (
    Dish,
    Ingredient,
    Menu,
    Purchase,
    PurchaseItem,
    RecipeRequirement,
    Unit,
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (read-only, excludes sensitive fields)."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_superuser", "date_joined"]
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "is_staff"]

    def validate(self, data):
        """Validate that passwords match."""
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for Unit model."""

    class Meta:
        model = Unit
        fields = ["id", "name", "description", "is_active"]


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""

    unit = UnitSerializer(read_only=True)
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_active=True),
        source="unit",
        write_only=True,
    )

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "unit",
            "unit_id",
            "price_per_unit",
            "quantity_available",
        ]


class IngredientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for ingredient lists."""

    unit_name = serializers.CharField(source="unit.name", read_only=True)

    class Meta:
        model = Ingredient
        fields = ["id", "name", "unit_name", "price_per_unit", "quantity_available"]


class RecipeRequirementSerializer(serializers.ModelSerializer):
    """Serializer for RecipeRequirement model."""

    ingredient = IngredientListSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
        write_only=True,
    )

    class Meta:
        model = RecipeRequirement
        fields = ["id", "ingredient", "ingredient_id", "quantity_required"]


class RecipeRequirementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recipe requirements."""

    class Meta:
        model = RecipeRequirement
        fields = ["ingredient", "quantity_required"]


class DishSerializer(serializers.ModelSerializer):
    """Serializer for Dish model with recipe requirements."""

    recipe_requirements = RecipeRequirementSerializer(many=True, read_only=True)
    calculated_cost = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            "id",
            "name",
            "description",
            "cost",
            "calculated_cost",
            "price",
            "is_available",
            "recipe_requirements",
        ]
        read_only_fields = ["cost", "is_available"]

    def get_calculated_cost(self, obj):
        """Calculate cost from recipe requirements."""
        total = Decimal("0")
        for req in obj.recipe_requirements.all():
            total += req.ingredient.price_per_unit * req.quantity_required
        return str(total.quantize(Decimal("0.01")))


class DishListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dish lists."""

    class Meta:
        model = Dish
        fields = ["id", "name", "description", "cost", "price", "is_available"]


class DishCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating dishes."""

    class Meta:
        model = Dish
        fields = ["name", "description", "price"]


class MenuSerializer(serializers.ModelSerializer):
    """Serializer for Menu model with dishes."""

    dishes = DishListSerializer(many=True, read_only=True)
    dish_ids = serializers.PrimaryKeyRelatedField(
        queryset=Dish.objects.all(),
        source="dishes",
        many=True,
        write_only=True,
        required=False,
    )
    calculated_cost = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "description",
            "dishes",
            "dish_ids",
            "cost",
            "calculated_cost",
            "price",
            "is_available",
        ]
        read_only_fields = ["cost", "is_available"]

    def get_calculated_cost(self, obj):
        """Calculate cost from dishes."""
        total = sum((dish.cost for dish in obj.dishes.all()), Decimal("0"))
        return str(total.quantize(Decimal("0.01")))


class MenuListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for menu lists."""

    dish_count = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "description",
            "cost",
            "price",
            "is_available",
            "dish_count",
        ]

    def get_dish_count(self, obj):
        """Get number of dishes in menu."""
        return obj.dishes.count()


class PurchaseItemSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseItem model."""

    dish = DishListSerializer(read_only=True)
    dish_id = serializers.PrimaryKeyRelatedField(
        queryset=Dish.objects.filter(is_available=True),
        source="dish",
        write_only=True,
    )

    class Meta:
        model = PurchaseItem
        fields = [
            "id",
            "dish",
            "dish_id",
            "quantity",
            "price_at_purchase",
            "subtotal",
        ]
        read_only_fields = ["price_at_purchase", "subtotal"]


class PurchaseItemCreateSerializer(serializers.Serializer):
    """Serializer for creating purchase items."""

    dish_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class PurchaseSerializer(serializers.ModelSerializer):
    """Serializer for Purchase model with items."""

    items = PurchaseItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Purchase
        fields = [
            "id",
            "user",
            "timestamp",
            "total_price_at_purchase",
            "status",
            "notes",
            "items",
        ]
        read_only_fields = ["user", "timestamp", "total_price_at_purchase", "status"]


class PurchaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for purchase lists."""

    user = serializers.StringRelatedField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = [
            "id",
            "user",
            "timestamp",
            "total_price_at_purchase",
            "status",
            "item_count",
        ]

    def get_item_count(self, obj):
        """Get number of items in purchase."""
        return obj.items.count()


class PurchaseCreateSerializer(serializers.Serializer):
    """Serializer for creating a purchase with items."""

    items = PurchaseItemCreateSerializer(many=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_items(self, value):
        """Validate that items list is not empty."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


class InventoryAdjustmentSerializer(serializers.Serializer):
    """Serializer for adjusting inventory."""

    adjustment = serializers.DecimalField(max_digits=10, decimal_places=2)
    action = serializers.ChoiceField(choices=["add", "subtract"])

    def validate(self, data):
        """Validate adjustment amount."""
        if data["adjustment"] <= 0:
            raise serializers.ValidationError(
                {"adjustment": "Adjustment amount must be positive."}
            )
        return data


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard metrics."""

    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_purchases = serializers.IntegerField()
    top_dishes = serializers.ListField()
    low_stock_ingredients = serializers.ListField()
