"""Configuration management for ClawLayer."""

import os
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class ProviderConfig:
    """LLM provider configuration."""
    name: str
    url: str
    type: str
    models: Dict[str, str]


@dataclass
class RouterConfig:
    """Individual router configuration."""
    enabled: bool
    options: Dict[str, Any]


@dataclass
class Config:
    """ClawLayer configuration."""
    providers: Dict[str, ProviderConfig]
    embedding_provider: str
    text_provider: str
    vision_provider: str
    port: int
    router_priority: List[str]
    routers: Dict[str, RouterConfig]
    
    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get provider by name."""
        return self.providers.get(name)
    
    def get_embedding_url(self) -> str:
        """Get embedding provider URL."""
        provider = self.providers.get(self.embedding_provider)
        if provider:
            return provider.url
        return "http://localhost:11434"
    
    def get_embedding_model(self) -> str:
        """Get embedding model name."""
        provider = self.providers.get(self.embedding_provider)
        if provider and 'embed' in provider.models:
            return provider.models['embed']
        return "nomic-embed-text"
    
    def get_text_url(self) -> str:
        """Get text generation provider URL."""
        provider = self.providers.get(self.text_provider)
        if provider:
            # Handle different provider types
            if provider.type == 'ollama':
                return f"{provider.url}/v1/chat/completions"
            return provider.url
        return "http://localhost:11434/v1/chat/completions"
    
    def get_text_model(self) -> str:
        """Get text generation model name."""
        provider = self.providers.get(self.text_provider)
        if provider and 'text' in provider.models:
            return provider.models['text']
        return "llama3.2"
    
    @classmethod
    def from_yaml(cls, config_path: str = None) -> 'Config':
        """Load configuration from YAML file."""
        load_dotenv()
        
        # Default config path
        if config_path is None:
            config_path = os.getenv("CLAWLAYER_CONFIG", "config.yml")
        
        # Try to find config file
        config_file = Path(config_path)
        if not config_file.exists():
            config_file = Path.cwd() / config_path
        if not config_file.exists():
            config_file = Path(__file__).parent.parent / config_path
        
        # Load YAML or use defaults
        if config_file.exists():
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
        else:
            data = {}
        
        # Parse providers
        providers_data = data.get('providers', {})
        providers = {}
        for name, pdata in providers_data.items():
            providers[name] = ProviderConfig(
                name=name,
                url=pdata.get('url', 'http://localhost:11434'),
                type=pdata.get('type', 'ollama'),
                models=pdata.get('models', {})
            )
        
        # Parse defaults
        defaults = data.get('defaults', {})
        
        # Parse server config
        server = data.get('server', {})
        
        # Parse router configs
        routers_config = data.get('routers', {})
        routers = {}
        for name in ['echo', 'command', 'greeting', 'summarize']:
            router_data = routers_config.get(name, {})
            routers[name] = RouterConfig(
                enabled=router_data.get('enabled', True),
                options={
                    k: v for k, v in router_data.items() 
                    if k != 'enabled'
                }
            )
        
        return cls(
            providers=providers,
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", defaults.get('embedding_provider', 'local')),
            text_provider=os.getenv("TEXT_PROVIDER", defaults.get('text_provider', 'remote')),
            vision_provider=os.getenv("VISION_PROVIDER", defaults.get('vision_provider', 'remote')),
            port=int(os.getenv("PORT", server.get('port', 11435))),
            router_priority=routers_config.get('priority', ['echo', 'command', 'greeting', 'summarize']),
            routers=routers
        )
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables (legacy)."""
        return cls.from_yaml()
