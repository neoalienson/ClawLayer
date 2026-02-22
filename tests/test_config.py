"""Unit tests for ClawLayer configuration."""

import unittest
from unittest.mock import patch
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.config import Config


class TestConfig(unittest.TestCase):
    """Test configuration."""
    
    def test_from_yaml(self):
        config = Config.from_yaml()
        
        self.assertIsNotNone(config.providers)
        self.assertIn('local', config.providers)
        self.assertIn('remote', config.providers)
        self.assertEqual(config.port, 11435)
    
    def test_provider_methods(self):
        config = Config.from_yaml()
        
        # Test embedding provider
        self.assertIsNotNone(config.get_embedding_url())
        self.assertIsNotNone(config.get_embedding_model())
        
        # Test text provider
        self.assertIsNotNone(config.get_text_url())
        self.assertIsNotNone(config.get_text_model())
    
    def test_provider_config(self):
        """Test provider configuration structure."""
        config = Config.from_yaml()
        
        # Test local provider
        local = config.get_provider('local')
        self.assertIsNotNone(local)
        self.assertEqual(local.type, 'ollama')
        self.assertIn('embed', local.models)
        
        # Test remote provider
        remote = config.get_provider('remote')
        self.assertIsNotNone(remote)
        self.assertEqual(remote.type, 'openai')
        self.assertIn('text', remote.models)
    
    def test_provider_capabilities(self):
        """Test provider capabilities parsing."""
        config = Config.from_yaml()
        
        local = config.get_provider('local')
        self.assertIsNotNone(local.capabilities)
        self.assertIn('max_context', local.capabilities)
        self.assertIn('tool_use', local.capabilities)
        self.assertIn('agentic', local.capabilities)
        
        remote = config.get_provider('remote')
        self.assertIsNotNone(remote.capabilities)
        self.assertEqual(remote.capabilities.get('max_context'), 131072)
        self.assertTrue(remote.capabilities.get('tool_use'))
    
    def test_router_config(self):
        """Test router configuration."""
        config = Config.from_yaml()
        
        # Test fast router priority
        self.assertEqual(config.fast_router_priority, ['echo', 'command'])
        
        # Test semantic router priority
        self.assertEqual(config.semantic_router_priority, ['greeting', 'summarize'])
        
        # Test router enabled status
        self.assertTrue(config.routers['echo'].enabled)
        self.assertTrue(config.routers['command'].enabled)
        self.assertTrue(config.routers['greeting'].enabled)
        self.assertTrue(config.routers['summarize'].enabled)
        
        # Test router options
        self.assertEqual(config.routers['command'].options.get('prefix'), 'run:')
    
    def test_router_utterances(self):
        """Test router utterances from YAML."""
        config = Config.from_yaml()
        
        # Test greeting utterances
        greeting_utterances = config.routers['greeting'].options.get('utterances', [])
        self.assertIsInstance(greeting_utterances, list)
        self.assertGreater(len(greeting_utterances), 0)
        self.assertIn('hello', greeting_utterances)
        self.assertIn('hi', greeting_utterances)
        
        # Test summarize utterances
        summarize_utterances = config.routers['summarize'].options.get('utterances', [])
        self.assertIsInstance(summarize_utterances, list)
        self.assertGreater(len(summarize_utterances), 0)
        self.assertIn('summarize', summarize_utterances)
    
    def test_provider_assignments(self):
        """Test default provider assignments."""
        config = Config.from_yaml()
        
        self.assertEqual(config.embedding_provider, 'local')
        self.assertEqual(config.text_provider, 'remote')
        self.assertEqual(config.vision_provider, 'remote')
    
    def test_config_without_env_file(self):
        """Test configuration loading when .env file is missing."""
        # Temporarily rename .env if it exists
        env_path = '.env'
        env_backup = '.env.backup'
        env_existed = False
        
        if os.path.exists(env_path):
            os.rename(env_path, env_backup)
            env_existed = True
        
        try:
            # Should work without .env file
            config = Config.from_yaml()
            self.assertIsNotNone(config)
            self.assertIsNotNone(config.providers)
            self.assertEqual(config.port, 11435)  # Default port
        finally:
            # Restore .env if it existed
            if env_existed and os.path.exists(env_backup):
                os.rename(env_backup, env_path)
    
    @patch.dict('os.environ', {'EMBEDDING_PROVIDER': 'custom', 'PORT': '9999'})
    def test_env_override(self):
        """Test environment variable overrides."""
        config = Config.from_yaml()
        
        self.assertEqual(config.embedding_provider, 'custom')
        self.assertEqual(config.port, 9999)


if __name__ == "__main__":
    unittest.main()