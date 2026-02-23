# Quick Router

**Quick Router** refers to ClawLayer's fast, pattern-based routing system that provides **zero-latency responses** without any embedding or LLM inference.

## Overview

Quick routers use simple pattern matching (regex) and logic checks to instantly route requests, bypassing expensive model inference entirely. They are checked **first** in the routing pipeline before semantic routers.

## Performance

- **Latency**: <1ms (instant)
- **Cost**: $0 (no API calls)
- **Accuracy**: 100% for matching patterns

Compare this to:
- Semantic routing: ~100ms + API costs
- LLM inference: 2-5s + higher API costs

## Built-in Quick Routers

### 1. CommandRouter

**Purpose**: Detects command execution requests with "run:" prefix

**Pattern**: `^run:\s*(.+)$`

**Example**:
```
Input:  "run: ls -la"
Output: tool_call(function="exec", arguments={"command": "ls -la"})
Latency: <1ms
```

**Configuration**:
```yaml
routers:
  fast:
    command:
      enabled: true
      prefix: "run:"  # Customizable prefix
```

**Use case**: OpenClaw agents can execute commands instantly without LLM inference:
```
User: "run: pwd"
→ Quick Router detects pattern
→ Returns tool call immediately
→ Agent executes command
→ Total time: <10ms (vs 2-5s with LLM)
```

### 2. EchoRouter

**Purpose**: Detects tool execution results and echoes them back

**Pattern**: Checks for `role=tool` and `function=exec` in message context

**Example**:
```
Input:  {role: "tool", function: "exec", content: "/home/user"}
Output: {role: "assistant", content: "/home/user"}
Latency: <1ms
```

**Configuration**:
```yaml
routers:
  fast:
    echo:
      enabled: true
```

**Use case**: After command execution, echo results without LLM processing:
```
Agent executes: ls -la
→ Returns: [file listing]
→ EchoRouter detects tool result
→ Echoes output immediately
→ Total time: <1ms (vs 2-5s with LLM)
```

## Quick Router Pipeline

```mermaid
flowchart LR
    Request[Request] --> Quick{Quick Router?}
    Quick -->|Match| Response[Instant Response]
    Quick -->|No Match| Semantic[Semantic Router]
    Semantic -->|Match| Response2[~100ms Response]
    Semantic -->|No Match| LLM[LLM Inference]
    LLM --> Response3[2-5s Response]
    
    style Quick fill:#90EE90
    style Response fill:#90EE90
    style Semantic fill:#FFD700
    style Response2 fill:#FFD700
    style LLM fill:#FFB6C1
    style Response3 fill:#FFB6C1
```

## Custom Quick Routers

You can add custom quick routers for your specific patterns:

```python
from clawlayer.routers import Router, RouteResult
import re

class CustomQuickRouter(Router):
    def __init__(self):
        self.pattern = re.compile(r'^calc:\s*(.+)$')
    
    def route(self, message: str, context: dict):
        match = self.pattern.match(message)
        if match:
            expression = match.group(1)
            # Instant calculation without LLM
            try:
                result = eval(expression)  # Use safe eval in production
                return RouteResult(
                    name="calculator",
                    content=f"Result: {result}"
                )
            except:
                return None
        return None
```

Register in config:
```yaml
routers:
  fast:
    priority:
      - calculator  # Your custom quick router
      - command
      - echo
```

## Benefits

### 1. Cost Savings

**Without Quick Router**:
```
100 command requests/day × $0.001/request = $0.10/day = $36.50/year
```

**With Quick Router**:
```
100 command requests/day × $0/request = $0/day = $0/year
```

### 2. Speed Improvement

**Command execution flow comparison**:

| Step | Without Quick Router | With Quick Router |
|------|---------------------|-------------------|
| Parse request | 2-5s (LLM) | <1ms (regex) |
| Execute command | 10-100ms | 10-100ms |
| Process result | 2-5s (LLM) | <1ms (echo) |
| **Total** | **4-10s** | **10-100ms** |

**50-100x faster** for command execution!

### 3. Reliability

- No API rate limits
- No network latency
- No model availability issues
- 100% deterministic behavior

## Configuration Examples

### Example 1: Disable Quick Routers

```yaml
routers:
  fast:
    command:
      enabled: false  # All commands go to LLM
    echo:
      enabled: false  # All tool results go to LLM
```

### Example 2: Custom Command Prefix

```yaml
routers:
  fast:
    command:
      enabled: true
      prefix: "exec:"  # Use "exec: ls" instead of "run: ls"
```

### Example 3: Multiple Quick Routers

```yaml
routers:
  fast:
    priority:
      - calculator    # Check calculator first
      - command       # Then commands
      - echo          # Then tool results
    
    calculator:
      enabled: true
      prefix: "calc:"
    
    command:
      enabled: true
      prefix: "run:"
    
    echo:
      enabled: true
```

## Monitoring

Quick router hits are tracked in the web UI:

- **Dashboard**: Shows quick router hit rate vs semantic/LLM
- **Logs**: Each request shows which router handled it
- **Metrics**: Average latency for quick router requests

Example dashboard:
```
Quick Router:    75% (750/1000 requests, avg 0.5ms)
Semantic Router: 20% (200/1000 requests, avg 120ms)
LLM Fallback:     5% (50/1000 requests, avg 3.2s)
```

## Best Practices

1. **Use quick routers for deterministic patterns**: Commands, calculations, lookups
2. **Keep patterns simple**: Complex regex can slow down routing
3. **Validate input**: Quick routers bypass LLM safety checks
4. **Monitor hit rates**: Optimize patterns to maximize quick router usage
5. **Test thoroughly**: Quick routers are deterministic - test all edge cases

## Related Documentation

- [README.md](../README.md) - Main documentation
- [CASCADE.md](CASCADE.md) - Multi-stage semantic routing
- [TESTING.md](TESTING.md) - Testing quick routers
