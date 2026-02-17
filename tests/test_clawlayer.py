"""Unit tests for ClawLayer."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.routers import (
    GreetingRouter, EchoRouter, CommandRouter, 
    SummarizeRouter, RouterChain, RouteResult
)
from clawlayer.handler import MessageHandler, ResponseGenerator
from clawlayer.proxy import LLMProxy
from clawlayer.config import Config


class TestGreetingRouter(unittest.TestCase):
    """Test greeting router."""
    
    def setUp(self):
        # Mock semantic router with cascade structure
        self.mock_semantic = Mock()
        # Pass as list of (matcher, threshold, type) tuples
        self.router = GreetingRouter([(self.mock_semantic, 0.5, 'embedding')])
    
    def test_matches_hello(self):
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.9
        self.mock_semantic.return_value = mock_result
        
        result = self.router.route("hello", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "greeting")
        self.assertIn("Hi", result.content)
    
    def test_matches_hi(self):
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.8
        self.mock_semantic.return_value = mock_result
        
        result = self.router.route("hi", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "greeting")
    
    def test_no_match(self):
        mock_result = Mock()
        mock_result.name = "other"
        self.mock_semantic.return_value = mock_result
        
        result = self.router.route("what is the weather", {})
        self.assertIsNone(result)
    
    def test_no_semantic_router(self):
        router = GreetingRouter([])
        result = router.route("hello", {})
        self.assertIsNone(result)


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
        self.mock_semantic = Mock()
        # Pass as list of (matcher, threshold, type) tuples
        self.router = SummarizeRouter([(self.mock_semantic, 0.5, 'embedding')])
    
    def test_matches_summarize(self):
        mock_result = Mock()
        mock_result.name = "summarize"
        mock_result.score = 0.9
        self.mock_semantic.return_value = mock_result
        
        result = self.router.route("summarize the conversation", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "summarize")
        self.assertIn("## Goal", result.content)
    
    def test_matches_checkpoint(self):
        mock_result = Mock()
        mock_result.name = "summarize"
        mock_result.score = 0.8
        self.mock_semantic.return_value = mock_result
        
        result = self.router.route("checkpoint", {})
        self.assertIsNotNone(result)
    
    def test_no_match(self):
        mock_result = Mock()
        mock_result.name = "other"
        self.mock_semantic.return_value = mock_result
        
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
        mock_semantic = Mock()
        mock_result = Mock()
        mock_result.name = "other"
        mock_semantic.return_value = mock_result
        
        greeting_router = GreetingRouter(mock_semantic)
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
    
    def test_from_yaml(self):
        config = Config.from_yaml()
        
        self.assertIsNotNone(config.providers)
        self.assertIn('local', config.providers)
        self.assertIn('remote', config.providers)
        self.assertEqual(config.port, 11435)
    
    def test_provider_methods(self):
        config = Config.from_yaml()
        
        # Test embedding provider
        self.assertIsNotNone(config.get_embedding_url())
        self.assertIsNotNone(config.get_embedding_model())
        
        # Test text provider
        self.assertIsNotNone(config.get_text_url())
        self.assertIsNotNone(config.get_text_model())
    
    def test_provider_config(self):
        """Test provider configuration structure."""
        config = Config.from_yaml()
        
        # Test local provider
        local = config.get_provider('local')
        self.assertIsNotNone(local)
        self.assertEqual(local.type, 'ollama')
        self.assertIn('embed', local.models)
        
        # Test remote provider
        remote = config.get_provider('remote')
        self.assertIsNotNone(remote)
        self.assertEqual(remote.type, 'openai')
        self.assertIn('text', remote.models)
    
    def test_provider_capabilities(self):
        """Test provider capabilities parsing."""
        config = Config.from_yaml()
        
        local = config.get_provider('local')
        self.assertIsNotNone(local.capabilities)
        self.assertIn('max_context', local.capabilities)
        self.assertIn('tool_use', local.capabilities)
        self.assertIn('agentic', local.capabilities)
        
        remote = config.get_provider('remote')
        self.assertIsNotNone(remote.capabilities)
        self.assertEqual(remote.capabilities.get('max_context'), 131072)
        self.assertTrue(remote.capabilities.get('tool_use'))
    
    def test_router_config(self):
        """Test router configuration."""
        config = Config.from_yaml()
        
        # Test fast router priority
        self.assertEqual(config.fast_router_priority, ['echo', 'command'])
        
        # Test semantic router priority
        self.assertEqual(config.semantic_router_priority, ['greeting', 'summarize'])
        
        # Test router enabled status
        self.assertTrue(config.routers['echo'].enabled)
        self.assertTrue(config.routers['command'].enabled)
        self.assertTrue(config.routers['greeting'].enabled)
        self.assertTrue(config.routers['summarize'].enabled)
        
        # Test router options
        self.assertEqual(config.routers['command'].options.get('prefix'), 'run:')
    
    def test_router_utterances(self):
        """Test router utterances from YAML."""
        config = Config.from_yaml()
        
        # Test greeting utterances
        greeting_utterances = config.routers['greeting'].options.get('utterances', [])
        self.assertIsInstance(greeting_utterances, list)
        self.assertGreater(len(greeting_utterances), 0)
        self.assertIn('hello', greeting_utterances)
        self.assertIn('hi', greeting_utterances)
        
        # Test summarize utterances
        summarize_utterances = config.routers['summarize'].options.get('utterances', [])
        self.assertIsInstance(summarize_utterances, list)
        self.assertGreater(len(summarize_utterances), 0)
        self.assertIn('summarize', summarize_utterances)
    
    def test_provider_assignments(self):
        """Test default provider assignments."""
        config = Config.from_yaml()
        
        self.assertEqual(config.embedding_provider, 'local')
        self.assertEqual(config.text_provider, 'remote')
        self.assertEqual(config.vision_provider, 'remote')
    
    @patch.dict('os.environ', {'EMBEDDING_PROVIDER': 'custom', 'PORT': '9999'})
    def test_env_override(self):
        """Test environment variable overrides."""
        config = Config.from_yaml()
        
        self.assertEqual(config.embedding_provider, 'custom')
        self.assertEqual(config.port, 9999)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_routing_chain(self):
        """Test complete routing flow."""
        mock_semantic = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.9
        mock_semantic.return_value = mock_result
        
        routers = [
            EchoRouter(),
            CommandRouter(),
            GreetingRouter([(mock_semantic, 0.5, 'embedding')]),
            SummarizeRouter([(mock_semantic, 0.5, 'embedding')])
        ]
        chain = RouterChain(routers)
        
        # Test greeting
        result = chain.route("hello", {})
        self.assertEqual(result.name, "greeting")
        
        # Test command
        result = chain.route("run: ls", {})
        self.assertEqual(result.name, "linux_command")
        
        # Test fallback
        mock_result.name = "other"
        result = chain.route("what is the weather", {})
        self.assertEqual(result.name, "fallback")
        self.assertTrue(result.should_proxy)


class TestRouterFactory(unittest.TestCase):
    """Test router factory."""
    
    def test_create_echo_router(self):
        """Test creating echo router from config."""
        from clawlayer.config import Config
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        factory = RouterFactory(config)
        
        router = factory.create_router('echo')
        self.assertIsNotNone(router)
        self.assertIsInstance(router, EchoRouter)
    
    def test_create_command_router(self):
        """Test creating command router with prefix from config."""
        from clawlayer.config import Config
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        factory = RouterFactory(config)
        
        router = factory.create_router('command')
        self.assertIsNotNone(router)
        self.assertIsInstance(router, CommandRouter)
        self.assertEqual(router.prefix, 'run:')
    
    def test_build_router_chain(self):
        """Test building complete router chain from config."""
        from clawlayer.config import Config
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        
        # Mock _init_semantic_router to avoid network calls
        factory = RouterFactory(config)
        mock_semantic = Mock()
        factory._init_semantic_router = Mock(return_value=mock_semantic)
        
        routers = factory.build_router_chain()
        self.assertIsInstance(routers, list)
        self.assertGreater(len(routers), 0)
        
        # Check router order matches config
        router_types = [type(r).__name__ for r in routers]
        self.assertIn('EchoRouter', router_types)
        self.assertIn('CommandRouter', router_types)


if __name__ == "__main__":
    unittest.main()
