"""Summarize router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any
from clawlayer.routers import RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


class SummarizeRouter(SemanticBaseRouter):
    """Provides structured summary template using semantic similarity with cascade support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        is_match, confidence, stage_idx, stage_details = self._match_cascade(message, "summarize")
        
        # Always store stage details for debugging
        self._last_stage_details = stage_details
        
        if is_match:
            result = RouteResult(name="summarize", content=self.template)
            result.stage_details = stage_details
            return result
        
        return None
