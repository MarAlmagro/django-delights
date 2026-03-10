"""
Custom API renderers for Django Delights.

This module provides custom renderers that add additional metadata
to API responses, such as request IDs for tracing.
"""

from rest_framework.renderers import JSONRenderer


class RequestIdRenderer(JSONRenderer):
    """
    JSON renderer that adds request ID to response headers.
    
    This allows clients to reference specific requests when reporting issues
    and enables correlation of logs across distributed systems.
    """
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Add X-Request-ID header to response."""
        if renderer_context:
            response = renderer_context.get('response')
            if response:
                try:
                    from request_id import get_current_request_id
                    request_id = get_current_request_id()
                    if request_id:
                        response['X-Request-ID'] = request_id
                except ImportError:
                    pass
        
        return super().render(data, accepted_media_type, renderer_context)
