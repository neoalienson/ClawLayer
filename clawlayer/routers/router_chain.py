"""Router chain for managing multiple routers."""

from typing import List
from clawlayer.routers import Router, RouteResult


class RouterChain:
    """Chains multiple routers with priority order."""
    
    def __init__(self, routers: List[Router]):
        self.routers = routers
    
    def route(self, message: str, context: dict) -> RouteResult:
        """Try each router in order until one matches."""
        for router in self.routers:
            result = router.route(message, context)
            if result:
                return result
        
        # Default: proxy to LLM
        return RouteResult(name="fallback", should_proxy=True)
