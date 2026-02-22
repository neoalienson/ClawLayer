"""Unit tests for ClawLayer routers."""

import unittest
from unittest.mock import Mock
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.routers import (
    GreetingRouter, EchoRouter, CommandRouter, 
    SummarizeRouter, RouterChain, RouteResult
)


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
        router1._last_stage_details = []
        
        router2 = Mock()
        router2.route.return_value = RouteResult(name="test")
        router2._last_stage_details = []
        
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
        router._last_stage_details = []
        
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


if __name__ == "__main__":
    unittest.main()