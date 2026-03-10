"""
Django signals for automatic updates.
"""
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from delights.models import Ingredient, RecipeRequirement, Dish, Menu
from delights.services.availability import (
    update_dish_availability,
    update_dishes_for_ingredient,
    update_menu_availability,
    update_menus_for_dish,
)


@receiver(post_save, sender=Ingredient)
def ingredient_saved(sender, instance, **kwargs):
    """Update dish availability when ingredient changes."""
    update_fields = kwargs.get('update_fields')
    if update_fields is None or 'quantity_available' in update_fields or 'price_per_unit' in update_fields:
        update_dishes_for_ingredient(instance)


@receiver([post_save, post_delete], sender=RecipeRequirement)
def recipe_requirement_changed(sender, instance, **kwargs):
    """Update dish when recipe requirement changes."""
    update_dish_availability(instance.dish)
    update_menus_for_dish(instance.dish)


@receiver(post_save, sender=Dish)
def dish_saved(sender, instance, **kwargs):
    """Update menus when dish availability changes."""
    update_fields = kwargs.get('update_fields')
    if update_fields is None or 'is_available' in update_fields:
        update_menus_for_dish(instance)


@receiver(m2m_changed, sender=Menu.dishes.through)
def menu_dishes_changed(sender, instance, action, **kwargs):
    """Update menu when dishes are added/removed."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        update_menu_availability(instance)
