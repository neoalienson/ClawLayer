"""Greeting router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any
from clawlayer.routers import RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


class GreetingRouter(SemanticBaseRouter):
    """Handles greeting messages using semantic similarity with cascade support."""
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading based on confidence thresholds."""
        # Pre-filter: reject obvious system messages
        msg_lower = message.lower()
        if any([
            message.startswith('System:'),
            'greet the user' in msg_lower,
            'please read them' in msg_lower,
            len(message) > 500  # Greetings are typically short
        ]):
            return None
        
        is_match, confidence, stage_idx, stage_details = self._match_cascade(message, "greeting")
        
        # Always store stage details for debugging
        self._last_stage_details = stage_details
        
        if is_match:
            stage_info = f" (stage {stage_idx}, confidence: {confidence:.2f})" if len(self.cascade_stages) > 1 else ""
            result = RouteResult(
                name="greeting",
                content=f"Hi (quick response{stage_info})"
            )
            result.stage_details = stage_details
            return result
        
        return None
