"""Greeting router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any, List
from clawlayer.routers import Router, RouteResult


class GreetingRouter(Router):
    """Handles greeting messages using semantic similarity with cascade support."""
    
    def __init__(self, semantic_routers: List[Any] = None):
        """Initialize with list of semantic routers for cascading.
        
        Args:
            semantic_routers: List of (semantic_router, threshold) tuples for cascade stages
        """
        self.semantic_routers = semantic_routers or []
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading based on confidence thresholds."""
        for stage_idx, (semantic_router, threshold) in enumerate(self.semantic_routers, 1):
            if not semantic_router:
                continue
            
            result = semantic_router(message)
            if result and result.name == "greeting":
                # Check if confidence meets threshold
                confidence = getattr(result, 'score', 1.0)
                if confidence >= threshold:
                    stage_info = f" (stage {stage_idx}, confidence: {confidence:.2f})" if len(self.semantic_routers) > 1 else ""
                    return RouteResult(
                        name="greeting",
                        content=f"Hi (quick response from semantic router{stage_info})"
                    )
                # Continue to next stage if confidence too low
        
        return None
