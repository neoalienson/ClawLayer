"""Unit tests for ClawLayer core components."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.handler import MessageHandler, ResponseGenerator
from clawlayer.proxy import LLMProxy
from clawlayer.routers import RouteResult


class TestMessageHandler(unittest.TestCase):
    """Test message handler."""
    
    def test_extract_string_message(self):
        data = {
            "messages": [
                {"role": "user", "content": "hello"}
            ]
        }
        message = MessageHandler.extract_message(data)
        self.assertEqual(message, "hello")
    
    def test_extract_structured_message(self):
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello"},
                        {"type": "text", "text": "world"}
                    ]
                }
            ]
        }
        message = MessageHandler.extract_message(data)
        self.assertEqual(message, "hello world")
    
    def test_build_context(self):
        data = {
            "messages": [
                {"role": "user", "content": "test"}
            ],
            "stream": True
        }
        context = MessageHandler.build_context(data)
        
        self.assertEqual(context["role"], "user")
        self.assertTrue(context["stream"])
        self.assertEqual(len(context["messages"]), 1)


class TestResponseGenerator(unittest.TestCase):
    """Test response generator."""
    
    def test_generate_content_response(self):
        route_result = RouteResult(name="test", content="Hello")
        response = ResponseGenerator.generate_response(route_result)
        
        self.assertIn("choices", response)
        self.assertEqual(response["choices"][0]["message"]["content"], "Hello")
        self.assertEqual(response["choices"][0]["message"]["role"], "assistant")
    
    def test_generate_tool_call_response(self):
        tool_calls = [{"id": "call_1", "type": "function"}]
        route_result = RouteResult(name="test", tool_calls=tool_calls)
        response = ResponseGenerator.generate_response(route_result)
        
        self.assertEqual(response["choices"][0]["message"]["tool_calls"], tool_calls)
        self.assertEqual(response["choices"][0]["message"]["content"], "")
    
    def test_generate_stream(self):
        route_result = RouteResult(name="test", content="Hello")
        chunks = list(ResponseGenerator.generate_stream(route_result))
        
        self.assertGreater(len(chunks), 0)
        self.assertTrue(any("data:" in chunk for chunk in chunks))
        self.assertTrue(any("[DONE]" in chunk for chunk in chunks))


class TestLLMProxy(unittest.TestCase):
    """Test LLM proxy."""
    
    @patch('clawlayer.proxy.requests.post')
    def test_forward_non_streaming(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"result": "test"}
        mock_post.return_value = mock_response
        
        proxy = LLMProxy("http://test.com", "model")
        result = proxy.forward([{"role": "user", "content": "test"}], stream=False)
        
        self.assertEqual(result, {"result": "test"})
        mock_post.assert_called_once()
    
    @patch('clawlayer.proxy.requests.post')
    def test_forward_streaming(self, mock_post):
        mock_response = Mock()
        mock_response.iter_lines.return_value = [b"data: test"]
        mock_post.return_value = mock_response
        
        proxy = LLMProxy("http://test.com", "model")
        result = list(proxy.forward([{"role": "user", "content": "test"}], stream=True))
        
        self.assertEqual(len(result), 1)
        self.assertIn("data: test", result[0])


if __name__ == "__main__":
    unittest.main()