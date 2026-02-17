"""Command router for detecting command execution patterns."""

from typing import Optional, Dict, Any
import json
import time
from clawlayer.routers import Router, RouteResult


class CommandRouter(Router):
    """Detects command execution patterns and generates tool calls."""
    
    def __init__(self, prefix: str = "run:"):
        self.prefix = prefix.lower()
    
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
