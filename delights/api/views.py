"""
Django REST Framework views for Django Delights API.

Provides CRUD operations and business logic for all models.
"""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from delights.models import (
    Dish,
    Ingredient,
    Menu,
    Purchase,
    PurchaseItem,
    RecipeRequirement,
    Unit,
)
from delights.views import (
    calculate_dish_cost,
    calculate_menu_cost,
    check_dish_availability,
    update_dish_availability,
    update_menu_availability,
)

from .permissions import (
    CanEditPrice,
    IsAdminOrReadOnly,
    IsAdminUser,
    IsOwnerOrAdmin,
    IsStaffOrAdmin,
)
from .serializers import (
    DashboardSerializer,
    DishCreateSerializer,
    DishListSerializer,
    DishSerializer,
    IngredientListSerializer,
    IngredientSerializer,
    InventoryAdjustmentSerializer,
    MenuListSerializer,
    MenuSerializer,
    PurchaseCreateSerializer,
    PurchaseListSerializer,
    PurchaseSerializer,
    RecipeRequirementCreateSerializer,
    RecipeRequirementSerializer,
    UnitSerializer,
    UserCreateSerializer,
    UserSerializer,
)


# =============================================================================
# Health Check
# =============================================================================


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Health check",
        description="Returns service health status",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
        tags=["health"],
    )
    def get(self, request):
        return Response({"status": "healthy"}, status=status.HTTP_200_OK)


# =============================================================================
# Unit ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List all units", tags=["units"]),
    retrieve=extend_schema(summary="Get unit details", tags=["units"]),
    create=extend_schema(summary="Create a new unit", tags=["units"]),
    update=extend_schema(summary="Update a unit", tags=["units"]),
    partial_update=extend_schema(summary="Partially update a unit", tags=["units"]),
)
class UnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing units of measurement.
    Admin only for create/update/delete operations.
    """

    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(summary="Toggle unit active status", tags=["units"])
    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a unit."""
        unit = self.get_object()
        unit.is_active = not unit.is_active
        unit.save()
        return Response(UnitSerializer(unit).data)


# =============================================================================
# Ingredient ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List all ingredients", tags=["ingredients"]),
    retrieve=extend_schema(summary="Get ingredient details", tags=["ingredients"]),
    create=extend_schema(summary="Create a new ingredient", tags=["ingredients"]),
    update=extend_schema(summary="Update an ingredient", tags=["ingredients"]),
    partial_update=extend_schema(summary="Partially update an ingredient", tags=["ingredients"]),
)
class IngredientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ingredients.
    Staff can view and adjust inventory.
    Admin can create/update/delete.
    """

    queryset = Ingredient.objects.select_related("unit").all()
    permission_classes = [IsStaffOrAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return IngredientListSerializer
        return IngredientSerializer

    @extend_schema(
        summary="Adjust ingredient inventory",
        request=InventoryAdjustmentSerializer,
        tags=["ingredients"],
    )
    @action(detail=True, methods=["post"])
    def adjust(self, request, pk=None):
        """Adjust the inventory quantity of an ingredient."""
        ingredient = self.get_object()
        serializer = InventoryAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        adjustment = serializer.validated_data["adjustment"]
        action_type = serializer.validated_data["action"]

        if action_type == "add":
            ingredient.quantity_available += adjustment
        else:
            if ingredient.quantity_available < adjustment:
                return Response(
                    {"error": "Insufficient quantity available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ingredient.quantity_available -= adjustment

        ingredient.save()

        # Update availability for affected dishes
        for req in ingredient.recipe_requirements.all():
            update_dish_availability(req.dish)

        return Response(IngredientSerializer(ingredient).data)


# =============================================================================
# Dish ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List all dishes", tags=["dishes"]),
    retrieve=extend_schema(summary="Get dish details", tags=["dishes"]),
    create=extend_schema(summary="Create a new dish", tags=["dishes"]),
    update=extend_schema(summary="Update a dish", tags=["dishes"]),
    partial_update=extend_schema(summary="Partially update a dish", tags=["dishes"]),
)
class DishViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dishes.
    Staff can create/edit dishes (except prices).
    Admin can edit prices.
    """

    queryset = Dish.objects.prefetch_related("recipe_requirements__ingredient").all()
    permission_classes = [CanEditPrice]

    def get_serializer_class(self):
        if self.action == "list":
            return DishListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return DishCreateSerializer
        return DishSerializer

    def perform_create(self, serializer):
        """Create dish with auto-calculated cost and availability."""
        dish = serializer.save(cost=Decimal("0"), is_available=False)
        return dish

    def perform_update(self, serializer):
        """Update dish and recalculate cost/availability."""
        dish = serializer.save()
        dish.cost = calculate_dish_cost(dish)
        dish.save()
        update_dish_availability(dish)
        return dish

    @extend_schema(
        summary="Add recipe requirement to dish",
        request=RecipeRequirementCreateSerializer,
        tags=["dishes"],
    )
    @action(detail=True, methods=["post"])
    def add_requirement(self, request, pk=None):
        """Add a recipe requirement to the dish."""
        dish = self.get_object()
        serializer = RecipeRequirementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requirement, created = RecipeRequirement.objects.get_or_create(
            dish=dish,
            ingredient=serializer.validated_data["ingredient"],
            defaults={"quantity_required": serializer.validated_data["quantity_required"]},
        )

        if not created:
            requirement.quantity_required = serializer.validated_data["quantity_required"]
            requirement.save()

        # Recalculate cost and availability
        dish.cost = calculate_dish_cost(dish)
        dish.save()
        update_dish_availability(dish)

        return Response(DishSerializer(dish).data)

    @extend_schema(summary="Remove recipe requirement from dish", tags=["dishes"])
    @action(detail=True, methods=["delete"], url_path="remove_requirement/(?P<req_id>[^/.]+)")
    def remove_requirement(self, request, pk=None, req_id=None):
        """Remove a recipe requirement from the dish."""
        dish = self.get_object()
        try:
            requirement = RecipeRequirement.objects.get(id=req_id, dish=dish)
            requirement.delete()

            # Recalculate cost and availability
            dish.cost = calculate_dish_cost(dish)
            dish.save()
            update_dish_availability(dish)

            return Response(DishSerializer(dish).data)
        except RecipeRequirement.DoesNotExist:
            return Response(
                {"error": "Requirement not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(summary="Get only available dishes", tags=["dishes"])
    @action(detail=False, methods=["get"])
    def available(self, request):
        """List only available dishes."""
        dishes = self.queryset.filter(is_available=True)
        serializer = DishListSerializer(dishes, many=True)
        return Response(serializer.data)


# =============================================================================
# Menu ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List all menus", tags=["menus"]),
    retrieve=extend_schema(summary="Get menu details", tags=["menus"]),
    create=extend_schema(summary="Create a new menu", tags=["menus"]),
    update=extend_schema(summary="Update a menu", tags=["menus"]),
    partial_update=extend_schema(summary="Partially update a menu", tags=["menus"]),
)
class MenuViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menus.
    Staff can create/edit menus (except prices).
    Admin can edit prices.
    """

    queryset = Menu.objects.prefetch_related("dishes").all()
    permission_classes = [CanEditPrice]

    def get_serializer_class(self):
        if self.action == "list":
            return MenuListSerializer
        return MenuSerializer

    def perform_create(self, serializer):
        """Create menu with auto-calculated cost and availability."""
        menu = serializer.save(cost=Decimal("0"), is_available=False)
        menu.cost = calculate_menu_cost(menu)
        menu.save()
        update_menu_availability(menu)
        return menu

    def perform_update(self, serializer):
        """Update menu and recalculate cost/availability."""
        menu = serializer.save()
        menu.cost = calculate_menu_cost(menu)
        menu.save()
        update_menu_availability(menu)
        return menu

    @extend_schema(summary="Add dish to menu", tags=["menus"])
    @action(detail=True, methods=["post"], url_path="add_dish/(?P<dish_id>[^/.]+)")
    def add_dish(self, request, pk=None, dish_id=None):
        """Add a dish to the menu."""
        menu = self.get_object()
        try:
            dish = Dish.objects.get(id=dish_id)
            menu.dishes.add(dish)

            # Recalculate cost and availability
            menu.cost = calculate_menu_cost(menu)
            menu.save()
            update_menu_availability(menu)

            return Response(MenuSerializer(menu).data)
        except Dish.DoesNotExist:
            return Response(
                {"error": "Dish not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(summary="Remove dish from menu", tags=["menus"])
    @action(detail=True, methods=["delete"], url_path="remove_dish/(?P<dish_id>[^/.]+)")
    def remove_dish(self, request, pk=None, dish_id=None):
        """Remove a dish from the menu."""
        menu = self.get_object()
        try:
            dish = Dish.objects.get(id=dish_id)
            menu.dishes.remove(dish)

            # Recalculate cost and availability
            menu.cost = calculate_menu_cost(menu)
            menu.save()
            update_menu_availability(menu)

            return Response(MenuSerializer(menu).data)
        except Dish.DoesNotExist:
            return Response(
                {"error": "Dish not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


# =============================================================================
# Purchase ViewSet
# =============================================================================


@extend_schema_view(
    list=extend_schema(summary="List purchases", tags=["purchases"]),
    retrieve=extend_schema(summary="Get purchase details", tags=["purchases"]),
    create=extend_schema(summary="Create a new purchase", tags=["purchases"]),
)
class PurchaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchases.
    Staff can view their own purchases.
    Admin can view all purchases.
    """

    permission_classes = [IsOwnerOrAdmin]
    http_method_names = ["get", "post", "head", "options"]  # No updates/deletes

    def get_queryset(self):
        """Filter purchases based on user role."""
        user = self.request.user
        if user.is_superuser:
            return Purchase.objects.select_related("user").prefetch_related("items__dish").all()
        return Purchase.objects.filter(user=user).prefetch_related("items__dish")

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseListSerializer
        if self.action == "create":
            return PurchaseCreateSerializer
        return PurchaseSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a purchase with atomic inventory deduction."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data["items"]
        notes = serializer.validated_data.get("notes", "")

        # Validate dishes and calculate total
        total_price = Decimal("0")
        validated_items = []

        for item_data in items_data:
            try:
                dish = Dish.objects.select_for_update().get(
                    id=item_data["dish_id"], is_available=True
                )
            except Dish.DoesNotExist:
                return Response(
                    {"error": f"Dish {item_data['dish_id']} not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check ingredient availability
            for req in dish.recipe_requirements.select_related("ingredient").all():
                ingredient = Ingredient.objects.select_for_update().get(id=req.ingredient.id)
                required = req.quantity_required * item_data["quantity"]
                if ingredient.quantity_available < required:
                    return Response(
                        {"error": f"Insufficient {ingredient.name} for {dish.name}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            subtotal = dish.price * item_data["quantity"]
            total_price += subtotal
            validated_items.append({
                "dish": dish,
                "quantity": item_data["quantity"],
                "price": dish.price,
                "subtotal": subtotal,
            })

        # Create purchase
        purchase = Purchase.objects.create(
            user=request.user,
            total_price_at_purchase=total_price,
            status=Purchase.STATUS_COMPLETED,
            notes=notes,
        )

        # Create items and deduct inventory
        for item in validated_items:
            PurchaseItem.objects.create(
                purchase=purchase,
                dish=item["dish"],
                quantity=item["quantity"],
                price_at_purchase=item["price"],
                subtotal=item["subtotal"],
            )

            # Deduct inventory
            for req in item["dish"].recipe_requirements.all():
                ingredient = Ingredient.objects.get(id=req.ingredient.id)
                ingredient.quantity_available -= req.quantity_required * item["quantity"]
                ingredient.save()

        # Update availability for all affected dishes
        for item in validated_items:
            update_dish_availability(item["dish"])

        return Response(
            PurchaseSerializer(purchase).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# Dashboard View
# =============================================================================


class DashboardView(APIView):
    """Dashboard with analytics and metrics."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Get dashboard metrics",
        responses={200: DashboardSerializer},
        tags=["dashboard"],
    )
    def get(self, request):
        """Get revenue, cost, profit, and other metrics."""
        # Calculate total revenue
        total_revenue = (
            Purchase.objects.filter(status=Purchase.STATUS_COMPLETED).aggregate(
                total=Sum("total_price_at_purchase")
            )["total"]
            or Decimal("0")
        )

        # Calculate total cost
        total_cost = Decimal("0")
        for item in PurchaseItem.objects.filter(
            purchase__status=Purchase.STATUS_COMPLETED
        ).select_related("dish"):
            total_cost += item.quantity * item.dish.cost

        # Calculate profit
        total_profit = total_revenue - total_cost

        # Total purchases
        total_purchases = Purchase.objects.filter(
            status=Purchase.STATUS_COMPLETED
        ).count()

        # Top selling dishes
        top_dishes = (
            PurchaseItem.objects.filter(purchase__status=Purchase.STATUS_COMPLETED)
            .values("dish__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        # Low stock ingredients (threshold from settings or default 10)
        threshold = getattr(settings, "LOW_STOCK_THRESHOLD", 10)
        low_stock = Ingredient.objects.filter(
            quantity_available__lt=threshold
        ).values("name", "quantity_available", "unit__name")

        data = {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "total_purchases": total_purchases,
            "top_dishes": list(top_dishes),
            "low_stock_ingredients": list(low_stock),
        }

        return Response(DashboardSerializer(data).data)
