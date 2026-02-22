# File Structure

ClawLayer follows a modular architecture with clear separation between backend, web UI, and configuration.

## Project Layout

```
clawlayer/
├── clawlayer/                   # Python backend package
│   ├── __init__.py              # Package exports
│   ├── app.py                   # Flask application & dependency injection
│   ├── config.py                # Configuration management
│   ├── handler.py               # Message handling & response generation
│   ├── proxy.py                 # LLM proxy for forwarding requests
│   ├── router_factory.py        # Factory for building routers from YAML config
│   ├── stats.py                 # Statistics collection
│   ├── web_api.py               # Web API endpoints
│   └── routers/                 # Router implementations
│       ├── __init__.py          # Base classes (Router, RouteResult) + exports
│       ├── semantic_base_router.py  # Base class for multi-stage semantic routers
│       ├── echo_router.py       # EchoRouter - tool result detection
│       ├── command_router.py    # CommandRouter - command prefix detection
│       ├── greeting_router.py   # GreetingRouter - semantic greeting matching
│       ├── summarize_router.py  # SummarizeRouter - semantic summary matching
│       └── router_chain.py      # RouterChain - router management
├── webui/                       # Node.js Web UI
│   ├── src/
│   │   ├── main.ts              # Main app component
│   │   ├── api/
│   │   │   └── clawlayer-client.ts  # API client
│   │   └── components/
│   │       ├── dashboard.ts     # Dashboard view
│   │       ├── config-editor.ts # Config editor
│   │       └── log-viewer.ts    # Log viewer
│   ├── index.html               # HTML entry point
│   ├── package.json             # Node.js dependencies
│   └── vite.config.ts           # Vite configuration
├── tests/                       # Python test suite
│   ├── test_clawlayer.py        # Core functionality tests
│   └── test_cascade_edge_cases.py  # Multi-stage cascade and edge case tests
├── docs/                        # Documentation
│   ├── TESTING.md               # Testing guide
│   ├── FILE_STRUCTURE.md        # This file
│   └── CASCADE.md               # Advanced cascade patterns
├── config.yml                   # Main configuration
├── config.example.yml           # Example configuration
├── run.py                       # Entry point
├── start-dev.sh                 # Development startup script
└── stop-dev.sh                  # Development shutdown script
```

## Core Components

### Backend (`clawlayer/`)

- **app.py**: Flask application setup, dependency injection, and service initialization
- **config.py**: YAML configuration parsing, environment variable handling, validation
- **handler.py**: Request processing, router orchestration, response formatting
- **proxy.py**: LLM proxy for forwarding unmatched requests to upstream providers
- **router_factory.py**: Dynamic router creation from YAML configuration
- **stats.py**: Request statistics, performance metrics, monitoring data
- **web_api.py**: OpenAI-compatible API endpoints, streaming support

### Routers (`clawlayer/routers/`)

- **Base classes**: `Router` interface, `RouteResult` data class, `SemanticBaseRouter`
- **Fast routers**: `EchoRouter` (tool detection), `CommandRouter` (regex matching)
- **Semantic routers**: `GreetingRouter`, `SummarizeRouter` (embedding-based matching)
- **Router chain**: `RouterChain` manages router priority and execution flow

### Web UI (`webui/`)

- **TypeScript/Vite**: Modern frontend build system with hot reload
- **Components**: Modular UI components for dashboard, config editing, log viewing
- **API client**: Type-safe backend integration with error handling
- **Real-time updates**: WebSocket/SSE integration for live statistics and logs

### Configuration

- **config.yml**: Main configuration file (YAML format)
- **Environment variables**: Provider URLs, API keys, feature flags
- **Runtime configuration**: Dynamic config reloading via web UI

### Testing

- **Python tests**: Unit tests for all core components using unittest
- **Node.js tests**: Component and integration tests using modern testing framework
- **Test isolation**: Separate test configurations and mock providers