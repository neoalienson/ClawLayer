"""Unit tests for OpenClaw config injection."""

import unittest
import tempfile
import json
import os
from unittest.mock import patch, Mock

from clawlayer.openclaw_inject import inject_openclaw_config
from clawlayer.config import Config


class TestOpenClawInjection(unittest.TestCase):
    """Test OpenClaw configuration injection."""
    
    def setUp(self):
        """Create temporary config files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_inject_into_empty_config(self):
        """Test injection into empty OpenClaw config."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Verify result
        self.assertEqual(result['provider_name'], 'clawlayer')
        self.assertIn('http://localhost:', result['url'])
        self.assertFalse(result['dry_run'])
        
        # Verify file was modified
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertIn('models', modified_config)
        self.assertIn('providers', modified_config['models'])
        self.assertIn('clawlayer', modified_config['models']['providers'])
        self.assertEqual(modified_config['models']['providers']['clawlayer']['api'], 'openai-completions')
    
    def test_inject_into_existing_providers(self):
        """Test injection into config with existing providers."""
        openclaw_config = {
            "models": {
                "providers": {
                    "existing": {
                        "baseUrl": "http://example.com",
                        "api": "ollama"
                    }
                }
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        inject_openclaw_config(config_path, dry_run=False)
        
        # Verify existing provider is preserved
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertIn('existing', modified_config['models']['providers'])
        self.assertIn('clawlayer', modified_config['models']['providers'])
        self.assertEqual(modified_config['models']['providers']['existing']['baseUrl'], 'http://example.com')
    
    def test_inject_overwrites_existing_clawlayer(self):
        """Test that injection skips existing clawlayer provider."""
        openclaw_config = {
            "models": {
                "providers": {
                    "clawlayer": {
                        "baseUrl": "http://old-url:9999",
                        "api": "old-api"
                    }
                }
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Verify clawlayer was NOT overwritten (skipped)
        self.assertTrue(result['provider_exists'])
        
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        # Should keep old config
        self.assertEqual(modified_config['models']['providers']['clawlayer']['baseUrl'], 'http://old-url:9999')
    
    def test_dry_run_does_not_modify_file(self):
        """Test that dry run doesn't modify the file."""
        openclaw_config = {"providers": {}}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        original_mtime = os.path.getmtime(config_path)
        
        result = inject_openclaw_config(config_path, dry_run=True)
        
        # Verify dry_run flag
        self.assertTrue(result['dry_run'])
        
        # Verify file was not modified
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertEqual(modified_config, openclaw_config)
        self.assertEqual(os.path.getmtime(config_path), original_mtime)
    
    def test_file_not_found(self):
        """Test error handling when OpenClaw config doesn't exist."""
        nonexistent_path = os.path.join(self.temp_dir, 'nonexistent.json')
        
        with self.assertRaises(FileNotFoundError):
            inject_openclaw_config(nonexistent_path)
    
    def test_invalid_json(self):
        """Test error handling for invalid JSON."""
        config_path = os.path.join(self.temp_dir, 'invalid.json')
        
        with open(config_path, 'w') as f:
            f.write('{ invalid json }')
        
        with self.assertRaises(json.JSONDecodeError):
            inject_openclaw_config(config_path)
    
    def test_preserves_other_config_fields(self):
        """Test that injection preserves other OpenClaw config fields."""
        openclaw_config = {
            "agents": {
                "defaults": {
                    "model": "test-model"
                }
            },
            "tools": {
                "allow": []
            },
            "models": {
                "providers": {
                    "existing": {
                        "baseUrl": "http://example.com"
                    }
                }
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        inject_openclaw_config(config_path, dry_run=False)
        
        # Verify all fields are preserved
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertIn('agents', modified_config)
        self.assertIn('tools', modified_config)
        self.assertEqual(modified_config['agents']['defaults']['model'], 'test-model')
        self.assertEqual(modified_config['tools']['allow'], [])
    
    def test_adds_trailing_newline(self):
        """Test that injection adds trailing newline to file."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        inject_openclaw_config(config_path, dry_run=False)
        
        # Verify trailing newline
        with open(config_path, 'rb') as f:
            content = f.read()
        
        self.assertTrue(content.endswith(b'\n'))
    
    def test_uses_clawlayer_port_from_config(self):
        """Test that injection uses port from ClawLayer config."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Verify URL contains port and /v1 endpoint
        self.assertIn('http://localhost:', result['url'])
        self.assertIn('/v1', result['url'])
    
    def test_uses_text_model_from_config(self):
        """Test that injection uses correct model structure."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Verify model is set
        self.assertEqual(result['model'], 'clawlayer/any')
        
        # Verify in file
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertIn('models', modified_config['models']['providers']['clawlayer'])
        self.assertEqual(modified_config['models']['providers']['clawlayer']['models'][0]['id'], 'any')
    
    def test_complex_openclaw_config(self):
        """Test injection into complex OpenClaw config with nested structures."""
        openclaw_config = {
            "agents": {
                "defaults": {
                    "model": {
                        "primary": "test-model"
                    },
                    "models": {
                        "model1": {"alias": "m1"},
                        "model2": {}
                    }
                },
                "list": [
                    {"id": "agent1", "name": "Agent 1"},
                    {"id": "agent2", "name": "Agent 2"}
                ]
            },
            "models": {
                "providers": {
                    "provider1": {
                        "baseUrl": "http://p1.com",
                        "models": [{"id": "model1"}]
                    }
                }
            },
            "tools": {
                "allow": ["tool1", "tool2"]
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        inject_openclaw_config(config_path, dry_run=False)
        
        # Verify complex structure is preserved
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertEqual(len(modified_config['agents']['list']), 2)
        self.assertEqual(modified_config['agents']['defaults']['model']['primary'], 'test-model')
        self.assertIn('provider1', modified_config['models']['providers'])
        self.assertIn('clawlayer', modified_config['models']['providers'])
        self.assertEqual(modified_config['tools']['allow'], ['tool1', 'tool2'])
    
    def test_provider_exists_model_alias_missing(self):
        """Test when provider exists but model alias is missing."""
        openclaw_config = {
            "models": {
                "providers": {
                    "clawlayer": {
                        "baseUrl": "http://localhost:11435/v1",
                        "api": "openai-completions"
                    }
                }
            },
            "agents": {
                "defaults": {
                    "models": {
                        "other/model": {"alias": "other"}
                    }
                }
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Provider exists, model alias should be added
        self.assertTrue(result['provider_exists'])
        self.assertFalse(result['model_alias_exists'])
        
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertIn('clawlayer/any', modified_config['agents']['defaults']['models'])
        self.assertEqual(modified_config['agents']['defaults']['models']['clawlayer/any']['alias'], 'clawlayer')
    
    def test_model_alias_exists_provider_missing(self):
        """Test when model alias exists but provider is missing."""
        openclaw_config = {
            "agents": {
                "defaults": {
                    "models": {
                        "clawlayer/any": {"alias": "clawlayer"}
                    }
                }
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Model alias exists, provider should be added
        self.assertFalse(result['provider_exists'])
        self.assertTrue(result['model_alias_exists'])
        
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertIn('clawlayer', modified_config['models']['providers'])
    
    def test_both_provider_and_alias_exist(self):
        """Test when both provider and model alias already exist."""
        openclaw_config = {
            "models": {
                "providers": {
                    "clawlayer": {
                        "baseUrl": "http://localhost:11435/v1",
                        "api": "openai-completions"
                    }
                }
            },
            "agents": {
                "defaults": {
                    "models": {
                        "clawlayer/any": {"alias": "clawlayer"}
                    }
                }
            }
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        original_content = json.dumps(openclaw_config, indent=2)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Both exist, nothing should be modified
        self.assertTrue(result['provider_exists'])
        self.assertTrue(result['model_alias_exists'])
        
        with open(config_path, 'r') as f:
            modified_content = f.read().strip()
        
        # File should be unchanged (except possibly formatting)
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        self.assertEqual(openclaw_config, modified_config)
    
    def test_empty_agents_section(self):
        """Test injection when agents section is empty."""
        openclaw_config = {
            "agents": {}
        }
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        inject_openclaw_config(config_path, dry_run=False)
        
        with open(config_path, 'r') as f:
            modified_config = json.load(f)
        
        # Should create nested structure
        self.assertIn('defaults', modified_config['agents'])
        self.assertIn('models', modified_config['agents']['defaults'])
        self.assertIn('clawlayer/any', modified_config['agents']['defaults']['models'])
    
    def test_readonly_file_permission(self):
        """Test handling of read-only file."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'readonly.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        # Make file read-only
        os.chmod(config_path, 0o444)
        
        try:
            with self.assertRaises(PermissionError):
                inject_openclaw_config(config_path, dry_run=False)
        finally:
            # Restore write permission for cleanup
            os.chmod(config_path, 0o644)
    
    def test_verbose_output(self):
        """Test verbose mode produces output."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        # Just verify it doesn't crash with verbose=1
        result = inject_openclaw_config(config_path, dry_run=True, verbose=1)
        
        self.assertIsNotNone(result)
    
    def test_changes_made_tracking(self):
        """Test that changes_made list is accurate."""
        openclaw_config = {}
        config_path = os.path.join(self.temp_dir, 'openclaw.json')
        
        with open(config_path, 'w') as f:
            json.dump(openclaw_config, f)
        
        result = inject_openclaw_config(config_path, dry_run=False)
        
        # Should have 2 changes: provider and model alias
        self.assertEqual(len(result['changes_made']), 2)
        self.assertIn('Added clawlayer provider', result['changes_made'])
        self.assertIn('Added clawlayer/any model alias', result['changes_made'])


if __name__ == '__main__':
    unittest.main()
