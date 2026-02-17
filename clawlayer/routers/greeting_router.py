"""Greeting router using semantic similarity."""

from typing import Optional, Dict, Any
from clawlayer.routers import Router, RouteResult


class GreetingRouter(Router):
    """Handles greeting messages using semantic similarity."""
    
    def __init__(self, semantic_router=None):
        self.semantic_router = semantic_router
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        if self.semantic_router:
            result = self.semantic_router(message)
            if result and result.name == "greeting":
                return RouteResult(
                    name="greeting",
                    content="Hi (quick response from semantic router)"
                )
        return None
