"""Tests for QuickRouter."""

import unittest
from clawlayer.routers.quick_router import QuickRouter


class TestQuickRouter(unittest.TestCase):
    """Test QuickRouter functionality."""
    
    def setUp(self):
        from clawlayer.config import RouterConfig
        config = RouterConfig(enabled=True, options={
            'patterns': [
                {'pattern': r"^(hi|hello|hey)$", 'response': 'Hi'}
            ]
        })
        self.router = QuickRouter(config)
    
    def test_matches_hi(self):
        """Test that 'hi' matches."""
        result = self.router.route("hi", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "quick")
        self.assertEqual(result.content, "Hi")
    
    def test_matches_hello(self):
        """Test that 'hello' matches."""
        result = self.router.route("hello", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "Hi")
    
    def test_matches_hey(self):
        """Test that 'hey' matches."""
        result = self.router.route("hey", {})
        self.assertIsNotNone(result)
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        for msg in ["HI", "Hello", "HEY", "hElLo"]:
            result = self.router.route(msg, {})
            self.assertIsNotNone(result, f"Failed to match: {msg}")
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        result = self.router.route("  hi  ", {})
        self.assertIsNotNone(result)
    
    def test_search_in_message(self):
        """Test that pattern is found anywhere in message."""
        from clawlayer.config import RouterConfig
        config = RouterConfig(enabled=True, options={
            'patterns': [{'pattern': "greet", 'response': 'Hello!'}]
        })
        router = QuickRouter(config)
        result = router.route("Please greet the user", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.content, 'Hello!')
    
    def test_no_match_different_word(self):
        """Test that different words don't match."""
        result = self.router.route("goodbye", {})
        self.assertIsNone(result)
    
    def test_custom_pattern(self):
        """Test custom pattern."""
        from clawlayer.config import RouterConfig
        config = RouterConfig(enabled=True, options={
            'patterns': [
                {'pattern': r"^(hola|bonjour)$", 'response': 'Hola!'}
            ]
        })
        router = QuickRouter(config)
        
        result = router.route("hola", {})
        self.assertIsNotNone(result)
        self.assertEqual(result.content, 'Hola!')
        
        result = router.route("bonjour", {})
        self.assertIsNotNone(result)
        
        result = router.route("hi", {})
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
