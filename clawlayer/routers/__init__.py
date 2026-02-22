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
    
    # Class-level registry mapping router names to classes
    _registry: Dict[str, type] = {}
    
    def __init__(self, router_config=None):
        """Initialize router with config.
        
        Args:
            router_config: RouterConfig object with options
        """
        self.router_config = router_config
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register a router class."""
        def wrapper(router_class):
            cls._registry[name] = router_class
            return router_class
        return wrapper
    
    @classmethod
    def create(cls, name: str, router_config) -> Optional['Router']:
        """Create a router instance by name."""
        router_class = cls._registry.get(name)
        if router_class:
            return router_class(router_config)
        return None
    
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
