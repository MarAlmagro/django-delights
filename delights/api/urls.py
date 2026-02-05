"""
URL configuration for Django Delights REST API.

Provides endpoints for all models with versioning (v1).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    DashboardView,
    DishViewSet,
    HealthCheckView,
    IngredientViewSet,
    MenuViewSet,
    PurchaseViewSet,
    UnitViewSet,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"ingredients", IngredientViewSet, basename="ingredient")
router.register(r"dishes", DishViewSet, basename="dish")
router.register(r"menus", MenuViewSet, basename="menu")
router.register(r"purchases", PurchaseViewSet, basename="purchase")

# API URL patterns
urlpatterns = [
    # Health check (no auth required)
    path("health/", HealthCheckView.as_view(), name="api-health"),
    # JWT Authentication
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Dashboard (admin only)
    path("dashboard/", DashboardView.as_view(), name="api-dashboard"),
    # ViewSet routes
    path("", include(router.urls)),
]
