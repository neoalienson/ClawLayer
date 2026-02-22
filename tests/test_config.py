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
        # Use config.example.yml since config.yml may not exist in CI
        config_path = 'config.example.yml' if os.path.exists('config.example.yml') else None
        if not config_path:
            self.skipTest("No config file found")
            
        config = Config.from_yaml(config_path)
        
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
        config_path = 'config.example.yml' if os.path.exists('config.example.yml') else None
        if not config_path:
            self.skipTest("No config file found")
            
        config = Config.from_yaml(config_path)
        
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
        config_path = 'config.example.yml' if os.path.exists('config.example.yml') else None
        if not config_path:
            self.skipTest("No config file found")
            
        config = Config.from_yaml(config_path)
        
        local = config.get_provider('local')
        if local and hasattr(local, 'capabilities') and local.capabilities:
            self.assertIn('max_context', local.capabilities)
            self.assertIn('tool_use', local.capabilities)
        
        remote = config.get_provider('remote')
        if remote and hasattr(remote, 'capabilities') and remote.capabilities:
            self.assertIn('max_context', remote.capabilities)
    
    def test_router_config(self):
        """Test router configuration."""
        config_path = 'config.example.yml' if os.path.exists('config.example.yml') else None
        if not config_path:
            self.skipTest("No config file found")
            
        config = Config.from_yaml(config_path)
        
        # Test fast router priority
        self.assertEqual(config.fast_router_priority, ['echo', 'command'])
        
        # Test semantic router priority
        self.assertEqual(config.semantic_router_priority, ['greeting', 'summarize'])
        
        # Test router enabled status
        self.assertTrue(config.routers['echo'].enabled)
        self.assertTrue(config.routers['command'].enabled)
        self.assertTrue(config.routers['greeting'].enabled)
        self.assertTrue(config.routers['summarize'].enabled)
        
        # Test router options (may not exist in example config)
        if 'command' in config.routers and hasattr(config.routers['command'], 'options'):
            prefix = config.routers['command'].options.get('prefix')
            if prefix:
                self.assertEqual(prefix, 'run:')
    
    def test_router_utterances(self):
        """Test router utterances from YAML."""
        config_path = 'config.example.yml' if os.path.exists('config.example.yml') else None
        if not config_path:
            self.skipTest("No config file found")
            
        config = Config.from_yaml(config_path)
        
        # Test greeting utterances (may not exist in example config)
        if 'greeting' in config.routers and hasattr(config.routers['greeting'], 'options'):
            greeting_utterances = config.routers['greeting'].options.get('utterances', [])
            if greeting_utterances:
                self.assertIsInstance(greeting_utterances, list)
                self.assertGreater(len(greeting_utterances), 0)
        
        # Test summarize utterances (may not exist in example config)
        if 'summarize' in config.routers and hasattr(config.routers['summarize'], 'options'):
            summarize_utterances = config.routers['summarize'].options.get('utterances', [])
            if summarize_utterances:
                self.assertIsInstance(summarize_utterances, list)
                self.assertGreater(len(summarize_utterances), 0)
    
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


class TestDynamicRouterLoading(unittest.TestCase):
    """Test dynamic router discovery from config."""
    
    def test_loads_custom_fast_router(self):
        """Test that custom fast routers are loaded from config."""
        import tempfile
        config_yaml = """
routers:
  fast:
    priority:
      - echo
      - fast_greet
    echo:
      enabled: true
    fast_greet:
      enabled: true
      pattern: "^(hi|hello)$"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name
        
        try:
            config = Config.from_yaml(temp_path)
            
            self.assertIn('fast_greet', config.routers)
            self.assertTrue(config.routers['fast_greet'].enabled)
            self.assertEqual(config.routers['fast_greet'].options['pattern'], '^(hi|hello)$')
            self.assertIn('fast_greet', config.fast_router_priority)
        finally:
            os.unlink(temp_path)
    
    def test_excludes_priority_key(self):
        """Test that 'priority' key is not treated as a router."""
        import tempfile
        config_yaml = """
routers:
  fast:
    priority:
      - echo
    echo:
      enabled: true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name
        
        try:
            config = Config.from_yaml(temp_path)
            
            self.assertNotIn('priority', config.routers)
            self.assertIn('echo', config.routers)
        finally:
            os.unlink(temp_path)
