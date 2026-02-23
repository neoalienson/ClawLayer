"""OpenClaw configuration injection utility."""

import json
import os
import sys
from typing import Dict, Any, Tuple

from clawlayer.config import Config


def inject_openclaw_config(openclaw_config_path: str, dry_run: bool = False, verbose: int = 0) -> Dict[str, Any]:
    """Inject ClawLayer provider configuration into OpenClaw config file.
    
    Args:
        openclaw_config_path: Path to OpenClaw config file
        dry_run: If True, don't write changes to file
        verbose: Verbosity level
        
    Returns:
        Dict with injection details
        
    Raises:
        FileNotFoundError: If OpenClaw config file doesn't exist
        json.JSONDecodeError: If OpenClaw config is invalid JSON
    """
    # Load ClawLayer config
    config = Config.from_yaml()
    
    # Get ClawLayer server URL
    clawlayer_url = f"http://localhost:{config.port}/v1"
    
    # Load OpenClaw config
    if not os.path.exists(openclaw_config_path):
        raise FileNotFoundError(f"OpenClaw config file not found: {openclaw_config_path}")
    
    with open(openclaw_config_path, 'r') as f:
        openclaw_config = json.load(f)
    
    # Check if ClawLayer provider already exists
    provider_exists = False
    model_alias_exists = False
    
    # Check in models.providers section (OpenClaw structure)
    if "models" in openclaw_config and "providers" in openclaw_config["models"] and "clawlayer" in openclaw_config["models"]["providers"]:
        provider_exists = True
    
    if ("agents" in openclaw_config and 
        "defaults" in openclaw_config["agents"] and
        "models" in openclaw_config["agents"]["defaults"] and
        "clawlayer/any" in openclaw_config["agents"]["defaults"]["models"]):
        model_alias_exists = True
    
    # Prepare ClawLayer provider entry
    clawlayer_provider = {
        "baseUrl": clawlayer_url,
        "apiKey": "clawlayer-local",
        "api": "openai-completions",
        "models": [
            {
                "id": "any",
                "name": "ClawLayer",
                "reasoning": False,
                "input": ["text"],
                "cost": {
                    "input": 0,
                    "output": 0,
                    "cacheRead": 0,
                    "cacheWrite": 0
                },
                "contextWindow": 16000,
                "maxTokens": 8192
            }
        ]
    }
    
    changes_made = []
    
    # Inject provider if missing
    if not provider_exists:
        # Use models.providers section for OpenClaw
        if "models" not in openclaw_config:
            openclaw_config["models"] = {}
        if "providers" not in openclaw_config["models"]:
            openclaw_config["models"]["providers"] = {}
        openclaw_config["models"]["providers"]["clawlayer"] = clawlayer_provider
        changes_made.append("Added clawlayer provider")
    else:
        changes_made.append("ClawLayer provider already exists (skipped)")
    
    # Inject model alias if missing
    if not model_alias_exists:
        if "agents" not in openclaw_config:
            openclaw_config["agents"] = {}
        if "defaults" not in openclaw_config["agents"]:
            openclaw_config["agents"]["defaults"] = {}
        if "models" not in openclaw_config["agents"]["defaults"]:
            openclaw_config["agents"]["defaults"]["models"] = {}
        
        openclaw_config["agents"]["defaults"]["models"]["clawlayer/any"] = {
            "alias": "clawlayer"
        }
        changes_made.append("Added clawlayer/any model alias")
    else:
        changes_made.append("ClawLayer model alias already exists (skipped)")
    
    # Show what will be injected
    if verbose or dry_run:
        print("\n" + "="*60)
        print("ClawLayer Configuration Status:")
        print("="*60)
        for change in changes_made:
            status = "✓" if "already exists" in change else "+"
            print(f"{status} {change}")
        print("="*60)
        if not provider_exists:
            print("\nProvider configuration:")
            print(json.dumps(clawlayer_provider, indent=2))
        if not model_alias_exists:
            print("\nModel alias:")
            print(json.dumps({"clawlayer/any": {"alias": "clawlayer"}}, indent=2))
        print("="*60 + "\n")
    
    if dry_run:
        if any("skipped" not in c for c in changes_made):
            print(f"📦 DRY RUN: Would modify {openclaw_config_path}")
            print(f"   Changes: {len([c for c in changes_made if 'skipped' not in c])} additions")
        else:
            print(f"✅ DRY RUN: No changes needed - ClawLayer already configured in {openclaw_config_path}")
    else:
        # Only write if changes were made
        if any("skipped" not in c for c in changes_made):
            with open(openclaw_config_path, 'w') as f:
                json.dump(openclaw_config, f, indent=2)
                f.write('\n')  # Add trailing newline
        else:
            print("ℹ️  No changes needed - ClawLayer already configured")
    
    return {
        "provider_name": "clawlayer",
        "url": clawlayer_url,
        "model": "clawlayer/any",
        "config_path": openclaw_config_path,
        "dry_run": dry_run,
        "provider_exists": provider_exists,
        "model_alias_exists": model_alias_exists,
        "changes_made": changes_made
    }
