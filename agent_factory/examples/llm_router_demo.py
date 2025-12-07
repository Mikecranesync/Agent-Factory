"""
LLM Router Demo - Phase 1 Validation

Demonstrates the new LLM abstraction layer with cost tracking.

Tests:
1. Basic completion with cost tracking
2. Multiple provider support
3. Usage tracker aggregation
4. Model info lookup

Run: poetry run python agent_factory/examples/llm_router_demo.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from agent_factory.llm import (
    LLMRouter,
    LLMConfig,
    LLMProvider,
    UsageTracker,
    get_model_info,
    MODEL_REGISTRY
)

# Load environment variables
load_dotenv()


def demo_basic_completion():
    """Test 1: Basic completion with cost tracking"""
    print("\n" + "="*60)
    print("TEST 1: Basic Completion with Cost Tracking")
    print("="*60)

    router = LLMRouter()

    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=100
    )

    messages = [
        {"role": "user", "content": "Say 'Hello from Agent Factory!' and nothing else."}
    ]

    try:
        response = router.complete(messages, config)

        print(f"\n[SUCCESS] Completion received")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Content: {response.content[:100]}...")
        print(f"\nUsage Statistics:")
        print(f"  Input tokens:  {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")
        print(f"  Total tokens:  {response.usage.total_tokens}")
        print(f"\nCost Breakdown:")
        print(f"  Input cost:  ${response.usage.input_cost_usd:.6f}")
        print(f"  Output cost: ${response.usage.output_cost_usd:.6f}")
        print(f"  Total cost:  ${response.usage.total_cost_usd:.6f}")
        print(f"\nPerformance:")
        print(f"  Latency: {response.latency_ms:.2f}ms")

        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        return False


def demo_usage_tracker():
    """Test 2: Usage tracker with multiple calls"""
    print("\n" + "="*60)
    print("TEST 2: Usage Tracker - Multiple Calls")
    print("="*60)

    router = LLMRouter()
    tracker = UsageTracker(budget_limit_usd=1.0)

    # Make several calls with different models
    test_configs = [
        LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini"),
        LLMConfig(provider=LLMProvider.OPENAI, model="gpt-3.5-turbo"),
    ]

    messages = [{"role": "user", "content": "Count to 3."}]

    for i, config in enumerate(test_configs, 1):
        try:
            print(f"\nCall {i}: {config.model}...", end=" ")
            response = router.complete(messages, config)
            tracker.track(response, tags=[f"demo", f"call_{i}"])
            print(f"[OK] ${response.usage.total_cost_usd:.6f}")
        except Exception as e:
            print(f"[FAILED] {str(e)}")

    # Get aggregated stats
    print("\n" + "-"*60)
    print("AGGREGATED STATISTICS")
    print("-"*60)

    stats = tracker.get_stats()
    print(f"Total calls:        {stats['total_calls']}")
    print(f"Total cost:         ${stats['total_cost_usd']:.6f}")
    print(f"Total tokens:       {stats['total_tokens']:,}")
    print(f"Avg latency:        {stats['avg_latency_ms']:.2f}ms")
    print(f"Avg cost per call:  ${stats['avg_cost_per_call']:.6f}")

    print(f"\nCost by provider:")
    for provider, cost in stats['providers'].items():
        print(f"  {provider}: ${cost:.6f}")

    print(f"\nCost by model:")
    for model, cost in stats['models'].items():
        print(f"  {model}: ${cost:.6f}")

    # Budget status
    budget = tracker.get_budget_status()
    print(f"\nBudget Status:")
    print(f"  Limit:     ${budget['limit_usd']:.2f}")
    print(f"  Used:      ${budget['used_usd']:.6f}")
    print(f"  Remaining: ${budget['remaining_usd']:.6f}")
    print(f"  Usage:     {budget['percentage_used']:.2f}%")


def demo_model_registry():
    """Test 3: Model registry and pricing lookup"""
    print("\n" + "="*60)
    print("TEST 3: Model Registry and Pricing")
    print("="*60)

    print(f"\nTotal models in registry: {len(MODEL_REGISTRY)}")

    # Show a few models
    sample_models = ["gpt-4o-mini", "claude-3-haiku-20240307", "llama3"]

    print("\nSample Model Information:")
    for model_name in sample_models:
        info = get_model_info(model_name)
        if info:
            print(f"\n{model_name}:")
            print(f"  Provider:      {info.provider}")
            print(f"  Input cost:    ${info.input_cost_per_1k:.6f}/1K tokens")
            print(f"  Output cost:   ${info.output_cost_per_1k:.6f}/1K tokens")
            print(f"  Context:       {info.context_window:,} tokens")
            print(f"  Capability:    {info.capability}")
            print(f"  Streaming:     {info.supports_streaming}")


def main():
    """Run all demo tests"""
    print("\n" + "="*60)
    print("LLM ROUTER DEMO - Phase 1 Validation")
    print("="*60)

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[ERROR] OPENAI_API_KEY not found in environment")
        print("Please set your API key in .env file")
        return

    print("\n[INFO] Running Phase 1 validation tests...")

    # Test 1: Basic completion
    success_1 = demo_basic_completion()

    if success_1:
        # Test 2: Usage tracker
        demo_usage_tracker()

    # Test 3: Model registry (no API calls)
    demo_model_registry()

    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nPhase 1 Status: LLM Abstraction Layer operational")
    print("Next: Integrate with AgentFactory, write comprehensive tests")


if __name__ == "__main__":
    main()
