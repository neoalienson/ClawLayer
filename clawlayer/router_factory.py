"""Router factory for building routers from configuration."""

from typing import List, Optional, Tuple, Any
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
        self.semantic_router_cache = {}  # Cache semantic routers by (provider, model)
    
    def _init_semantic_router(self, provider_name: str, model_name: str) -> Optional[Any]:
        """Initialize semantic router for specific provider and model.
        
        Args:
            provider_name: Provider name from config
            model_name: Model name to use for embeddings
            
        Returns:
            Initialized SemanticRouter or None
        """
        cache_key = (provider_name, model_name)
        if cache_key in self.semantic_router_cache:
            return self.semantic_router_cache[cache_key]
        
        try:
            from semantic_router import Route, SemanticRouter
            from semantic_router.encoders import OllamaEncoder
            
            provider = self.config.get_provider(provider_name)
            if not provider:
                return None
            
            encoder = OllamaEncoder(name=model_name, base_url=provider.url)
            
            routes = []
            
            # Build routes from config for this specific router instance
            for router_name in self.config.semantic_router_priority:
                router_config = self.config.routers.get(router_name)
                if not router_config or not router_config.enabled:
                    continue
                
                utterances = router_config.options.get('utterances', [])
                if utterances:
                    routes.append(Route(name=router_name, utterances=utterances))
            
            if routes:
                semantic_router = SemanticRouter(
                    encoder=encoder,
                    routes=routes,
                    auto_sync="local"
                )
                self.semantic_router_cache[cache_key] = semantic_router
                return semantic_router
        except ImportError:
            if self.verbose:
                print("Warning: semantic-router not installed", file=__import__('sys').stderr)
        
        return None
    
    def _build_cascade_stages(self, router_config) -> List[Tuple[Any, float]]:
        """Build cascade stages from router config.
        
        Args:
            router_config: RouterConfig with stages configuration
            
        Returns:
            List of (semantic_router, threshold) tuples
        """
        stages = router_config.options.get('stages', [])
        if not stages:
            # Fallback to legacy single provider config
            provider = router_config.options.get('provider', self.config.embedding_provider)
            model = self.config.get_embedding_model()
            semantic_router = self._init_semantic_router(provider, model)
            return [(semantic_router, 0.0)] if semantic_router else []
        
        cascade_stages = []
        for stage in stages:
            provider_name = stage.get('provider', self.config.embedding_provider)
            model_name = stage.get('model', self.config.get_embedding_model())
            threshold = stage.get('threshold', 0.0)
            
            semantic_router = self._init_semantic_router(provider_name, model_name)
            if semantic_router:
                cascade_stages.append((semantic_router, threshold))
                if self.verbose:
                    print(f"  Stage {len(cascade_stages)}: {provider_name}/{model_name} (threshold: {threshold})", 
                          file=__import__('sys').stderr)
        
        return cascade_stages
    
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
            if self.verbose:
                print(f"Building {router_name} with cascade stages:", file=__import__('sys').stderr)
            cascade_stages = self._build_cascade_stages(router_config)
            return GreetingRouter(cascade_stages)
        
        elif router_name == 'summarize':
            if self.verbose:
                print(f"Building {router_name} with cascade stages:", file=__import__('sys').stderr)
            cascade_stages = self._build_cascade_stages(router_config)
            return SummarizeRouter(cascade_stages)
        
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
