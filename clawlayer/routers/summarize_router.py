"""Summarize router using semantic similarity with multi-stage cascading."""

from typing import Optional, Dict, Any
from clawlayer.routers import Router, RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


@Router.register('summarize')
class SummarizeRouter(SemanticBaseRouter):
    """Provides structured summary template using semantic similarity with cascade support."""
    
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
        return self._route_with_cascade(message, context, "summarize", self.template)
