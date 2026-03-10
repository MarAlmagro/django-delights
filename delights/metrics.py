"""
Prometheus metrics for Django Delights application.

This module defines custom business metrics for monitoring
application performance and usage.
"""

from prometheus_client import Counter, Histogram, Gauge

# Purchase metrics
purchase_counter = Counter(
    'delights_purchases_total',
    'Total number of purchases',
    ['status']
)

purchase_value = Histogram(
    'delights_purchase_value',
    'Purchase value distribution',
    buckets=[5, 10, 25, 50, 100, 250, 500]
)

purchase_items_count = Histogram(
    'delights_purchase_items_count',
    'Number of items per purchase',
    buckets=[1, 2, 3, 5, 10, 20]
)

# Inventory metrics
inventory_adjustment = Counter(
    'delights_inventory_adjustments_total',
    'Total inventory adjustments',
    ['ingredient', 'action']
)

low_stock_items = Gauge(
    'delights_low_stock_items',
    'Number of ingredients with low stock'
)

# Dish metrics
dish_availability = Gauge(
    'delights_dishes_available',
    'Number of available dishes'
)

dish_unavailable = Gauge(
    'delights_dishes_unavailable',
    'Number of unavailable dishes'
)

# User metrics
active_users = Gauge(
    'delights_active_users',
    'Number of active users in the last 24 hours'
)

# Error metrics
error_counter = Counter(
    'delights_errors_total',
    'Total number of errors',
    ['error_type', 'view']
)
