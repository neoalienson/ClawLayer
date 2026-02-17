"""Configuration management for ClawLayer."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """ClawLayer configuration."""
    ollama_url: str
    ollama_model: str
    embed_model: str
    port: int
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        load_dotenv()
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434/v1/chat/completions"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            embed_model=os.getenv("EMBED_MODEL", "nomic-embed-text"),
            port=int(os.getenv("PORT", "11435"))
        )
