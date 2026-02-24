"""Greeting router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any
from clawlayer.routers import Router, RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


@Router.register('greeting')
class GreetingRouter(SemanticBaseRouter):
    """Handles greeting messages using semantic similarity with cascade support."""
    
    SCHEMA = {
        'stages': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'provider': {'type': 'string', 'label': 'Provider'},
                    'model': {'type': 'string', 'label': 'Model'},
                    'threshold': {'type': 'number', 'label': 'Threshold'}
                }
            }
        },
        'utterances': {'type': 'array', 'label': 'Example utterances'}
    }
    
    def _pre_filter(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Pre-filter to reject obvious non-greetings."""
        msg_lower = message.lower()
        
        if len(message) > 3000:
            return f'Message too long ({len(message)} chars)'
        
        return None
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading based on confidence thresholds."""
        return self._route_with_cascade(message, context, "greeting", "Hi (quick response)")
