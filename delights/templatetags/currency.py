from django import template
from django.conf import settings

register = template.Library()


@register.filter
def currency(value):
    """Format value as currency based on locale."""
    if value is None:
        return ''
    symbol = getattr(settings, 'CURRENCY_SYMBOL', '$')
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"
