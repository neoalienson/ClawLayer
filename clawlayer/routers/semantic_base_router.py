"""Base router for semantic matching with multi-stage cascading."""

from typing import Optional, Dict, Any, List, Tuple
import requests
import json
from clawlayer.routers import Router, RouteResult


class SemanticBaseRouter(Router):
    """Base class for semantic routers with multi-stage cascade support."""
    
    def __init__(self, cascade_stages: List[Tuple[Any, float, str]] = None):
        """Initialize with list of cascade stages.
        
        Args:
            cascade_stages: List of (matcher, threshold, type) tuples where type is 'embedding' or 'llm'
        """
        self.cascade_stages = cascade_stages or []
    
    def _match_with_llm(self, message: str, llm_config: Dict) -> Tuple[bool, float]:
        """Match message using LLM.
        
        Args:
            message: User message
            llm_config: LLM configuration dict
            
        Returns:
            (is_match, confidence) tuple
        """
        provider = llm_config['provider']
        model = llm_config['model']
        utterances = llm_config['utterances']
        route_name = llm_config['route_name']
        
        # Build prompt for LLM
        prompt = f"""Determine if the following message is a {route_name} request.

Example {route_name} requests:
{chr(10).join('- ' + u for u in utterances)}

User message: "{message}"

Respond with ONLY a JSON object: {{"is_match": true/false, "confidence": 0.0-1.0}}"""
        
        try:
            response = requests.post(
                provider.url,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                # Parse JSON response
                try:
                    parsed = json.loads(content)
                    return (parsed.get('is_match', False), parsed.get('confidence', 0.0))
                except json.JSONDecodeError:
                    # Fallback: check for keywords
                    is_match = 'true' in content.lower() and 'is_match' in content.lower()
                    return (is_match, 0.5 if is_match else 0.0)
        except Exception:
            pass
        
        return (False, 0.0)
    
    def _match_cascade(self, message: str, route_name: str) -> Tuple[bool, float, int]:
        """Try matching through cascade stages.
        
        Args:
            message: User message
            route_name: Expected route name for embedding matchers
            
        Returns:
            (is_match, confidence, stage_idx) tuple
        """
        for stage_idx, (matcher, threshold, stage_type) in enumerate(self.cascade_stages, 1):
            if not matcher:
                continue
            
            if stage_type == 'llm':
                # LLM-based matching
                is_match, confidence = self._match_with_llm(message, matcher)
                if is_match and confidence >= threshold:
                    return (True, confidence, stage_idx)
            else:
                # Embedding-based matching
                result = matcher(message)
                if result and result.name == route_name:
                    confidence = getattr(result, 'score', 1.0)
                    if confidence >= threshold:
                        return (True, confidence, stage_idx)
        
        return (False, 0.0, 0)
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading. Override in subclass."""
        raise NotImplementedError("Subclass must implement route()")
