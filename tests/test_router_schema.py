"""Unit tests for router SCHEMA enforcement."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.routers import Router, RouteResult


class TestRouterSchemaEnforcement(unittest.TestCase):
    """Test that routers must define SCHEMA when registered."""
    
    def test_register_without_schema_raises_error(self):
        """Test that registering a router without SCHEMA raises AttributeError."""
        with self.assertRaises(AttributeError) as cm:
            @Router.register('bad_router')
            class BadRouter(Router):
                def route(self, message, context):
                    return None
        
        self.assertIn("must define SCHEMA", str(cm.exception))
        self.assertIn("bad_router", str(cm.exception))
    
    def test_register_with_schema_succeeds(self):
        """Test that registering a router with SCHEMA succeeds."""
        @Router.register('good_router')
        class GoodRouter(Router):
            SCHEMA = {'test': {'type': 'string'}}
            
            def route(self, message, context):
                return None
        
        self.assertIn('good_router', Router._registry)
        self.assertEqual(Router._registry['good_router'], GoodRouter)
    
    def test_quick_handler_has_schema(self):
        """Test that QuickHandler has SCHEMA defined."""
        from clawlayer.routers.quick_handler import QuickHandler
        
        self.assertTrue(hasattr(QuickHandler, 'SCHEMA'))
        self.assertIsInstance(QuickHandler.SCHEMA, dict)
        self.assertIn('patterns', QuickHandler.SCHEMA)


if __name__ == "__main__":
    unittest.main()
