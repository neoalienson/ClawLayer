"""Summarize router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any, List
from clawlayer.routers import Router, RouteResult


class SummarizeRouter(Router):
    """Provides structured summary template using semantic similarity with cascade support."""
    
    def __init__(self, semantic_routers: List[Any] = None):
        """Initialize with list of semantic routers for cascading.
        
        Args:
            semantic_routers: List of (semantic_router, threshold) tuples for cascade stages
        """
        self.semantic_routers = semantic_routers or []
        self.template = """## Goal
No user goal provided in the conversation.

## Constraints & Preferences
- (none)

## Progress
### Done
- [x] None

### In Progress
- [ ] None

### Blocked
- [ ] None

## Key Decisions
- **None**

## Next Steps
1. None

## Critical Context
- (none)"""
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading based on confidence thresholds."""
        for stage_idx, (semantic_router, threshold) in enumerate(self.semantic_routers, 1):
            if not semantic_router:
                continue
            
            result = semantic_router(message)
            if result and result.name == "summarize":
                # Check if confidence meets threshold
                confidence = getattr(result, 'score', 1.0)
                if confidence >= threshold:
                    return RouteResult(name="summarize", content=self.template)
                # Continue to next stage if confidence too low
        
        return None
