"""
Custom decorators for Django Delights.

Includes rate limiting decorators for sensitive operations.
"""

from functools import wraps
from django_ratelimit.decorators import ratelimit


def ratelimit_post(key='ip', rate='10/m'):
    """
    Rate limit POST requests.
    
    Args:
        key: Rate limit key (default: 'ip')
        rate: Rate limit (default: '10/m' = 10 per minute)
    """
    def decorator(func):
        return ratelimit(key=key, rate=rate, method='POST', block=True)(func)
    return decorator


def ratelimit_strict(key='ip', rate='5/m'):
    """
    Strict rate limit for sensitive operations.
    
    Args:
        key: Rate limit key (default: 'ip')
        rate: Rate limit (default: '5/m' = 5 per minute)
    """
    def decorator(func):
        return ratelimit(key=key, rate=rate, method='POST', block=True)(func)
    return decorator
