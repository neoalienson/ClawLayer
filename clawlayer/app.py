"""Flask application for ClawLayer."""

from flask import Flask, request, jsonify, Response
import argparse
import sys
import json

from clawlayer.config import Config
from clawlayer.router import (
    RouterChain, EchoRouter, CommandRouter, 
    GreetingRouter, SummarizeRouter, SemanticRouterAdapter
)
from clawlayer.handler import MessageHandler, ResponseGenerator
from clawlayer.proxy import LLMProxy


class ClawLayerApp:
    """Main application class."""
    
    def __init__(self, config: Config, router_chain: RouterChain, llm_proxy: LLMProxy, verbose: int = 0):
        self.config = config
        self.router_chain = router_chain
        self.llm_proxy = llm_proxy
        self.verbose = verbose
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        self.app.route("/v1/models", methods=["GET"])(self.models)
        self.app.route("/v1/chat/completions", methods=["POST"])(self.chat_completions)
    
    def models(self):
        """Return available models."""
        return jsonify({"models": ["clawlayer"]})
    
    def chat_completions(self):
        """Handle chat completion requests."""
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
        
        # Handle response
        if route_result.should_proxy:
            return self._handle_proxy(data, context["stream"], route_result.name)
        else:
            return self._handle_static(route_result, context["stream"])
    
    def _handle_static(self, route_result, stream: bool):
        """Handle static route response."""
        if stream:
            return Response(
                ResponseGenerator.generate_stream(route_result),
                mimetype="text/event-stream"
            )
        else:
            response = ResponseGenerator.generate_response(route_result, stream)
            if self.verbose:
                self._log(f"💬 RESPONSE: {json.dumps(response, indent=2)}")
            return jsonify(response)
    
    def _handle_proxy(self, data: dict, stream: bool, route_name: str):
        """Handle proxy to LLM."""
        if self.verbose:
            self._log(f"📡 Forwarding to LLM (route: {route_name})")
        
        result = self.llm_proxy.forward(data["messages"], stream)
        
        if stream:
            def proxy_stream():
                for chunk in result:
                    if self.verbose >= 4:
                        self._log(f"📤 Chunk: {chunk[:100]}")
                    yield chunk
            return Response(proxy_stream(), mimetype="text/event-stream")
        else:
            if self.verbose >= 2:
                self._log(f"🔍 LLM RESPONSE: {json.dumps(result, indent=2)[:500]}")
            return jsonify(result)
    
    def _log(self, message: str):
        """Log message to stderr."""
        print(f"\n{'='*60}", file=sys.stderr)
        print(message, file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
    
    def run(self):
        """Run the Flask application."""
        self.app.run(port=self.config.port)


def create_app(verbose: int = 0) -> ClawLayerApp:
    """Factory function to create ClawLayer application."""
    config = Config.from_env()
    
    # Create routers in priority order
    routers = [
        EchoRouter(),
        CommandRouter(),
        GreetingRouter(),
        SummarizeRouter()
    ]
    
    # Add semantic router if available
    try:
        from semantic_router import Route, SemanticRouter
        from semantic_router.encoders import OllamaEncoder
        
        encoder = OllamaEncoder(name=config.embed_model)
        
        greeting_route = Route(
            name="greeting",
            utterances=["hello", "hi", "hey", "good morning", "good afternoon"]
        )
        
        summarize_route = Route(
            name="summarize",
            utterances=["summarize the conversation", "create a summary", 
                       "checkpoint summary", "structured context checkpoint"]
        )
        
        semantic_router = SemanticRouter(
            encoder=encoder, 
            routes=[greeting_route, summarize_route],
            auto_sync="local"
        )
        
        routers.append(SemanticRouterAdapter(semantic_router))
    except ImportError:
        pass
    
    router_chain = RouterChain(routers)
    llm_proxy = LLMProxy(config.ollama_url, config.ollama_model)
    
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
