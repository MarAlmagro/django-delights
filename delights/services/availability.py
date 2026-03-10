"""
Availability service for checking and updating availability status.
"""
from delights.models import Dish, Ingredient, Menu


def check_dish_availability(dish: Dish) -> bool:
    """
    Check if dish is available based on ingredient stock.
    
    A dish is available if:
    - It has at least one recipe requirement
    - All required ingredients have sufficient quantity
    
    Args:
        dish: The dish to check
        
    Returns:
        True if available, False otherwise
    """
    requirements = dish.recipe_requirements.select_related('ingredient')
    
    if not requirements.exists():
        return False
    
    for requirement in requirements:
        if requirement.ingredient.quantity_available < requirement.quantity_required:
            return False
    
    return True


def check_menu_availability(menu: Menu) -> bool:
    """
    Check if menu is available based on dish availability.
    
    A menu is available if:
    - It has at least one dish
    - All dishes are available
    
    Args:
        menu: The menu to check
        
    Returns:
        True if available, False otherwise
    """
    dishes = menu.dishes.all()
    
    if not dishes.exists():
        return False
    
    return all(dish.is_available for dish in dishes)


def update_dish_availability(dish: Dish) -> None:
    """
    Update dish cost and availability status.
    
    Args:
        dish: The dish to update
    """
    from delights.services.pricing import calculate_dish_cost
    
    dish.cost = calculate_dish_cost(dish)
    dish.is_available = check_dish_availability(dish)
    dish.save(update_fields=['cost', 'is_available'])


def update_dishes_for_ingredient(ingredient: Ingredient) -> None:
    """
    Update all dishes that use the specified ingredient.
    
    Args:
        ingredient: The ingredient that changed
    """
    dishes = Dish.objects.filter(
        recipe_requirements__ingredient=ingredient
    ).distinct()
    
    for dish in dishes:
        update_dish_availability(dish)


def update_menu_availability(menu: Menu) -> None:
    """
    Update menu cost and availability status.
    
    Args:
        menu: The menu to update
    """
    from delights.services.pricing import calculate_menu_cost
    
    menu.cost = calculate_menu_cost(menu)
    menu.is_available = check_menu_availability(menu)
    menu.save(update_fields=['cost', 'is_available'])


def update_menus_for_dish(dish: Dish) -> None:
    """
    Update all menus that contain the specified dish.
    
    Args:
        dish: The dish that changed
    """
    menus = Menu.objects.filter(dishes=dish)
    
    for menu in menus:
        update_menu_availability(menu)
