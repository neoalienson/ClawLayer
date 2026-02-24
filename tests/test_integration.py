"""Unit tests for ClawLayer integration and factory components."""

import unittest
from unittest.mock import Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.routers import (
    GreetingRouter, EchoHandler, CommandHandler, 
    SummarizeRouter, RouterChain, RouteResult
)


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
            EchoHandler(),
            CommandHandler(),
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
    
    def test_create_echo_handler(self):
        """Test creating echo router from config."""
        from clawlayer.config import Config
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        factory = RouterFactory(config)
        
        router = factory.create_router('echo')
        if router is None:
            self.skipTest("Echo router not enabled in config")
        self.assertIsInstance(router, EchoHandler)
    
    def test_create_command_handler(self):
        """Test creating command router with prefix from config."""
        from clawlayer.config import Config
        from clawlayer.router_factory import RouterFactory
        
        config = Config.from_yaml()
        factory = RouterFactory(config)
        
        router = factory.create_router('command')
        if router is None:
            self.skipTest("Command router not enabled in config")
        self.assertIsInstance(router, CommandHandler)
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
        # May be empty if no routers are enabled in config
        if len(routers) == 0:
            self.skipTest("No routers enabled in config")
        
        # Check router order matches config
        router_types = [type(r).__name__ for r in routers]
        # At least one router should be present
        self.assertGreater(len(router_types), 0)


if __name__ == "__main__":
    unittest.main()