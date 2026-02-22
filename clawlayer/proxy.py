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
        request_data = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        try:
            response = requests.post(
                self.url,
                json=request_data,
                stream=stream,
                timeout=30
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                # Log the error
                import sys
                print(f"\n{'='*60}", file=sys.stderr)
                print(f"LLM PROXY HTTP ERROR: {response.status_code}", file=sys.stderr)
                print(f"URL: {self.url}", file=sys.stderr)
                print(f"Model: {self.model}", file=sys.stderr)
                response_text = getattr(response, 'text', 'N/A')
                if hasattr(response_text, '__getitem__'):
                    print(f"Response: {response_text[:500]}", file=sys.stderr)
                else:
                    print(f"Response: {response_text}", file=sys.stderr)
                print(f"{'='*60}\n", file=sys.stderr)
                
                return {
                    "error": {
                        "message": f"HTTP {response.status_code}: {response.text}",
                        "type": "http_error",
                        "details": {
                            "url": self.url,
                            "model": self.model,
                            "status_code": response.status_code
                        }
                    }
                }
            
            if stream:
                return self._stream_response(response), request_data
            else:
                response_json = response.json()
                return response_json, request_data
        except requests.exceptions.RequestException as e:
            # Log the error
            import sys
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"LLM PROXY ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr)
            print(f"URL: {self.url}", file=sys.stderr)
            print(f"Model: {self.model}", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)
            
            # Return error response in OpenAI format with details
            return {
                "error": {
                    "message": f"LLM proxy error: {str(e)}",
                    "type": "connection_error",
                    "details": {
                        "url": self.url,
                        "model": self.model,
                        "error_type": type(e).__name__
                    }
                }
            }
    
    def _stream_response(self, response) -> Iterator[str]:
        """Stream response from LLM."""
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                yield f"{decoded}\n\n"
