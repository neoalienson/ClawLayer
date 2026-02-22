"""Unit tests for ClawLayer integration and factory components."""

import unittest
from unittest.mock import Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.routers import (
    GreetingRouter, EchoRouter, CommandRouter, 
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