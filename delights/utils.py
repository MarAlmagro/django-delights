"""
Utility functions for Django Delights.

Includes audit logging helpers and other common utilities.
"""

from .models import AuditLog


def get_client_ip(request):
    """
    Get the client IP address from the request.
    
    Args:
        request: Django request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit(user, action, model_name, object_id=None, changes=None, request=None):
    """
    Create an audit log entry.
    
    Args:
        user: User who performed the action (can be None for system actions)
        action: Action type (use AuditLog.ACTION_* constants)
        model_name: Name of the model affected
        object_id: ID of the object affected (optional)
        changes: Dictionary of changes made (optional)
        request: Django request object (optional, for IP address)
        
    Returns:
        AuditLog: Created audit log entry
    """
    ip_address = None
    if request:
        ip_address = get_client_ip(request)
    
    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        changes=changes or {},
        ip_address=ip_address
    )


def calculate_suggested_price(cost, margin=None):
    """
    Calculate suggested price based on cost and margin.
    
    Args:
        cost: Base cost
        margin: Profit margin (default from settings)
        
    Returns:
        Decimal: Suggested price
    """
    from django.conf import settings
    from decimal import Decimal
    
    if margin is None:
        margin = getattr(settings, 'GLOBAL_MARGIN', Decimal('0.20'))
    
    return cost * (1 + Decimal(str(margin)))


def update_dishes_for_ingredient(ingredient):
    """
    Update availability for all dishes using the given ingredient.
    
    Args:
        ingredient: Ingredient instance
    """
    from .services.availability import update_dish_availability
    
    for requirement in ingredient.recipe_requirements.select_related('dish'):
        update_dish_availability(requirement.dish)
