"""Core routing logic for ClawLayer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re
import json
import time


@dataclass
class RouteResult:
    """Result of routing decision."""
    name: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    should_proxy: bool = False


class Router(ABC):
    """Abstract base class for routers."""
    
    @abstractmethod
    def route(self, message: str, context: Dict[str, Any]) -> RouteResult:
        """Route a message and return the result."""
        pass


class GreetingRouter(Router):
    """Handles greeting messages."""
    
    def __init__(self, patterns: List[str] = None):
        self.patterns = patterns or [r'\b(hi|hello|hey|greetings)\b']
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        msg_lower = message.lower().strip()
        for pattern in self.patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return RouteResult(
                    name="greeting",
                    content="Hi (quick response from semantic router)"
                )
        return None


class EchoRouter(Router):
    """Echoes tool execution results without LLM processing."""
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        if context.get("role") == "tool" and context.get("tool_call_id"):
            # Find the function name from previous messages
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


class SummarizeRouter(Router):
    """Provides structured summary template."""
    
    def __init__(self, patterns: List[str] = None):
        self.patterns = patterns or [r'\b(summarize|checkpoint|summary)\b']
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
        msg_lower = message.lower()
        for pattern in self.patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return RouteResult(name="summarize", content=self.template)
        return None


class SemanticRouterAdapter(Router):
    """Adapter for semantic-router library."""
    
    def __init__(self, semantic_router):
        self.semantic_router = semantic_router
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        result = self.semantic_router(message)
        if result and result.name:
            return RouteResult(name=result.name, should_proxy=True)
        return None


class RouterChain:
    """Chains multiple routers with priority order."""
    
    def __init__(self, routers: List[Router]):
        self.routers = routers
    
    def route(self, message: str, context: Dict[str, Any]) -> RouteResult:
        """Try each router in order until one matches."""
        for router in self.routers:
            result = router.route(message, context)
            if result:
                return result
        
        # Default: proxy to LLM
        return RouteResult(name="fallback", should_proxy=True)
