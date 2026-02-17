"""Additional unit tests for multi-stage cascade and edge cases."""

import unittest
from unittest.mock import Mock, patch
from clawlayer.routers import GreetingRouter, SummarizeRouter, RouteResult
from clawlayer.routers.semantic_base_router import SemanticBaseRouter
from clawlayer.config import Config, ProviderConfig


class TestMultiStageCascade(unittest.TestCase):
    """Test multi-stage cascade functionality."""
    
    def test_cascade_stage_1_high_confidence_match(self):
        """Test that high confidence at stage 1 returns immediately."""
        mock_stage1 = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.95  # High confidence
        mock_stage1.return_value = mock_result
        
        mock_stage2 = Mock()  # Should not be called
        
        router = GreetingRouter([
            (mock_stage1, 0.75, 'embedding'),
            (mock_stage2, 0.6, 'embedding')
        ])
        
        result = router.route("hello", {})
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "greeting")
        mock_stage1.assert_called_once()
        mock_stage2.assert_not_called()  # Stage 2 should not be called
    
    def test_cascade_stage_1_low_confidence_fallback_to_stage_2(self):
        """Test cascade to stage 2 when stage 1 confidence is low."""
        mock_stage1 = Mock()
        mock_result1 = Mock()
        mock_result1.name = "greeting"
        mock_result1.score = 0.65  # Below stage 1 threshold (0.75)
        mock_stage1.return_value = mock_result1
        
        mock_stage2 = Mock()
        mock_result2 = Mock()
        mock_result2.name = "greeting"
        mock_result2.score = 0.70  # Above stage 2 threshold (0.6)
        mock_stage2.return_value = mock_result2
        
        router = GreetingRouter([
            (mock_stage1, 0.75, 'embedding'),
            (mock_stage2, 0.6, 'embedding')
        ])
        
        result = router.route("hey what's up", {})
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "greeting")
        mock_stage1.assert_called_once()
        mock_stage2.assert_called_once()  # Stage 2 should be called
    
    def test_cascade_all_stages_below_threshold(self):
        """Test that no match is returned when all stages fail."""
        mock_stage1 = Mock()
        mock_result1 = Mock()
        mock_result1.name = "greeting"
        mock_result1.score = 0.50  # Below threshold
        mock_stage1.return_value = mock_result1
        
        mock_stage2 = Mock()
        mock_result2 = Mock()
        mock_result2.name = "greeting"
        mock_result2.score = 0.55  # Below threshold
        mock_stage2.return_value = mock_result2
        
        router = GreetingRouter([
            (mock_stage1, 0.75, 'embedding'),
            (mock_stage2, 0.6, 'embedding')
        ])
        
        result = router.route("what's the weather", {})
        
        self.assertIsNone(result)
        mock_stage1.assert_called_once()
        mock_stage2.assert_called_once()
    
    def test_cascade_with_none_matcher(self):
        """Test cascade handles None matchers gracefully."""
        mock_stage2 = Mock()
        mock_result = Mock()
        mock_result.name = "greeting"
        mock_result.score = 0.8
        mock_stage2.return_value = mock_result
        
        router = GreetingRouter([
            (None, 0.75, 'embedding'),  # None matcher
            (mock_stage2, 0.6, 'embedding')
        ])
        
        result = router.route("hello", {})
        
        self.assertIsNotNone(result)
        mock_stage2.assert_called_once()


class TestSemanticBaseRouter(unittest.TestCase):
    """Test SemanticBaseRouter base class."""
    
    @patch('clawlayer.routers.semantic_base_router.requests.post')
    def test_match_with_llm_success(self, mock_post):
        """Test successful LLM matching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"is_match": true, "confidence": 0.85}'
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
            'utterances': ['hello', 'hi'],
            'route_name': 'greeting'
        }
        
        is_match, confidence = router._match_with_llm("hello", llm_config)
        
        self.assertTrue(is_match)
        self.assertEqual(confidence, 0.85)
    
    @patch('clawlayer.routers.semantic_base_router.requests.post')
    def test_match_with_llm_json_parse_error(self, mock_post):
        """Test LLM matching with malformed JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'Yes, this is a greeting with is_match: true'
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
        self.assertTrue(is_match)
        self.assertEqual(confidence, 0.5)
    
    @patch('clawlayer.routers.semantic_base_router.requests.post')
    def test_match_with_llm_network_error(self, mock_post):
        """Test LLM matching with network error."""
        mock_post.side_effect = Exception("Network error")
        
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
    
    def test_match_cascade_returns_correct_stage_index(self):
        """Test that cascade returns correct stage index."""
        mock_stage1 = Mock()
        mock_result1 = Mock()
        mock_result1.name = "greeting"
        mock_result1.score = 0.65  # Below threshold
        mock_stage1.return_value = mock_result1
        
        mock_stage2 = Mock()
        mock_result2 = Mock()
        mock_result2.name = "greeting"
        mock_result2.score = 0.75  # Above threshold
        mock_stage2.return_value = mock_result2
        
        router = SemanticBaseRouter([
            (mock_stage1, 0.75, 'embedding'),
            (mock_stage2, 0.6, 'embedding')
        ])
        
        is_match, confidence, stage_idx = router._match_cascade("hello", "greeting")
        
        self.assertTrue(is_match)
        self.assertEqual(confidence, 0.75)
        self.assertEqual(stage_idx, 2)  # Matched at stage 2


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
        from clawlayer.config import Config
        
        config = Config.from_yaml()
        
        # Modify config to have empty utterances
        config.routers['greeting'].options['utterances'] = []
        
        # Should handle gracefully
        self.assertEqual(config.routers['greeting'].options['utterances'], [])


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
