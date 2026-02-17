"""Greeting router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any
from clawlayer.routers import RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


class GreetingRouter(SemanticBaseRouter):
    """Handles greeting messages using semantic similarity with cascade support."""
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading based on confidence thresholds."""
        is_match, confidence, stage_idx = self._match_cascade(message, "greeting")
        
        if is_match:
            stage_info = f" (stage {stage_idx}, confidence: {confidence:.2f})" if len(self.cascade_stages) > 1 else ""
            return RouteResult(
                name="greeting",
                content=f"Hi (quick response{stage_info})"
            )
        
        return None
