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
        self._last_stage_details = []  # Always initialize to ensure it exists
    
    def _pre_filter(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Pre-filter hook for subclasses to reject messages early.
        
        Args:
            message: User message
            context: Request context
            
        Returns:
            Rejection reason string if message should be rejected, None otherwise
        """
        # Default: no pre-filtering
        # Subclasses can override to add custom pre-filters
        return None
    
    def _match_with_llm(self, message: str, llm_config: Dict) -> Tuple[bool, float, Dict]:
        """Match message using LLM.
        
        Args:
            message: User message
            llm_config: LLM configuration dict
            
        Returns:
            (is_match, confidence, stage_data) tuple
        """
        import time
        start_time = time.time()
        
        provider = llm_config['provider']
        model = llm_config['model']
        utterances = llm_config['utterances']
        route_name = llm_config['route_name']
        
        # Build prompt for LLM
        prompt = f"""Determine if the user's message matches a {route_name} request.

Example {route_name} requests:
{chr(10).join('- ' + u for u in utterances)}

User message: "{message}"

Respond with ONLY a JSON object: {{"is_match": true, "confidence": 0.0-1.0}}
where confidence indicates how similar the message is to the examples (1.0 = exact match, 0.0 = completely different)."""
        
        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        stage_data = {
            "model": model,
            "provider_url": provider.url,
            "request": request_data,
            "response": None,
            "error": None,
            "latency_ms": 0
        }
        
        try:
            # Check provider type and use appropriate API format
            if provider.type == 'ollama':
                # Use Ollama chat API format
                response = requests.post(
                    f"{provider.url}/api/chat",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    },
                    timeout=10
                )
            else:
                # Use OpenAI-compatible API format
                response = requests.post(
                    provider.url,
                    json=request_data,
                    timeout=10
                )
            
            stage_data["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                result = response.json()
                stage_data["response"] = result
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                # Parse JSON response - strip markdown code blocks if present
                try:
                    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
                    content_clean = content.strip()
                    if content_clean.startswith('```'):
                        # Find the actual JSON content between code fences
                        lines = content_clean.split('\n')
                        content_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else content_clean
                    
                    parsed = json.loads(content_clean)
                    return (parsed.get('is_match', False), parsed.get('confidence', 0.0), stage_data)
                except json.JSONDecodeError as e:
                    stage_data["error"] = f"JSON parse error: {str(e)}. Content: {content[:200]}"
            else:
                stage_data["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            stage_data["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            stage_data["error"] = str(e)
        
        return (False, 0.0, stage_data)
    
    def _match_cascade(self, message: str, route_name: str) -> Tuple[bool, float, int, list]:
        """Try matching through cascade stages.
        
        Args:
            message: User message
            route_name: Expected route name for embedding matchers
            
        Returns:
            (is_match, confidence, stage_idx, stage_details) tuple
        """
        import time
        stage_details = []
        
        for stage_idx, (matcher, threshold, stage_type) in enumerate(self.cascade_stages, 1):
            if not matcher:
                stage_details.append({"stage": stage_idx, "type": "none", "result": "No matcher"})
                continue
            
            if stage_type == 'llm':
                # LLM-based matching
                is_match, confidence, stage_data = self._match_with_llm(message, matcher)
                stage_detail = {
                    "stage": stage_idx,
                    "type": "LLM", 
                    "confidence": confidence,
                    "threshold": threshold,
                    "result": "match" if is_match and confidence >= threshold else "no match",
                    "model": stage_data.get("model", "unknown"),
                    "provider_url": stage_data.get("provider_url", "unknown"),
                    "latency_ms": stage_data.get("latency_ms", 0),
                    "request": stage_data.get("request"),
                    "response": stage_data.get("response"),
                    "error": stage_data.get("error")
                }
                stage_details.append(stage_detail)
                if is_match and confidence >= threshold:
                    return (True, confidence, stage_idx, stage_details)
            else:
                # Embedding-based matching
                start_time = time.time()
                result = matcher(message)
                latency_ms = round((time.time() - start_time) * 1000, 2)
                
                if result and result.name == route_name:
                    confidence = getattr(result, 'score', 1.0)
                    stage_detail = {
                        "stage": stage_idx,
                        "type": "Embedding",
                        "confidence": confidence,
                        "threshold": threshold,
                        "result": "match" if confidence >= threshold else "no match",
                        "latency_ms": latency_ms,
                        "message": message
                    }
                    stage_details.append(stage_detail)
                    if confidence >= threshold:
                        return (True, confidence, stage_idx, stage_details)
                else:
                    stage_details.append({
                        "stage": stage_idx,
                        "type": "Embedding",
                        "result": "no match or wrong route",
                        "latency_ms": latency_ms,
                        "message": message
                    })
        
        return (False, 0.0, 0, stage_details)
    
    def _build_llm_request(self, message: str, llm_config: Dict) -> Dict:
        """Build the LLM request for display purposes."""
        provider = llm_config['provider']
        model = llm_config['model']
        utterances = llm_config['utterances']
        route_name = llm_config['route_name']
        
        prompt = f"""Determine if the user's PRIMARY INTENT is a {route_name} request.

Example {route_name} requests:
{chr(10).join('- ' + u for u in utterances)}

IMPORTANT: Only match if the user is DIRECTLY making a {route_name} request. Do NOT match if:
- The message only MENTIONS {route_name} as part of instructions or system messages
- The message is asking the AI to perform a {route_name} action (not the user greeting)
- The {route_name} keyword appears in quoted text or metadata

User message: "{message}"

Respond with ONLY a JSON object: {{"is_match": true/false, "confidence": 0.0-1.0}}"""
        
        return {
            "url": provider.url,
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
    
    def route(self, message: str, context: Dict[str, Any]) -> Optional[RouteResult]:
        """Route with multi-stage cascading. Override in subclass."""
        raise NotImplementedError("Subclass must implement route()")
    
    def _route_with_cascade(self, message: str, context: Dict[str, Any], route_name: str, response_content: str) -> Optional[RouteResult]:
        """Standard routing with cascade and pre-filter support.
        
        This method enforces the pattern:
        1. Check pre-filter
        2. Run cascade matching
        3. Store stage details
        4. Return result
        
        Args:
            message: User message
            context: Request context
            route_name: Name of the route (e.g., 'greeting', 'summarize')
            response_content: Content to return if matched
            
        Returns:
            RouteResult if matched, None otherwise
        """
        # Check pre-filter
        rejection_reason = self._pre_filter(message, context)
        if rejection_reason:
            # Store rejection info for tried_routers
            self._last_stage_details = [{
                'stage': 0,
                'type': 'Pre-filter',
                'result': f'rejected: {rejection_reason}',
                'latency_ms': 0
            }]
            return None
        
        # Run cascade matching
        is_match, confidence, stage_idx, stage_details = self._match_cascade(message, route_name)
        
        # Always store stage details for debugging
        self._last_stage_details = stage_details
        
        if is_match:
            stage_info = f" (stage {stage_idx}, confidence: {confidence:.2f})" if len(self.cascade_stages) > 1 else ""
            result = RouteResult(
                name=route_name,
                content=f"{response_content}{stage_info}"
            )
            result.stage_details = stage_details
            return result
        
        return None
