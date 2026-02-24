"""Command router for detecting command execution patterns."""

from typing import Optional, Dict, Any
import json
import time
from clawlayer.routers import Router, RouteResult


@Router.register('command')
class CommandHandler(Router):
    """Detects command execution patterns and generates tool calls."""
    
    SCHEMA = {
        'prefix': {'type': 'string', 'label': 'Command prefix'}
    }
    
    def __init__(self, router_config=None):
        super().__init__(router_config)
        if router_config:
            self.prefix = router_config.options.get('prefix', 'run:').lower()
        else:
            self.prefix = 'run:'
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        if self.prefix in message.lower():
            command = self._extract_command(message)
            tool_calls = [{
                "id": f"call_{int(time.time())}",
                "type": "function",
                "function": {
                    "name": "exec",
                    "arguments": json.dumps({
                        "command": command,
                        "pty": False,
                        "background": False
                    })
                }
            }]
            return RouteResult(name="linux_command", tool_calls=tool_calls)
        return None
    
    def _extract_command(self, text: str) -> str:
        idx = text.lower().find(self.prefix)
        if idx != -1:
            return text[idx + len(self.prefix):].strip()
        return text.strip()
