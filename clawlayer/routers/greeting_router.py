"""Greeting router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any
from clawlayer.routers import RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


class GreetingRouter(SemanticBaseRouter):
    """Handles greeting messages using semantic similarity with cascade support."""
    
    def _pre_filter(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Pre-filter to reject obvious non-greetings."""
        msg_lower = message.lower()
        
        if len(message) > 3000:
            return f'Message too long ({len(message)} chars)'
        
        return None
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading based on confidence thresholds."""
        return self._route_with_cascade(message, context, "greeting", "Hi (quick response)")
