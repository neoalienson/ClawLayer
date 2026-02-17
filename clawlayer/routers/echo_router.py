"""Echo router for tool execution results."""

from typing import Optional, Dict, Any, List
from clawlayer.routers import Router, RouteResult


class EchoRouter(Router):
    """Echoes tool execution results without LLM processing."""
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        if context.get("role") == "tool" and context.get("tool_call_id"):
            tool_function = self._find_tool_function(
                context.get("messages", []),
                context.get("tool_call_id")
            )
            
            if tool_function == "exec":
                return RouteResult(name="echo", content=message)
        return None
    
    def _find_tool_function(self, messages: List[Dict], tool_call_id: str) -> Optional[str]:
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    if tc.get("id") == tool_call_id:
                        return tc.get("function", {}).get("name")
        return None
