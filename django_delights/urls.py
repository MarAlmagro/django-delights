"""
URL configuration for django_delights project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from delights.views import LoginView

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # Authentication
    path("accounts/login/", LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Web UI Routes
    path("units/", include("delights.urls", namespace="units")),
    path("ingredients/", include("delights.urls_ingredients", namespace="ingredients")),
    path("dishes/", include("delights.urls_dishes", namespace="dishes")),
    path("menus/", include("delights.urls_menus", namespace="menus")),
    path("purchases/", include("delights.urls_purchases", namespace="purchases")),
    path("dashboard/", include("delights.urls_dashboard", namespace="dashboard")),
    path("users/", include("delights.urls_users", namespace="users")),
    # REST API (v1)
    path("api/v1/", include("delights.api.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
