"""Unit tests for multi-stage cascade functionality."""

import unittest
from unittest.mock import Mock, patch
from clawlayer.routers import GreetingRouter
from clawlayer.routers.semantic_base_router import SemanticBaseRouter


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


if __name__ == "__main__":
    unittest.main()