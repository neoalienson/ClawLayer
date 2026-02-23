# ClawLayer

A **lightweight, intelligent proxy and routing layer** for **OpenClaw** AI agents - delivering instant responses, cost savings, and deep observability into agent-LLM communication for security, development, and troubleshooting.

## Purpose

ClawLayer provides a **simple YAML-driven configuration** to route OpenClaw agent requests intelligently:

- **Instant responses** for greetings and routine queries via semantic matching
- **Zero-latency tool calls** for command execution patterns via quick router (regex)
- **Multi-stage cascade** from fast/cheap to accurate/expensive models
- **Transparent fallback** to full LLM inference when needed
- **Real-time monitoring** with web UI to inspect prompts, context, and responses

**Key Benefits:**
- ⚡ **Quick Response**: Zero-latency routing for commands, ~100ms for semantic matching vs 2-5s LLM inference
- 💰 **Cost Savings**: Route 80% of requests through cheap models, 15% through mid-tier, 5% to expensive LLM
- 🔍 **Deep Observability**: Inspect full agent-LLM communication (prompts, context, responses) via web UI
- 🛡️ **Security Guardrails**: Monitor and analyze all requests/responses for security compliance
- 🐛 **Development & Troubleshooting**: Understand OpenClaw's behavior, debug issues, optimize workflows
- 🎯 **Easy Configuration**: Everything in YAML with web-based config editor - no code changes needed
- 🔧 **Highly Customizable**: Mix embedding and LLM stages, adjust thresholds, add custom routers

See [Architecture](docs/ARCHITECTURE.md) for detailed system design and performance analysis.

## Features

### Core Capabilities
- **Multi-Stage Cascade Routing**: Cost-optimized semantic matching with confidence-based fallback
- **YAML-Driven Configuration**: No code changes - configure everything via config.yml
- **Flexible Provider System**: Mix local/remote, embedding/LLM, Ollama/OpenAI providers
- **Semantic Routing**: Embedding-based matching for greetings, summaries, and custom patterns
- **Fast Regex Routing**: Pattern matching for commands and tool execution
- **Streaming Support**: Full SSE streaming for both static and proxied responses

### Why ClawLayer?
- **Lightweight**: ~500 lines of core code, minimal dependencies
- **Easy to Configure**: Add new routes by editing YAML, no Python required
- **Highly Customizable**: 
  - Adjust confidence thresholds per stage
  - Mix embedding and LLM providers in cascade
  - Add custom routers with simple Python interface
  - Configure router priority and enable/disable per route
- **Understand OpenClaw**: Web UI provides real-time visibility into how OpenClaw agents work
  - See which routers handle which requests
  - Inspect full request/response data
  - Monitor routing performance and latency
  - Perfect for learning, debugging, and optimizing OpenClaw workflows

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure

**Quick Router Only (Fastest - Zero API Costs)**
```bash
cp config.quickrouter.yml config.yml
```

Minimal config for instant responses:
```yaml
# Quick router only - zero-latency pattern matching
routers:
  fast:
    priority:
      - quick
    quick:
      enabled: true
      patterns:
        - pattern: Greet the user
          response: Hi
        - pattern: <conversation>.*</conversation>.*summarize
          response: '## Goal\n\n  No user goal provided...'
  semantic:
    priority: []
```


### 3. Run

**CLI Only:**
```bash
python run.py -v
```

**With Web UI:**
```bash
# Install web UI dependencies (first time only)
cd webui && npm install && cd ..

# Start both backend and web UI
./start-dev.sh

# Or start separately:
# Terminal 1: python run.py -v
# Terminal 2: cd webui && npm run dev
```

**Access:**
- Backend API: http://localhost:11435
- Web UI: http://localhost:3000

**Stop services:**
```bash
./stop-dev.sh
```

That's it! ClawLayer is now routing requests intelligently. See [Configuration Guide](docs/CONFIGURATION.md) for detailed setup and [Web UI Guide](docs/WEBUI.md) for monitoring features.

## Usage

```bash
# Development mode (Flask dev server)
python run.py -v

# Production mode (Gunicorn WSGI server - recommended)
./start-prod.sh

# Run with full request logging
python run.py -vv

# Run with streaming chunk logging
python run.py -vvvv

# Run tests
python -m unittest tests.test_clawlayer -v
```

### Production vs Development

**Development mode** (`python run.py`):
- Uses Flask's built-in development server (werkzeug)
- Good for testing and debugging
- ⚠️ Has unicode encoding limitations with emojis in responses
- Not suitable for production

**Production mode** (`./start-prod.sh`):
- Uses Gunicorn WSGI server
- Handles unicode/emoji characters properly
- Better performance and stability
- Recommended for production use

## API

OpenAI-compatible endpoints:
- `GET /v1/models`
- `POST /v1/chat/completions`

Supports both streaming and non-streaming modes.

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design, router priority, and performance analysis
- **[Configuration Guide](docs/CONFIGURATION.md)** - Detailed configuration and customization examples
- **[Web UI Guide](docs/WEBUI.md)** - Web interface for monitoring and observability
- **[Quick Router](docs/QUICK_ROUTER.md)** - Zero-latency pattern-based routing for instant responses
- **[Cascade Patterns](docs/CASCADE.md)** - Advanced multi-stage routing configurations
- **[Testing Guide](docs/TESTING.md)** - Python and Node.js test coverage, running tests
- **[File Structure](docs/FILE_STRUCTURE.md)** - Project layout and component organization

## Related Projects

- **[ClawRouter](https://github.com/BlockRunAI/ClawRouter)** - Advanced routing with load balancing, fallback chains, and cost optimization for production deployments
