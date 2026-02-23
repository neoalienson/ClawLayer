# ClawLayer Configuration Guide

ClawLayer is **100% YAML-driven** - no code changes needed for most customizations.

## Basic Configuration

### Step 1: Define Providers

```yaml
providers:
  local:
    url: http://localhost:11434
    type: ollama
    provider_type: embedding  # Fast, cheap
    models:
      embed: nomic-embed-text
  
  remote:
    url: http://192.168.1.100:11434/v1/chat/completions
    type: openai
    provider_type: llm  # Accurate, expensive
    models:
      text: llama3.2
```

### Step 2: Configure Routes

```yaml
routers:
  semantic:
    greeting:
      enabled: true
      stages:
        - provider: local      # Try cheap embedding first
          model: nomic-embed-text
          threshold: 0.75
        - provider: remote     # Fallback to LLM if needed
          model: llama3.2
          threshold: 0.6
      utterances:
        - "hello"
        - "hi"
```

**That's it!** ClawLayer will:
1. Try local embedding (fast/cheap) with 0.75 threshold
2. If confidence < 0.75, try remote LLM (accurate/expensive)
3. If no match, forward to full LLM inference

## Environment Variables

```bash
export EMBEDDING_PROVIDER=local
export TEXT_PROVIDER=remote
export VISION_PROVIDER=openai
export CLAWLAYER_CONFIG=/path/to/config.yml
```

## Customization Examples

### Example 1: Add a New Route (No Code!)

```yaml
routers:
  semantic:
    farewell:  # New route!
      enabled: true
      stages:
        - provider: local
          model: nomic-embed-text
          threshold: 0.7
      utterances:
        - "goodbye"
        - "bye"
        - "see you"
```

### Example 2: Adjust Thresholds for Cost/Accuracy Tradeoff

```yaml
# More aggressive (cheaper, less accurate)
stages:
  - provider: local
    threshold: 0.6  # Lower threshold = more matches at stage 1

# More conservative (expensive, more accurate)  
stages:
  - provider: local
    threshold: 0.9  # Higher threshold = more cascade to stage 2
```

### Example 3: Multi-Cloud Setup

```yaml
providers:
  local_ollama:
    provider_type: embedding
    url: http://localhost:11434
  
  aws_bedrock:
    provider_type: llm
    url: https://bedrock.us-east-1.amazonaws.com
  
  openai:
    provider_type: llm
    url: https://api.openai.com/v1/chat/completions

routers:
  semantic:
    greeting:
      stages:
        - provider: local_ollama   # Free local
          threshold: 0.8
        - provider: aws_bedrock    # Mid-tier cloud
          threshold: 0.7
        - provider: openai         # Premium fallback
          threshold: 0.6
```

### Example 4: Add Custom Router (Minimal Code)

```python
# custom_router.py
from clawlayer.routers import Router, RouteResult

class CustomRouter(Router):
    def route(self, message: str, context: dict):
        if "custom_pattern" in message:
            return RouteResult(name="custom", content="Custom response")
        return None
```

Then register in config:
```yaml
routers:
  fast:
    priority:
      - custom  # Add your router
      - echo
      - command
```

## Router Behavior Customization

### Change Router Priority

```yaml
routers:
  fast:
    priority:
      - command  # Check commands first
      - echo
  
  semantic:
    priority:
      - farewell  # Check farewells before greetings
      - greeting
```

### Disable Routes

```yaml
routers:
  semantic:
    greeting:
      enabled: false  # Disable greeting router
```

### Change Command Prefix

```yaml
routers:
  fast:
    command:
      prefix: "exec:"  # Use 'exec:' instead of 'run:'
```

## Multi-Stage Cascade Configuration

Semantic routers support **multi-stage cascading** to optimize cost and accuracy. Each stage tries a different provider with its own confidence threshold:

```yaml
# Define providers with their types
providers:
  local:
    url: http://localhost:11434
    type: ollama
    provider_type: embedding  # This is an embedding provider
    models:
      embed: nomic-embed-text
  
  remote:
    url: http://192.168.1.100:11434/v1/chat/completions
    type: openai
    provider_type: llm  # This is an LLM provider
    models:
      text: llama3.2

# Use providers in cascade stages
routers:
  semantic:
    greeting:
      enabled: true
      stages:
        - provider: local           # Stage 1: Uses embedding (from provider_type)
          model: nomic-embed-text
          threshold: 0.75
        - provider: remote          # Stage 2: Uses LLM (from provider_type)
          model: llama3.2
          threshold: 0.6
      utterances:
        - "hello"
        - "hi"
        - "hey"
```

### How It Works

1. **Stage 1** (fast/cheap embedding): Local embedding model with high threshold
   - If similarity ≥ 0.75 → Match! Return response immediately
   - If similarity < 0.75 → Continue to Stage 2

2. **Stage 2** (accurate/expensive LLM): LLM-based classification
   - LLM evaluates if message matches the route based on example utterances
   - If confidence ≥ 0.6 → Match! Return response
   - If confidence < 0.6 → No match, cascade to LLM fallback

### Example Scenarios

```
"hello" → Stage 1: similarity 0.92 ≥ 0.75 ✓ → Return (fast/cheap)
"hey what's up" → Stage 1: 0.68 < 0.75 → Stage 2: 0.71 ≥ 0.6 ✓ → Return (accurate/expensive)
"weather today" → Stage 1: 0.3 < 0.75 → Stage 2: 0.4 < 0.6 → LLM fallback (full inference)
```

### Benefits

- **Cost optimization**: 80% of queries match at Stage 1 (cheap local embeddings)
- **Accuracy**: 15% cascade to Stage 2 (LLM for complex/ambiguous cases)
- **Flexibility**: Only 5% reach expensive LLM fallback for full conversation

### Stage Types

- `provider_type: embedding` - Provider uses embedding model for vector similarity (fast, cheap)
- `provider_type: llm` - Provider uses LLM to classify if message matches route (accurate, expensive)

The stage type is determined by the provider's `provider_type` field, not specified in the router configuration.

### Confidence Scores

Confidence scores are cosine similarity values (0.0 to 1.0) calculated by the `semantic-router` library:
- 1.0 = identical vectors
- 0.8-1.0 = very similar
- 0.6-0.8 = somewhat similar  
- <0.6 = not similar

See [CASCADE.md](CASCADE.md) for advanced patterns.

## Custom Router Implementation

For advanced use cases, implement the Router interface:

```python
from clawlayer.routers import Router, RouteResult

class CustomRouter(Router):
    def route(self, message: str, context: dict):
        if "custom_pattern" in message:
            return RouteResult(name="custom", content="Custom response")
        return None
```

Register in `router_factory.py` or configure via YAML (see Example 4 above).

## Provider Configuration

### Provider Types

- **embedding**: Fast, cheap vector similarity matching
- **llm**: Accurate, expensive LLM-based classification

### Provider Fields

```yaml
providers:
  provider_name:
    url: http://localhost:11434              # API endpoint
    type: ollama                              # ollama or openai
    provider_type: embedding                  # embedding or llm
    models:
      embed: nomic-embed-text                 # Embedding model
      text: llama3.2                          # Text generation model
      vision: llava:latest                    # Vision model (optional)
    capabilities:                             # Optional capabilities
      max_context: 8192
      tool_use: true
```

## Router Configuration

### Fast Routers

Fast routers use pattern matching (regex/logic) for instant responses:

```yaml
routers:
  fast:
    priority:
      - echo      # Check echo first
      - command   # Then commands
      - quick     # Then quick patterns
    
    echo:
      enabled: true
    
    command:
      enabled: true
      prefix: "run:"
    
    quick:
      enabled: true
      patterns:
        - pattern: "^(hi|hello)$"
          response: "Hi"
```

### Semantic Routers

Semantic routers use embedding/LLM for similarity matching:

```yaml
routers:
  semantic:
    priority:
      - greeting
      - summarize
    
    greeting:
      enabled: true
      provider: local  # Single provider (simple)
      utterances:
        - "hello"
        - "hi"
    
    # Or use multi-stage cascade
    greeting:
      enabled: true
      stages:  # Multi-stage cascade (advanced)
        - provider: local
          model: nomic-embed-text
          threshold: 0.75
        - provider: remote
          model: llama3.2
          threshold: 0.6
      utterances:
        - "hello"
        - "hi"
```

## Related Documentation

- [README.md](../README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [CASCADE.md](CASCADE.md) - Advanced cascade patterns
- [QUICK_ROUTER.md](QUICK_ROUTER.md) - Quick router guide
