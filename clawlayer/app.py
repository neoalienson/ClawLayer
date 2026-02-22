"""Flask application for ClawLayer."""

from flask import Flask, request, jsonify, Response
import argparse
import sys
import json

from clawlayer.config import Config, RouterConfig, ProviderConfig
from clawlayer.routers import RouterChain
from clawlayer.router_factory import RouterFactory
from clawlayer.handler import MessageHandler, ResponseGenerator
from clawlayer.proxy import LLMProxy
from clawlayer.stats import StatsCollector
from clawlayer.web_api import register_web_api


class ClawLayerApp:
    """Main application class."""
    
    def __init__(self, config: Config, router_chain: RouterChain, llm_proxy: LLMProxy, verbose: int = 0):
        self.config = config
        self.router_chain = router_chain
        self.llm_proxy = llm_proxy
        self.verbose = verbose
        self.stats = StatsCollector()
        self.app = Flask(__name__)
        self.app.config['JSON_AS_ASCII'] = False  # Allow unicode in JSON responses
        self._setup_routes()
        register_web_api(self.app, self.stats, self.config, self.router_chain)
    
    def _setup_routes(self):
        """Setup Flask routes."""
        self.app.route("/v1/models", methods=["GET"])(self.models)
        self.app.route("/v1/chat/completions", methods=["POST"])(self.chat_completions)
        self.app.route("/api/logs/<int:log_id>", methods=["DELETE"])(self.delete_log)
    
    def models(self):
        """Return available models."""
        return jsonify({"models": ["clawlayer"]})
    
    def chat_completions(self):
        """Handle chat completion requests."""
        import time
        start_time = time.time()
        
        data = request.json
        
        if self.verbose >= 2:
            self._log(f"📦 RAW REQUEST: {json.dumps(data, indent=2)}")
        
        # Extract message and build context
        message = MessageHandler.extract_message(data)
        context = MessageHandler.build_context(data)
        
        if self.verbose:
            self._log(f"📨 REQUEST: {message}")
        
        # Route the message
        route_result = self.router_chain.route(message, context)
        
        if self.verbose:
            self._log(f"🎯 ROUTE: {route_result.name}")
        
        response_data = None
        error_info = None
        fallback_request = None
        try:
            # Handle response
            if route_result.should_proxy:
                response_tuple = self._handle_proxy(data, context["stream"], route_result.name)
                # Debug: print what we got
                if self.verbose:
                    self._log(f"🔍 PROXY RESPONSE TYPE: {type(response_tuple)}, LEN: {len(response_tuple) if isinstance(response_tuple, tuple) else 'N/A'}")
                
                # Handle 4-element tuple: (response_obj, status_code, fallback_request, response_data)
                if isinstance(response_tuple, tuple) and len(response_tuple) == 4:
                    response_obj, status_code, fallback_request, response_data = response_tuple
                    
                    # Check if this is an error response (status code 500)
                    if status_code == 500:
                        # Error case - extract error details
                        if hasattr(response_obj, 'get_json'):
                            error_data = response_obj.get_json()
                            if error_data and 'error' in error_data:
                                error_msg = error_data['error'].get('message', 'Unknown error')
                                if 'details' in error_data['error']:
                                    details = error_data['error']['details']
                                    error_msg += f" (URL: {details.get('url', 'N/A')}, Model: {details.get('model', 'N/A')})"
                                error_info = f"HTTP 500: {error_msg}"
                                response_data = error_data
                            else:
                                error_info = "HTTP 500: Unknown error - no error data"
                                response_data = None
                        else:
                            error_info = "HTTP 500: Unknown error - cannot extract JSON"
                            response_data = None
                    
                    response = response_obj
                    if self.verbose:
                        self._log(f"Captured response_data: {bool(response_data)}, type: {type(response_data)}")
                else:
                    response = response_tuple
                    response_data = None
            else:
                response, response_data = self._handle_static(route_result, context["stream"])
            
            # Record stats before returning
            latency_ms = (time.time() - start_time) * 1000
            content = route_result.content if hasattr(route_result, 'content') else None
            if error_info:
                content = error_info
            tried_routers = getattr(route_result, 'tried_routers', [])
            
            # Add fallback info to tried_routers if this was a proxy call
            if route_result.should_proxy and fallback_request:
                fallback_entry = {
                    'name': 'llm_fallback',
                    'request': fallback_request,
                    'response': response_data
                }
                if self.verbose:
                    self._log(f"Adding fallback to tried_routers: request={bool(fallback_request)}, response={bool(response_data)}")
                tried_routers.append(fallback_entry)
            
            self.stats.record(message, route_result.name, latency_ms, content, request_data=data, response_data=response_data, tried_routers=tried_routers, route_result=route_result)
            
            return response
        except Exception as e:
            if self.verbose:
                self._log(f"ERROR: {str(e)}")
            raise
    
    def delete_log(self, log_id: int):
        """Delete a specific log entry."""
        if self.stats.delete_log(log_id):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Log not found"}), 404
    
    def _handle_static(self, route_result, stream: bool):
        """Handle static route response."""
        if stream:
            return Response(
                ResponseGenerator.generate_stream(route_result),
                mimetype="text/event-stream"
            ), None
        else:
            response = ResponseGenerator.generate_response(route_result, stream)
            if self.verbose:
                self._log(f"RESPONSE: {json.dumps(response, indent=2)}")
            resp = jsonify(response)
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            return resp, response
    
    def _handle_proxy(self, data: dict, stream: bool, route_name: str):
        """Handle proxy to LLM."""
        if self.verbose:
            self._log(f"📡 Forwarding to LLM (route: {route_name})")
        
        result = self.llm_proxy.forward(data["messages"], stream)
        
        # Extract request_data if available
        request_data = None
        if isinstance(result, tuple) and len(result) == 2:
            result, request_data = result
        
        # Check for error response
        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500, request_data, None
        
        if stream:
            # Capture streaming response by wrapping the generator
            captured_response = {'chunks': [], 'combined_content': ''}
            
            def proxy_stream():
                for chunk in result:
                    # Store chunk for later inspection
                    captured_response['chunks'].append(chunk)
                    
                    # Parse SSE chunk to extract content
                    try:
                        if chunk.startswith('data: ') and chunk != 'data: [DONE]\n\n':
                            json_str = chunk[6:].strip()
                            if json_str:
                                chunk_data = json.loads(json_str)
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        captured_response['combined_content'] += content
                    except:
                        pass  # Skip malformed chunks
                    
                    if self.verbose >= 4:
                        self._log(f"📤 Chunk: {chunk[:100]}")
                    yield chunk
            
            return Response(proxy_stream(), mimetype="text/event-stream"), None, request_data, captured_response
        else:
            if self.verbose >= 2:
                self._log(f"LLM RESPONSE: {json.dumps(result, indent=2)[:500]}")
            resp = jsonify(result)
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            return resp, None, request_data, result
    
    def _log(self, message: str):
        """Log message to stderr."""
        print(f"\n{'='*60}", file=sys.stderr)
        print(message, file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
    
    def run(self):
        """Run the Flask application."""
        # Use threaded mode and explicitly set charset
        self.app.run(port=self.config.port, threaded=True)


def create_app(verbose: int = 0) -> ClawLayerApp:
    """Factory function to create ClawLayer application."""
    config = Config.from_yaml()
    
    if verbose:
        print(f"Embedding provider: {config.embedding_provider} ({config.get_embedding_url()})", file=sys.stderr)
        print(f"Text provider: {config.text_provider} ({config.get_text_url()})", file=sys.stderr)
    
    # Build router chain from config using factory
    factory = RouterFactory(config, verbose)
    routers = factory.build_router_chain()
    router_chain = RouterChain(routers)
    
    # Use text provider for LLM proxy
    llm_proxy = LLMProxy(config.get_text_url(), config.get_text_model())
    
    return ClawLayerApp(config, router_chain, llm_proxy, verbose)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ClawLayer - Intelligent routing for OpenClaw agents")
    parser.add_argument("-v", "--verbose", action="count", default=0, 
                       help="Increase verbosity (-v, -vv, -vvvv)")
    args = parser.parse_args()
    
    app = create_app(verbose=args.verbose)
    app.run()


if __name__ == "__main__":
    main()
