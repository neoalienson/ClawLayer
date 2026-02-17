"""Base router classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


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
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route a message and return the result."""
        pass


# Import all routers for convenience
from clawlayer.routers.echo_router import EchoRouter
from clawlayer.routers.command_router import CommandRouter
from clawlayer.routers.greeting_router import GreetingRouter
from clawlayer.routers.summarize_router import SummarizeRouter
from clawlayer.routers.router_chain import RouterChain

__all__ = [
    'Router',
    'RouteResult',
    'EchoRouter',
    'CommandRouter',
    'GreetingRouter',
    'SummarizeRouter',
    'RouterChain'
]
