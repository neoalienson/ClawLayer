"""Unit tests for terminal flag in handlers."""

import unittest
from unittest.mock import Mock
from clawlayer.routers import Router, RouteResult, RouterChain


class TestTerminalFlag(unittest.TestCase):
    """Test terminal flag behavior in handlers."""
    
    def test_terminal_true_stops_processing(self):
        """Test that terminal=True stops processing chain."""
        router1 = Mock()
        router1.route.return_value = RouteResult(name="handler1", content="response1", terminal=True)
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="handler2", content="response2")
        
        chain = RouterChain([router1, router2])
        result = chain.route("test message", {})
        
        self.assertEqual(result.name, "handler1")
        router1.route.assert_called_once()
        router2.route.assert_not_called()
    
    def test_terminal_false_continues_processing(self):
        """Test that terminal=False continues to next handler."""
        router1 = Mock()
        router1.route.return_value = RouteResult(name="handler1", content="response1", terminal=False)
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="handler2", content="response2", terminal=True)
        router2._last_stage_details = []
        
        chain = RouterChain([router1, router2])
        result = chain.route("test message", {})
        
        self.assertEqual(result.name, "handler2")
        router1.route.assert_called_once()
        router2.route.assert_called_once()
    
    def test_terminal_default_is_true(self):
        """Test that terminal defaults to True."""
        result = RouteResult(name="test")
        self.assertTrue(result.terminal)
    
    def test_multiple_non_terminal_handlers(self):
        """Test chain with multiple non-terminal handlers."""
        router1 = Mock()
        router1.route.return_value = RouteResult(name="handler1", terminal=False)
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="handler2", terminal=False)
        router2._last_stage_details = []
        
        router3 = Mock()
        router3.route.return_value = RouteResult(name="handler3", terminal=True)
        router3._last_stage_details = []
        
        chain = RouterChain([router1, router2, router3])
        result = chain.route("test message", {})
        
        self.assertEqual(result.name, "handler3")
        router1.route.assert_called_once()
        router2.route.assert_called_once()
        router3.route.assert_called_once()
    
    def test_no_match_with_non_terminal(self):
        """Test that None result continues chain even with terminal=False."""
        router1 = Mock()
        router1.route.return_value = None
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="handler2", terminal=True)
        router2._last_stage_details = []
        
        chain = RouterChain([router1, router2])
        result = chain.route("test message", {})
        
        self.assertEqual(result.name, "handler2")
        router1.route.assert_called_once()
        router2.route.assert_called_once()
    
    def test_all_non_terminal_falls_back(self):
        """Test that all non-terminal handlers eventually fall back to LLM."""
        router1 = Mock()
        router1.route.return_value = RouteResult(name="handler1", terminal=False)
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="handler2", terminal=False)
        router2._last_stage_details = []
        
        chain = RouterChain([router1, router2])
        result = chain.route("test message", {})
        
        # Should fall back to LLM since no terminal handler matched
        self.assertEqual(result.name, "fallback")
        self.assertTrue(result.should_proxy)
    
    def test_terminal_with_tool_calls(self):
        """Test terminal flag works with tool_calls."""
        router1 = Mock()
        router1.route.return_value = RouteResult(
            name="command", 
            tool_calls=[{"id": "1", "function": {"name": "exec"}}],
            terminal=True
        )
        router1._last_stage_details = []
        
        router2 = Mock()
        
        chain = RouterChain([router1, router2])
        result = chain.route("run: ls", {})
        
        self.assertEqual(result.name, "command")
        self.assertIsNotNone(result.tool_calls)
        router2.route.assert_not_called()
    
    def test_terminal_with_should_proxy(self):
        """Test terminal flag with should_proxy=True."""
        router1 = Mock()
        router1.route.return_value = RouteResult(
            name="proxy_handler",
            should_proxy=True,
            terminal=True
        )
        router1._last_stage_details = []
        
        router2 = Mock()
        
        chain = RouterChain([router1, router2])
        result = chain.route("test", {})
        
        self.assertEqual(result.name, "proxy_handler")
        self.assertTrue(result.should_proxy)
        router2.route.assert_not_called()
    
    def test_empty_chain_falls_back(self):
        """Test empty chain falls back to LLM."""
        chain = RouterChain([])
        result = chain.route("test", {})
        
        self.assertEqual(result.name, "fallback")
        self.assertTrue(result.should_proxy)
    
    def test_all_handlers_return_none(self):
        """Test all handlers returning None falls back to LLM."""
        router1 = Mock()
        router1.route.return_value = None
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = None
        router2._last_stage_details = []
        
        chain = RouterChain([router1, router2])
        result = chain.route("test", {})
        
        self.assertEqual(result.name, "fallback")
        self.assertTrue(result.should_proxy)
        router1.route.assert_called_once()
        router2.route.assert_called_once()
    
    def test_terminal_false_then_none_continues(self):
        """Test terminal=False followed by None continues chain."""
        router1 = Mock()
        router1.route.return_value = RouteResult(name="handler1", terminal=False)
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = None
        router2._last_stage_details = []
        
        router3 = Mock()
        router3.route.return_value = RouteResult(name="handler3", terminal=True)
        router3._last_stage_details = []
        
        chain = RouterChain([router1, router2, router3])
        result = chain.route("test", {})
        
        self.assertEqual(result.name, "handler3")
        router1.route.assert_called_once()
        router2.route.assert_called_once()
        router3.route.assert_called_once()
    
    def test_tried_routers_includes_non_terminal(self):
        """Test tried_routers includes non-terminal handlers."""
        router1 = Mock()
        router1.route.return_value = RouteResult(name="handler1", terminal=False)
        router1._last_stage_details = []
        router1.__class__.__name__ = "Handler1"
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="handler2", terminal=True)
        router2._last_stage_details = []
        router2.__class__.__name__ = "Handler2"
        
        chain = RouterChain([router1, router2])
        result = chain.route("test", {})
        
        self.assertEqual(len(result.tried_routers), 2)
        self.assertIn("Handler1", result.tried_routers[0]['name'])
        self.assertIn("Handler2", result.tried_routers[1]['name'])


if __name__ == "__main__":
    unittest.main()
