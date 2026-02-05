from django.contrib import admin
from .models import Unit, Ingredient, Dish, RecipeRequirement, Menu, Purchase, PurchaseItem


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'quantity_available', 'price_per_unit']
    list_filter = ['unit', 'unit__is_active']
    search_fields = ['name']
    raw_id_fields = ['unit']


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost', 'price', 'is_available']
    list_filter = ['is_available']
    search_fields = ['name', 'description']
    list_editable = ['is_available']


@admin.register(RecipeRequirement)
class RecipeRequirementAdmin(admin.ModelAdmin):
    list_display = ['dish', 'ingredient', 'quantity_required']
    list_filter = ['dish', 'ingredient']
    search_fields = ['dish__name', 'ingredient__name']
    raw_id_fields = ['dish', 'ingredient']


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost', 'price', 'is_available']
    list_filter = ['is_available']
    search_fields = ['name', 'description']
    filter_horizontal = ['dishes']
    list_editable = ['is_available']


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ['price_at_purchase', 'subtotal']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'timestamp', 'total_price_at_purchase', 'status']
    list_filter = ['status', 'timestamp']
    search_fields = ['user__username', 'notes']
    readonly_fields = ['timestamp', 'total_price_at_purchase']
    raw_id_fields = ['user']
    inlines = [PurchaseItemInline]


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'dish', 'quantity', 'price_at_purchase', 'subtotal']
    list_filter = ['purchase', 'dish']
    search_fields = ['purchase__id', 'dish__name']
    readonly_fields = ['price_at_purchase', 'subtotal']
    raw_id_fields = ['purchase', 'dish']
