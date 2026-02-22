"""Quick router using regex pattern matching."""

import re
from typing import Optional, Dict, Any
from clawlayer.routers import Router, RouteResult


@Router.register('quick')
class QuickRouter(Router):
    """Quick router using regex patterns."""
    
    def __init__(self, router_config=None):
        """Initialize with router config.
        
        Args:
            router_config: RouterConfig object with options, or None for defaults
        """
        super().__init__(router_config)
        self.patterns = []
        
        if router_config:
            patterns_config = router_config.options.get('patterns', [])
            for p in patterns_config:
                pattern = p.get('pattern', '')
                response = p.get('response', 'Hi')
                if pattern:
                    # Use DOTALL flag to make . match newlines
                    self.patterns.append({
                        'regex': re.compile(pattern, re.IGNORECASE | re.DOTALL),
                        'response': response
                    })
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route message if it matches any pattern."""
        msg = message.strip()
        for p in self.patterns:
            if p['regex'].search(msg):
                return RouteResult(name="quick", content=p['response'])
        return None
