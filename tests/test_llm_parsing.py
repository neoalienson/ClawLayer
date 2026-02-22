"""Unit tests for LLM response parsing edge cases."""

import unittest
from unittest.mock import Mock, patch
from clawlayer.routers.semantic_base_router import SemanticBaseRouter
from clawlayer.routers.greeting_router import GreetingRouter


class TestLLMResponseParsing(unittest.TestCase):
    """Test LLM response parsing with various formats."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = SemanticBaseRouter()
        self.mock_provider = Mock()
        self.mock_provider.url = "http://test:11434"
        self.mock_provider.type = "ollama"
        
        self.llm_config = {
            'provider': self.mock_provider,
            'model': 'test-model',
            'utterances': ['hello', 'hi'],
            'route_name': 'greeting'
        }
    
    @patch('requests.post')
    def test_plain_json_response(self, mock_post):
        """Test parsing plain JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '{"is_match": true, "confidence": 0.95}'}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertTrue(is_match)
        self.assertEqual(confidence, 0.95)
        self.assertIsNone(stage_data['error'])
    
    @patch('requests.post')
    def test_markdown_wrapped_json(self, mock_post):
        """Test parsing JSON wrapped in markdown code blocks."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '```json\n{"is_match": true, "confidence": 0.95}\n```'}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertTrue(is_match)
        self.assertEqual(confidence, 0.95)
        self.assertIsNone(stage_data['error'])
    
    @patch('requests.post')
    def test_markdown_without_language_tag(self, mock_post):
        """Test parsing JSON in code blocks without language tag."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '```\n{"is_match": false, "confidence": 0.2}\n```'}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("weather", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.2)
        self.assertIsNone(stage_data['error'])
    
    @patch('requests.post')
    def test_invalid_json_response(self, mock_post):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'This is not valid JSON'}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        self.assertIsNotNone(stage_data['error'])
        self.assertIn('JSON parse error', stage_data['error'])
    
    @patch('requests.post')
    def test_malformed_markdown_json(self, mock_post):
        """Test handling of malformed markdown-wrapped JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '```json\n{is_match: true}\n```'}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        self.assertIsNotNone(stage_data['error'])
        self.assertIn('JSON parse error', stage_data['error'])
    
    @patch('requests.post')
    def test_missing_fields_in_json(self, mock_post):
        """Test handling of JSON with missing fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '{"is_match": true}'}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertTrue(is_match)
        self.assertEqual(confidence, 0.0)  # Default when confidence missing
        self.assertIsNone(stage_data['error'])
    
    @patch('requests.post')
    def test_http_error_response(self, mock_post):
        """Test handling of HTTP error responses."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        self.assertIsNotNone(stage_data['error'])
        self.assertIn('HTTP 500', stage_data['error'])
    
    @patch('requests.post')
    def test_network_exception(self, mock_post):
        """Test handling of network exceptions."""
        mock_post.side_effect = Exception("Connection timeout")
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        self.assertIsNotNone(stage_data['error'])
        self.assertIn('Connection timeout', stage_data['error'])
    
    @patch('requests.post')
    def test_empty_content_response(self, mock_post):
        """Test handling of empty content in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': ''}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        self.assertIsNotNone(stage_data['error'])
    
    @patch('requests.post')
    def test_whitespace_only_response(self, mock_post):
        """Test handling of whitespace-only response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '   \n\n   '}}]
        }
        mock_post.return_value = mock_response
        
        is_match, confidence, stage_data = self.router._match_with_llm("hello", self.llm_config)
        
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        self.assertIsNotNone(stage_data['error'])


if __name__ == '__main__':
    unittest.main()


class TestGreetingRouterPreFilter(unittest.TestCase):
    """Test greeting router pre-filter for system messages."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = GreetingRouter()
    
    def test_system_message_prefix(self):
        """Test rejection of messages starting with 'System:'."""
        message = "System: [2026-02-22] Please greet the user."
        result = self.router.route(message, {})
        self.assertIsNone(result)
    
    def test_greet_the_user_instruction(self):
        """Test rejection of messages containing 'greet the user'."""
        message = "A new session was started. Greet the user in your configured persona."
        result = self.router.route(message, {})
        self.assertIsNone(result)
    
    def test_long_system_message(self):
        """Test rejection of very long messages (>500 chars)."""
        message = "x" * 501
        result = self.router.route(message, {})
        self.assertIsNone(result)
    
    def test_please_read_instruction(self):
        """Test rejection of messages with 'please read them'."""
        message = "Please read them now using the Read tool before continuing."
        result = self.router.route(message, {})
        self.assertIsNone(result)
