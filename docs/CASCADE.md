# Multi-Stage Semantic Routing with Conditional Cascading

ClawLayer supports multi-stage semantic routing where requests cascade through multiple embedding models based on confidence thresholds.

## How It Works

1. **Stage 1**: Fast/cheap embedding model with high confidence threshold
2. **Stage 2+**: More accurate models if confidence is too low
3. **Fallback**: LLM if no semantic match

## Configuration

```yaml
semantic:
  greeting:
    enabled: true
    stages:
      - provider: local          # Stage 1: Fast local model
        model: nomic-embed-text
        threshold: 0.75          # High confidence required
      - provider: remote         # Stage 2: Cascade if confidence < 0.75
        model: nomic-embed-text
        threshold: 0.6           # Lower threshold acceptable
    utterances:
      - "hello"
      - "hi"
      - "hey"
```

## Benefits

- **Cost Optimization**: Use cheap local embeddings for clear matches
- **Accuracy**: Cascade to better models for ambiguous cases
- **Latency Control**: Fast path for high-confidence matches
- **Flexibility**: Configure per-router cascade strategies

## Example Scenarios

### Scenario 1: Clear Match (Stage 1 Only)
```
User: "hello"
→ Stage 1 (local): confidence 0.92 ≥ 0.75 ✓
→ Response: "Hi (quick response)"
```

### Scenario 2: Ambiguous Match (Cascade to Stage 2)
```
User: "hey what's up"
→ Stage 1 (local): confidence 0.68 < 0.75 ✗
→ Stage 2 (remote): confidence 0.71 ≥ 0.6 ✓
→ Response: "Hi (quick response from stage 2)"
```

### Scenario 3: No Match (Fallback to LLM)
```
User: "what's the weather"
→ Stage 1 (local): no match ✗
→ Stage 2 (remote): no match ✗
→ Fallback: Forward to LLM
```

## Advanced Patterns

### Different Models Per Stage
```yaml
stages:
  - provider: local
    model: nomic-embed-text      # Fast, small model
    threshold: 0.8
  - provider: openai
    model: text-embedding-3-large # Accurate, larger model
    threshold: 0.6
```

### Cost-Aware Cascading
```yaml
stages:
  - provider: free_tier          # Free tier first
    model: basic-embed
    threshold: 0.85              # High bar for free tier
  - provider: paid_tier          # Paid tier for edge cases
    model: premium-embed
    threshold: 0.65
```

### Latency-Optimized
```yaml
stages:
  - provider: local              # Local first (0ms network)
    model: fast-embed
    threshold: 0.7
  - provider: edge_cdn           # Edge CDN second (low latency)
    model: standard-embed
    threshold: 0.6
```

## Implementation Details

- Each stage creates a separate `SemanticRouter` instance
- Stages are tried sequentially until threshold is met
- Confidence scores come from semantic-router library
- Router cache prevents duplicate initialization
- Verbose mode shows which stage matched

## Testing

Run the cascade example:
```bash
python examples/cascade_example.py
```

Run tests:
```bash
python -m unittest tests.test_clawlayer -v
```
