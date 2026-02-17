"""Router factory for building routers from configuration."""

from typing import List, Optional
from clawlayer.routers import (
    Router, EchoRouter, CommandRouter,
    GreetingRouter, SummarizeRouter
)
from clawlayer.config import Config


class RouterFactory:
    """Factory for creating routers from configuration."""
    
    def __init__(self, config: Config, verbose: int = 0):
        self.config = config
        self.verbose = verbose
        self.semantic_router = None
    
    def _init_semantic_router(self):
        """Initialize semantic router library if needed."""
        if self.semantic_router:
            return self.semantic_router
        
        try:
            from semantic_router import Route, SemanticRouter
            from semantic_router.encoders import OllamaEncoder
            
            embed_url = self.config.get_embedding_url()
            embed_model = self.config.get_embedding_model()
            
            encoder = OllamaEncoder(name=embed_model, base_url=embed_url)
            
            routes = []
            
            # Build routes from config
            for router_name in self.config.semantic_router_priority:
                if not self.config.routers.get(router_name, None):
                    continue
                
                router_config = self.config.routers[router_name]
                if not router_config.enabled:
                    continue
                
                utterances = router_config.options.get('utterances', [])
                if utterances:
                    routes.append(Route(name=router_name, utterances=utterances))
            
            if routes:
                self.semantic_router = SemanticRouter(
                    encoder=encoder,
                    routes=routes,
                    auto_sync="local"
                )
                return self.semantic_router
        except ImportError:
            if self.verbose:
                print("Warning: semantic-router not installed", file=__import__('sys').stderr)
        
        return None
    
    def create_router(self, router_name: str) -> Optional[Router]:
        """Create a router instance by name."""
        router_config = self.config.routers.get(router_name)
        if not router_config or not router_config.enabled:
            return None
        
        if router_name == 'echo':
            return EchoRouter()
        
        elif router_name == 'command':
            prefix = router_config.options.get('prefix', 'run:')
            return CommandRouter(prefix)
        
        elif router_name == 'greeting':
            semantic_router = self._init_semantic_router()
            return GreetingRouter(semantic_router)
        
        elif router_name == 'summarize':
            semantic_router = self._init_semantic_router()
            return SummarizeRouter(semantic_router)
        
        return None
    
    def build_router_chain(self) -> List[Router]:
        """Build router chain from configuration."""
        routers = []
        
        # Add fast routers
        for router_name in self.config.fast_router_priority:
            router = self.create_router(router_name)
            if router:
                routers.append(router)
        
        # Add semantic routers
        for router_name in self.config.semantic_router_priority:
            router = self.create_router(router_name)
            if router:
                routers.append(router)
        
        if self.verbose:
            enabled_routers = [r.__class__.__name__ for r in routers]
            print(f"Router chain: {' → '.join(enabled_routers)}", file=__import__('sys').stderr)
        
        return routers
