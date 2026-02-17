"""Unit tests for ClawLayer."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.router import (
    GreetingRouter, EchoRouter, CommandRouter, 
    SummarizeRouter, RouterChain, RouteResult
)
from clawlayer.handler import MessageHandler, ResponseGenerator
from clawlayer.proxy import LLMProxy
from clawlayer.config import Config


class TestGreetingRouter(unittest.TestCase):
    """Test greeting router."""
    
    def setUp(self):
        self.router = GreetingRouter()
    
    def test_matches_hello(self):
        result = self.router.route("hello", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "greeting")
        self.assertIn("Hi", result.content)
    
    def test_matches_hi(self):
        result = self.router.route("hi", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "greeting")
    
    def test_matches_hey(self):
        result = self.router.route("hey there", {})
        self.assertIsNotNone(result)
    
    def test_no_match(self):
        result = self.router.route("what is the weather", {})
        self.assertIsNone(result)
    
    def test_case_insensitive(self):
        result = self.router.route("HELLO", {})
        self.assertIsNotNone(result)


class TestEchoRouter(unittest.TestCase):
    """Test echo router."""
    
    def setUp(self):
        self.router = EchoRouter()
    
    def test_echoes_exec_tool_result(self):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [{
                    "id": "call_123",
                    "function": {"name": "exec"}
                }]
            }
        ]
        context = {
            "role": "tool",
            "tool_call_id": "call_123",
            "messages": messages
        }
        
        result = self.router.route("command output", context)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "echo")
        self.assertEqual(result.content, "command output")
    
    def test_no_echo_for_non_exec(self):
        messages = [
            {
                "role": "assistant",
                "tool_calls": [{
                    "id": "call_123",
                    "function": {"name": "other_function"}
                }]
            }
        ]
        context = {
            "role": "tool",
            "tool_call_id": "call_123",
            "messages": messages
        }
        
        result = self.router.route("output", context)
        self.assertIsNone(result)
    
    def test_no_echo_without_tool_role(self):
        context = {"role": "user"}
        result = self.router.route("message", context)
        self.assertIsNone(result)


class TestCommandRouter(unittest.TestCase):
    """Test command router."""
    
    def setUp(self):
        self.router = CommandRouter()
    
    def test_detects_run_prefix(self):
        result = self.router.route("run: ls -la", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "linux_command")
        self.assertIsNotNone(result.tool_calls)
        self.assertEqual(len(result.tool_calls), 1)
    
    def test_extracts_command(self):
        result = self.router.route("run: pwd", {})
        tool_call = result.tool_calls[0]
        args = json.loads(tool_call["function"]["arguments"])
        self.assertEqual(args["command"], "pwd")
    
    def test_case_insensitive(self):
        result = self.router.route("RUN: echo test", {})
        self.assertIsNotNone(result)
    
    def test_no_match_without_prefix(self):
        result = self.router.route("list files", {})
        self.assertIsNone(result)
    
    def test_tool_call_structure(self):
        result = self.router.route("run: ls", {})
        tool_call = result.tool_calls[0]
        
        self.assertIn("id", tool_call)
        self.assertEqual(tool_call["type"], "function")
        self.assertEqual(tool_call["function"]["name"], "exec")
        self.assertIn("arguments", tool_call["function"])


class TestSummarizeRouter(unittest.TestCase):
    """Test summarize router."""
    
    def setUp(self):
        self.router = SummarizeRouter()
    
    def test_matches_summarize(self):
        result = self.router.route("summarize the conversation", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "summarize")
        self.assertIn("## Goal", result.content)
    
    def test_matches_checkpoint(self):
        result = self.router.route("checkpoint", {})
        self.assertIsNotNone(result)
    
    def test_no_match(self):
        result = self.router.route("hello", {})
        self.assertIsNone(result)


class TestRouterChain(unittest.TestCase):
    """Test router chain."""
    
    def test_returns_first_match(self):
        router1 = Mock()
        router1.route.return_value = None
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="test")
        
        router3 = Mock()
        
        chain = RouterChain([router1, router2, router3])
        result = chain.route("message", {})
        
        self.assertEqual(result.name, "test")
        router1.route.assert_called_once()
        router2.route.assert_called_once()
        router3.route.assert_not_called()
    
    def test_fallback_when_no_match(self):
        router = Mock()
        router.route.return_value = None
        
        chain = RouterChain([router])
        result = chain.route("message", {})
        
        self.assertEqual(result.name, "fallback")
        self.assertTrue(result.should_proxy)
    
    def test_priority_order(self):
        """Test that routers are tried in order."""
        greeting_router = GreetingRouter()
        command_router = CommandRouter()
        
        chain = RouterChain([command_router, greeting_router])
        
        # Should match command first
        result = chain.route("run: echo hi", {})
        self.assertEqual(result.name, "linux_command")


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


class TestConfig(unittest.TestCase):
    """Test configuration."""
    
    @patch.dict('os.environ', {
        'OLLAMA_URL': 'http://custom:8080',
        'OLLAMA_MODEL': 'custom-model',
        'EMBED_MODEL': 'custom-embed',
        'PORT': '9999'
    })
    def test_from_env(self):
        config = Config.from_env()
        
        self.assertEqual(config.ollama_url, 'http://custom:8080')
        self.assertEqual(config.ollama_model, 'custom-model')
        self.assertEqual(config.embed_model, 'custom-embed')
        self.assertEqual(config.port, 9999)
    
    @patch.dict('os.environ', {}, clear=True)
    def test_defaults(self):
        config = Config.from_env()
        
        self.assertEqual(config.port, 11435)
        self.assertIsNotNone(config.ollama_url)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_routing_chain(self):
        """Test complete routing flow."""
        routers = [
            EchoRouter(),
            CommandRouter(),
            GreetingRouter(),
            SummarizeRouter()
        ]
        chain = RouterChain(routers)
        
        # Test greeting
        result = chain.route("hello", {})
        self.assertEqual(result.name, "greeting")
        
        # Test command
        result = chain.route("run: ls", {})
        self.assertEqual(result.name, "linux_command")
        
        # Test fallback
        result = chain.route("what is the weather", {})
        self.assertEqual(result.name, "fallback")
        self.assertTrue(result.should_proxy)


if __name__ == "__main__":
    unittest.main()
