"""Web API endpoints for ClawLayer UI."""

from flask import jsonify, request, Response
from flask_cors import CORS
import yaml
import os
import json
import time
import shutil


def rotate_backups(config_path):
    """Rotate backup files from .9.bak down to .0.bak"""
    # Move .8.bak -> .9.bak, .7.bak -> .8.bak, etc.
    for i in range(8, -1, -1):
        old_backup = f"{config_path}.{i}.bak"
        new_backup = f"{config_path}.{i+1}.bak"
        if os.path.exists(old_backup):
            if os.path.exists(new_backup):
                os.remove(new_backup)
            os.rename(old_backup, new_backup)
    
    # Copy current config to .0.bak
    if os.path.exists(config_path):
        shutil.copy2(config_path, f"{config_path}.0.bak")


def register_web_api(app, stats, config, router_chain):
    """Register web API routes."""
    
    # Enable CORS for Node.js frontend
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}})
    
    @app.route('/api/stats')
    def get_stats():
        """Get current statistics."""
        return jsonify(stats.to_dict())
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current configuration."""
        config_path = os.getenv('CLAWLAYER_CONFIG', 'config.yml')
        example_path = 'config.example.yml'
        
        # Try to load existing config, fallback to example
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            elif os.path.exists(example_path):
                with open(example_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            else:
                return jsonify({'error': 'No config file found'}), 404
            return jsonify(config_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config', methods=['POST'])
    def save_config():
        """Save configuration with backup rotation."""
        config_path = os.getenv('CLAWLAYER_CONFIG', 'config.yml')
        try:
            # Rotate backups if config exists
            if os.path.exists(config_path):
                rotate_backups(config_path)
            
            config_data = request.json
            with open(config_path, 'w') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False)
            return jsonify({'status': 'saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/reload', methods=['POST'])
    def reload_config():
        """Reload configuration (requires restart for now)."""
        return jsonify({
            'status': 'reload_required',
            'message': 'Please restart ClawLayer to apply changes'
        })
    
    @app.route('/api/routers')
    def get_routers():
        """Get list of routers."""
        routers = []
        for router in router_chain.routers:
            routers.append({
                'name': router.__class__.__name__,
                'type': 'fast' if router.__class__.__name__ in ['EchoRouter', 'CommandRouter'] else 'semantic',
                'enabled': True
            })
        return jsonify(routers)
    
    @app.route('/api/test', methods=['POST'])
    def test_route():
        """Test message routing."""
        try:
            message = request.json.get('message', '')
            if not message:
                return jsonify({'error': 'Message required'}), 400
            
            import time
            start = time.time()
            result = router_chain.route(message, {})
            latency = (time.time() - start) * 1000
            
            return jsonify({
                'router': result.name,
                'content': result.content if hasattr(result, 'content') else None,
                'latency_ms': round(latency, 2),
                'should_proxy': result.should_proxy if hasattr(result, 'should_proxy') else False
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/logs')
    def get_logs():
        """Get recent logs."""
        limit = request.args.get('limit', 50, type=int)
        return jsonify(stats.get_recent_logs(limit))
    
    @app.route('/api/events')
    def events():
        """SSE endpoint for real-time updates."""
        def generate():
            while True:
                routers = []
                for router in router_chain.routers:
                    routers.append({
                        'name': router.__class__.__name__,
                        'type': 'fast' if router.__class__.__name__ in ['EchoRouter', 'CommandRouter'] else 'semantic',
                        'enabled': True
                    })
                
                data = {
                    'stats': stats.to_dict(),
                    'logs': stats.get_recent_logs(10),
                    'routers': routers
                }
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(3)
        
        return Response(generate(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
