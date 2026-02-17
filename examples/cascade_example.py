"""Example demonstrating multi-stage semantic routing with conditional cascading.

This example shows how ClawLayer can use multiple embedding models in cascade:
1. Try fast/cheap local model first with high confidence threshold
2. If confidence is low, cascade to more accurate remote model
"""

from clawlayer.config import Config
from clawlayer.router_factory import RouterFactory

def main():
    # Load config with cascade stages
    config = Config.from_yaml()
    
    print("=== ClawLayer Multi-Stage Cascade Example ===\n")
    print("Configuration:")
    print(f"  Embedding Provider: {config.embedding_provider}")
    print(f"  Text Provider: {config.text_provider}\n")
    
    # Build router chain with cascade support
    factory = RouterFactory(config, verbose=1)
    routers = factory.build_router_chain()
    
    print(f"\nBuilt {len(routers)} routers with cascade support\n")
    
    # Example messages to test cascade behavior
    test_messages = [
        ("hello", "Clear greeting - should match stage 1"),
        ("hi there", "Clear greeting - should match stage 1"),
        ("hey what's up", "Casual greeting - may need stage 2"),
        ("greetings friend", "Formal greeting - should match stage 1"),
        ("summarize", "Clear summary request - should match stage 1"),
        ("give me a summary", "Summary request - may need stage 2"),
    ]
    
    print("Testing cascade behavior:")
    print("-" * 60)
    
    for message, description in test_messages:
        print(f"\nMessage: '{message}'")
        print(f"Description: {description}")
        
        # Try each router
        for router in routers:
            result = router.route(message, {})
            if result:
                print(f"✓ Matched by {router.__class__.__name__}: {result.name}")
                if hasattr(result, 'content') and result.content:
                    print(f"  Response: {result.content[:80]}...")
                break
        else:
            print("→ Would cascade to LLM fallback")

if __name__ == "__main__":
    main()
