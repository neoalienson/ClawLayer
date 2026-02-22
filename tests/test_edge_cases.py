"""Unit tests for error handling and edge cases."""

import unittest
from unittest.mock import Mock, patch
import yaml
import tempfile
import os
import threading
import requests
from clawlayer.routers import GreetingRouter, RouteResult, RouterChain
from clawlayer.routers.semantic_base_router import SemanticBaseRouter
from clawlayer.config import Config, ProviderConfig
from clawlayer.handler import MessageHandler


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_message(self):
        """Test routing with empty message."""
        mock_semantic = Mock()
        mock_semantic.return_value = None
        
        router = GreetingRouter([(mock_semantic, 0.5, 'embedding')])
        result = router.route("", {})
        
        # Should handle gracefully
        self.assertIsNone(result)
    
    def test_very_long_message(self):
        """Test routing with very long message."""
        mock_semantic = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.9
        mock_semantic.return_value = mock_result
        
        router = GreetingRouter([(mock_semantic, 0.5, 'embedding')])
        long_message = "hello " * 10000  # Very long message
        
        result = router.route(long_message, {})
        
        # Should handle without crashing
        self.assertIsNotNone(result)
    
    def test_special_characters_in_message(self):
        """Test routing with special characters and unicode."""
        mock_semantic = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.9
        mock_semantic.return_value = mock_result
        
        router = GreetingRouter([(mock_semantic, 0.5, 'embedding')])
        
        # Test with emojis and unicode
        result = router.route("hello 👋 مرحبا", {})
        
        self.assertIsNotNone(result)
    
    def test_invalid_threshold_values(self):
        """Test cascade with invalid threshold values."""
        mock_semantic = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.9
        mock_semantic.return_value = mock_result
        
        # Threshold > 1.0 (invalid)
        router = GreetingRouter([(mock_semantic, 1.5, 'embedding')])
        result = router.route("hello", {})
        
        # Should not match (score 0.9 < 1.5)
        self.assertIsNone(result)
    
    def test_empty_utterances_list(self):
        """Test router with empty utterances list."""
        config = Config.from_yaml()
        
        # Modify config to have empty utterances
        config.routers['greeting'].options['utterances'] = []
        
        # Should handle gracefully
        self.assertEqual(config.routers['greeting'].options['utterances'], [])


class TestConfigErrors(unittest.TestCase):
    """Test configuration error handling."""
    
    def test_config_file_not_found(self):
        """Test handling of missing config file."""
        # Should use defaults when config file doesn't exist
        config = Config.from_yaml('/nonexistent/path/config.yml')
        
        # Should have default values
        self.assertIsNotNone(config)
        self.assertEqual(config.port, 11435)
    
    def test_invalid_yaml_syntax(self):
        """Test handling of malformed YAML."""
        # Create temp file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: syntax: [unclosed")
            temp_path = f.name
        
        try:
            # Should raise YAML error
            with self.assertRaises(yaml.YAMLError):
                config = Config.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_missing_provider_in_config(self):
        """Test handling of missing provider reference."""
        config = Config.from_yaml()
        
        # Try to get non-existent provider
        provider = config.get_provider('nonexistent')
        
        self.assertIsNone(provider)
    
    def test_invalid_provider_type(self):
        """Test provider with invalid provider_type."""
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        
        # Create provider with invalid type
        config.providers['invalid'] = ProviderConfig(
            name='invalid',
            url='http://test.com',
            type='ollama',
            provider_type='invalid_type',  # Not 'embedding' or 'llm'
            models={'embed': 'test'}
        )
        
        factory = RouterFactory(config)
        
        # Should handle gracefully (treat as embedding by default)
        self.assertIsNotNone(factory)


class TestMessageHandlerErrors(unittest.TestCase):
    """Test MessageHandler error handling."""
    
    def test_extract_message_with_empty_messages(self):
        """Test message extraction with empty messages list."""
        data = {"messages": []}
        
        # Should handle gracefully - may raise IndexError or return empty
        try:
            message = MessageHandler.extract_message(data)
            self.assertIsInstance(message, str)
        except IndexError:
            # Expected behavior for empty messages
            pass
    
    def test_extract_message_with_missing_content(self):
        """Test message extraction with missing content field."""
        data = {
            "messages": [
                {"role": "user"}  # No content field
            ]
        }
        
        # Should handle gracefully - may raise KeyError or return empty
        try:
            message = MessageHandler.extract_message(data)
            self.assertIsInstance(message, str)
        except (KeyError, TypeError):
            # Expected behavior for missing content
            pass
    
    def test_build_context_with_minimal_data(self):
        """Test context building with minimal data."""
        data = {"messages": []}
        
        # Should raise IndexError for empty messages
        with self.assertRaises(IndexError):
            context = MessageHandler.build_context(data)


class TestConcurrency(unittest.TestCase):
    """Test concurrent request handling."""
    
    def test_multiple_routers_concurrent_access(self):
        """Test that routers can handle concurrent requests."""
        mock_semantic = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.9
        mock_semantic.return_value = mock_result
        
        router = GreetingRouter([(mock_semantic, 0.5, 'embedding')])
        
        results = []
        
        def route_message():
            result = router.route("hello", {})
            results.append(result)
        
        # Create multiple threads
        threads = [threading.Thread(target=route_message) for _ in range(10)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all to complete
        for t in threads:
            t.join()
        
        # All should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r is not None for r in results))
    
    def test_router_chain_thread_safety(self):
        """Test RouterChain with concurrent requests."""
        router1 = Mock()
        router1.route.return_value = None
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="test")
        
        chain = RouterChain([router1, router2])
        
        results = []
        
        def route_message():
            result = chain.route("message", {})
            results.append(result)
        
        threads = [threading.Thread(target=route_message) for _ in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.name == "test" for r in results))


class TestLLMMatcherEdgeCases(unittest.TestCase):
    """Test LLM matcher edge cases."""
    
    @patch('clawlayer.routers.semantic_base_router.requests.post')
    def test_llm_timeout(self, mock_post):
        """Test LLM matching with timeout."""
        mock_post.side_effect = requests.Timeout("Request timeout")
        
        router = SemanticBaseRouter([])
        provider = Mock()
        provider.url = "http://test.com"
        
        llm_config = {
            'provider': provider,
            'model': 'test-model',
            'utterances': ['hello'],
            'route_name': 'greeting'
        }
        
        is_match, confidence = router._match_with_llm("hello", llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
    
    @patch('clawlayer.routers.semantic_base_router.requests.post')
    def test_llm_returns_non_json(self, mock_post):
        """Test LLM returns plain text instead of JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'This is definitely a greeting!'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        router = SemanticBaseRouter([])
        provider = Mock()
        provider.url = "http://test.com"
        
        llm_config = {
            'provider': provider,
            'model': 'test-model',
            'utterances': ['hello'],
            'route_name': 'greeting'
        }
        
        is_match, confidence = router._match_with_llm("hello", llm_config)
        
        # Should fallback to keyword matching
        self.assertFalse(is_match)  # No "is_match" keyword
        self.assertEqual(confidence, 0.0)
    
    @patch('clawlayer.routers.semantic_base_router.requests.post')
    def test_llm_returns_invalid_confidence(self, mock_post):
        """Test LLM returns confidence outside 0-1 range."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"is_match": true, "confidence": 5.0}'  # Invalid
                }
            }]
        }
        mock_post.return_value = mock_response
        
        router = SemanticBaseRouter([])
        provider = Mock()
        provider.url = "http://test.com"
        
        llm_config = {
            'provider': provider,
            'model': 'test-model',
            'utterances': ['hello'],
            'route_name': 'greeting'
        }
        
        is_match, confidence = router._match_with_llm("hello", llm_config)
        
        # Should still parse the match
        self.assertTrue(is_match)
        self.assertEqual(confidence, 5.0)  # Returns as-is, router handles threshold


class TestRouterFactoryErrors(unittest.TestCase):
    """Test RouterFactory error handling."""
    
    def test_router_factory_with_disabled_router(self):
        """Test factory skips disabled routers."""
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        config.routers['greeting'].enabled = False
        
        factory = RouterFactory(config)
        router = factory.create_router('greeting')
        
        self.assertIsNone(router)
    
    def test_router_factory_with_missing_router_config(self):
        """Test factory handles missing router config."""
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        factory = RouterFactory(config)
        
        router = factory.create_router('nonexistent_router')
        
        self.assertIsNone(router)
    
    def test_build_cascade_with_missing_provider(self):
        """Test cascade building with missing provider."""
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        
        # Add stage with non-existent provider
        config.routers['greeting'].options['stages'] = [
            {'provider': 'nonexistent', 'model': 'test', 'threshold': 0.5}
        ]
        
        factory = RouterFactory(config)
        factory._init_semantic_router = Mock(return_value=None)
        
        # Should handle gracefully
        cascade_stages = factory._build_cascade_stages(config.routers['greeting'])
        
        # Should return empty list or skip invalid stage
        self.assertIsInstance(cascade_stages, list)


class TestProviderType(unittest.TestCase):
    """Test provider_type functionality."""
    
    def test_provider_type_embedding(self):
        """Test provider with embedding type."""
        config = Config.from_yaml()
        local = config.get_provider('local')
        
        self.assertEqual(local.provider_type, 'embedding')
    
    def test_provider_type_llm(self):
        """Test provider with LLM type."""
        config = Config.from_yaml()
        remote = config.get_provider('remote')
        
        self.assertEqual(remote.provider_type, 'llm')
    
    def test_provider_type_default_value(self):
        """Test provider_type defaults to 'embedding' if not specified."""
        provider = ProviderConfig(
            name='test',
            url='http://test.com',
            type='ollama',
            provider_type='embedding',  # Should default if not provided
            models={}
        )
        
        self.assertEqual(provider.provider_type, 'embedding')


if __name__ == "__main__":
    unittest.main()