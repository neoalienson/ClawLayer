"""Unit tests for ClawLayer web API."""

import unittest
from unittest.mock import Mock, patch
import json
import os
import sys
import yaml
from flask import Flask

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawlayer.web_api import register_web_api


class TestWebAPI(unittest.TestCase):
    """Test web API endpoints including SSE."""
    
    def setUp(self):
        self.app = Flask(__name__)
        self.stats = Mock()
        self.stats.to_dict.return_value = {'requests': 10, 'router_hits': {}}
        self.stats.get_recent_logs.return_value = [{'message': 'test', 'timestamp': 123}]
        self.config = Mock()
        self.router_chain = Mock()
        
        register_web_api(self.app, self.stats, self.config, self.router_chain)
        self.client = self.app.test_client()
    
    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['requests'], 10)
    
    def test_get_logs(self):
        response = self.client.get('/api/logs')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['message'], 'test')
    
    def test_sse_events_endpoint(self):
        """Test SSE events endpoint returns proper headers."""
        # Mock router_chain.routers to be iterable
        self.router_chain.routers = []
        
        response = self.client.get('/api/events')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/event-stream')
        self.assertIn('no-cache', response.headers.get('Cache-Control', ''))
        self.assertIn('keep-alive', response.headers.get('Connection', ''))


class TestBackupRotation(unittest.TestCase):
    """Test backup file rotation functionality."""
    
    def setUp(self):
        self.test_dir = '/tmp/clawlayer_test'
        os.makedirs(self.test_dir, exist_ok=True)
        self.config_path = os.path.join(self.test_dir, 'test_config.yml')
    
    def tearDown(self):
        # Clean up test files
        import glob
        for f in glob.glob(f"{self.config_path}*"):
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)
    
    def test_backup_rotation_new_file(self):
        """Test backup rotation when no existing backups."""
        from clawlayer.web_api import rotate_backups
        
        # Create initial config
        with open(self.config_path, 'w') as f:
            f.write('test: config')
        
        rotate_backups(self.config_path)
        
        # Should create .0.bak
        self.assertTrue(os.path.exists(f"{self.config_path}.0.bak"))
        with open(f"{self.config_path}.0.bak", 'r') as f:
            self.assertEqual(f.read(), 'test: config')
    
    def test_backup_rotation_existing_backups(self):
        """Test backup rotation with existing backup files."""
        from clawlayer.web_api import rotate_backups
        
        # Create config and existing backups
        with open(self.config_path, 'w') as f:
            f.write('current: config')
        with open(f"{self.config_path}.0.bak", 'w') as f:
            f.write('backup: 0')
        with open(f"{self.config_path}.1.bak", 'w') as f:
            f.write('backup: 1')
        
        rotate_backups(self.config_path)
        
        # Check rotation
        with open(f"{self.config_path}.0.bak", 'r') as f:
            self.assertEqual(f.read(), 'current: config')
        with open(f"{self.config_path}.1.bak", 'r') as f:
            self.assertEqual(f.read(), 'backup: 0')
        with open(f"{self.config_path}.2.bak", 'r') as f:
            self.assertEqual(f.read(), 'backup: 1')
    
    def test_backup_rotation_max_backups(self):
        """Test backup rotation with maximum number of backups."""
        from clawlayer.web_api import rotate_backups
        
        # Create config and 10 backups (0-9)
        with open(self.config_path, 'w') as f:
            f.write('current: config')
        
        for i in range(10):
            with open(f"{self.config_path}.{i}.bak", 'w') as f:
                f.write(f'backup: {i}')
        
        rotate_backups(self.config_path)
        
        # .9.bak should be removed, others shifted
        self.assertFalse(os.path.exists(f"{self.config_path}.10.bak"))
        
        with open(f"{self.config_path}.0.bak", 'r') as f:
            self.assertEqual(f.read(), 'current: config')
        with open(f"{self.config_path}.9.bak", 'r') as f:
            self.assertEqual(f.read(), 'backup: 8')
    
    @patch.dict('os.environ', {'CLAWLAYER_CONFIG': '/tmp/test_config.yml'})
    def test_save_config_with_backup(self):
        """Test config save API creates backups."""
        app = Flask(__name__)
        stats = Mock()
        config = Mock()
        router_chain = Mock()
        
        register_web_api(app, stats, config, router_chain)
        client = app.test_client()
        
        config_path = '/tmp/test_config.yml'
        
        # Create initial config
        with open(config_path, 'w') as f:
            f.write('initial: config')
        
        # Save new config
        response = client.post('/api/config', 
                             json={'new': 'config'},
                             content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check backup was created
        self.assertTrue(os.path.exists(f"{config_path}.0.bak"))
        with open(f"{config_path}.0.bak", 'r') as f:
            self.assertEqual(f.read(), 'initial: config')
        
        # Clean up
        for f in [config_path, f"{config_path}.0.bak"]:
            if os.path.exists(f):
                os.remove(f)
    
    def test_config_api_missing_config_yml(self):
        """Test config API when config.yml is missing but config.example.yml exists."""
        app = Flask(__name__)
        stats = Mock()
        config = Mock()
        router_chain = Mock()
        
        register_web_api(app, stats, config, router_chain)
        client = app.test_client()
        
        # Temporarily rename config.yml if it exists
        config_path = 'config.yml'
        config_backup = 'config.yml.test_backup'
        config_existed = False
        
        if os.path.exists(config_path):
            os.rename(config_path, config_backup)
            config_existed = True
        
        try:
            # Should load config.example.yml when config.yml is missing
            response = client.get('/api/config')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertIn('providers', data)
            self.assertIn('server', data)
        finally:
            # Restore config.yml if it existed
            if config_existed and os.path.exists(config_backup):
                os.rename(config_backup, config_path)
    
    def test_saved_yaml_is_valid(self):
        """Test that saved YAML can be loaded and parsed correctly."""
        app = Flask(__name__)
        stats = Mock()
        config = Mock()
        router_chain = Mock()
        
        register_web_api(app, stats, config, router_chain)
        client = app.test_client()
        
        test_config_path = '/tmp/test_saved_config.yml'
        
        # Test config data
        test_config = {
            'server': {'port': 8080},
            'providers': {
                'test_provider': {
                    'url': 'http://test.com',
                    'type': 'ollama',
                    'models': {'text': 'test-model'}
                }
            },
            'defaults': {
                'text_provider': 'test_provider'
            },
            'routers': {
                'fast': {
                    'echo': {'enabled': True}
                }
            }
        }
        
        try:
            # Save config via API
            with patch.dict('os.environ', {'CLAWLAYER_CONFIG': test_config_path}):
                response = client.post('/api/config',
                                     json=test_config,
                                     content_type='application/json')
                self.assertEqual(response.status_code, 200)
            
            # Verify file was created
            self.assertTrue(os.path.exists(test_config_path))
            
            # Load and verify YAML is valid
            with open(test_config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Verify structure and content
            self.assertEqual(loaded_config['server']['port'], 8080)
            self.assertEqual(loaded_config['providers']['test_provider']['url'], 'http://test.com')
            self.assertEqual(loaded_config['defaults']['text_provider'], 'test_provider')
            self.assertTrue(loaded_config['routers']['fast']['echo']['enabled'])
            
        finally:
            # Clean up
            for f in [test_config_path, f"{test_config_path}.0.bak"]:
                if os.path.exists(f):
                    os.remove(f)


if __name__ == "__main__":
    unittest.main()