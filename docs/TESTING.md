# Testing

ClawLayer includes comprehensive test coverage for both Python backend and Node.js web UI components.

## Python Backend Tests

All core components have unit tests covering routing logic, configuration, and API endpoints.

### Running Python Tests

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_clawlayer -v

# Run cascade and edge case tests
python -m unittest tests.test_cascade_edge_cases -v

# Run specific test class
python -m unittest tests.test_clawlayer.TestCommandRouter -v
```

### Test Coverage

- **Core routing logic**: Router chain, semantic matching, cascade behavior
- **Configuration management**: YAML parsing, provider setup, validation
- **API endpoints**: OpenAI-compatible chat completions, model listing
- **Edge cases**: Multi-stage cascade fallback, malformed requests, provider failures

## Node.js Web UI Tests

The web UI includes tests for components, API integration, and user interactions.

### Running Web UI Tests

```bash
# Install test dependencies (first time only)
cd webui && npm install

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Test Coverage

- **Component rendering**: Dashboard, config editor, log viewer
- **API client**: ClawLayer backend integration, error handling
- **User interactions**: Config editing, log filtering, real-time updates
- **State management**: Statistics updates, log streaming, configuration changes

## Integration Tests

End-to-end tests verify the complete request flow from web UI through backend to LLM providers.

```bash
# Start test environment
./start-test.sh

# Run integration tests
npm run test:integration
```

## Test Configuration

Test environments use isolated configurations to avoid affecting development settings:

- **Python**: `tests/test_config.yml` - Minimal test configuration
- **Node.js**: `webui/test.config.js` - Mock API responses and test data