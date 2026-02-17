"""Message handling and response generation."""

from typing import Dict, Any, List, Optional
import json


class MessageHandler:
    """Handles message extraction and context building."""
    
    @staticmethod
    def extract_message(data: Dict[str, Any]) -> str:
        """Extract message content from request data."""
        last_message = data["messages"][-1]
        content = last_message["content"]
        
        # Handle structured content
        if isinstance(content, list):
            return " ".join(
                part["text"] for part in content 
                if part.get("type") == "text"
            )
        return content
    
    @staticmethod
    def build_context(data: Dict[str, Any]) -> Dict[str, Any]:
        """Build routing context from request data."""
        last_message = data["messages"][-1]
        return {
            "role": last_message.get("role"),
            "tool_call_id": last_message.get("tool_call_id"),
            "messages": data["messages"],
            "stream": data.get("stream", False)
        }


class ResponseGenerator:
    """Generates OpenAI-compatible responses."""
    
    @staticmethod
    def generate_response(route_result, stream: bool = False) -> Dict[str, Any]:
        """Generate response based on route result."""
        if route_result.tool_calls:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": route_result.tool_calls
                    }
                }]
            }
        else:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": route_result.content or ""
                    }
                }]
            }
    
    @staticmethod
    def generate_stream(route_result):
        """Generate SSE stream for route result."""
        import time
        
        fake_id = f"chatcmpl-{int(time.time())}"
        now = int(time.time())
        
        # Initial chunk with role
        yield f'data: {json.dumps({"id": fake_id, "object": "chat.completion.chunk", "created": now, "model": "clawlayer", "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})}\n\n'
        
        # Content or tool calls
        if route_result.tool_calls:
            tool_calls_with_index = [
                {**tc, "index": 0} for tc in route_result.tool_calls
            ]
            yield f'data: {json.dumps({"id": fake_id, "object": "chat.completion.chunk", "created": now, "model": "clawlayer", "choices": [{"index": 0, "delta": {"tool_calls": tool_calls_with_index}, "finish_reason": None}]})}\n\n'
        else:
            yield f'data: {json.dumps({"id": fake_id, "object": "chat.completion.chunk", "created": now, "model": "clawlayer", "choices": [{"index": 0, "delta": {"content": route_result.content}, "finish_reason": None}]})}\n\n'
        
        # Final chunk
        yield f'data: {json.dumps({"id": fake_id, "object": "chat.completion.chunk", "created": now, "model": "clawlayer", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'
        yield "data: [DONE]\n\n"
