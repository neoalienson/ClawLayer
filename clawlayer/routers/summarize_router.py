"""Summarize router using semantic similarity."""

from typing import Optional, Dict, Any
from clawlayer.routers import Router, RouteResult


class SummarizeRouter(Router):
    """Provides structured summary template using semantic similarity."""
    
    def __init__(self, semantic_router=None):
        self.semantic_router = semantic_router
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
        if self.semantic_router:
            result = self.semantic_router(message)
            if result and result.name == "summarize":
                return RouteResult(name="summarize", content=self.template)
        return None
