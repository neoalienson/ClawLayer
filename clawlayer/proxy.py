"""LLM proxy for forwarding requests."""

import requests
from typing import Dict, Any, Iterator


class LLMProxy:
    """Proxies requests to LLM backend."""
    
    def __init__(self, url: str, model: str):
        self.url = url
        self.model = model
    
    def forward(self, messages: list, stream: bool = False) -> Any:
        """Forward request to LLM."""
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": messages,
                "stream": stream
            },
            stream=stream
        )
        
        if stream:
            return self._stream_response(response)
        else:
            return response.json()
    
    def _stream_response(self, response) -> Iterator[str]:
        """Stream response from LLM."""
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                yield f"{decoded}\n\n"
