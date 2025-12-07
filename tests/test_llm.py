"""
Tests for LLM Abstraction Layer (Phase 1)

Validates:
- Model registry and pricing
- Configuration validation
- Router functionality
- Cost tracking
- Usage statistics

Part of Phase 1: LLM Abstraction Layer
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.llm import (
    LLMProvider,
    ModelCapability,
    ModelInfo,
    UsageStats,
    LLMConfig,
    LLMResponse,
    get_model_info,
    validate_model_exists,
    get_models_by_provider,
    get_models_by_capability,
    get_cheapest_model,
    get_default_model,
    UsageTracker,
    MODEL_REGISTRY,
)


class TestModelRegistry:
    """Test model registry and pricing information"""

    def test_registry_not_empty(self):
        """Model registry should contain models"""
        assert len(MODEL_REGISTRY) > 0
        assert len(MODEL_REGISTRY) >= 10  # At least 10 models

    def test_get_model_info_valid(self):
        """Should retrieve model info for valid models"""
        info = get_model_info("gpt-4o-mini")
        assert info is not None
        assert info.provider == LLMProvider.OPENAI
        assert info.model_name == "gpt-4o-mini"
        assert info.input_cost_per_1k >= 0.0
        assert info.output_cost_per_1k >= 0.0
        assert info.context_window > 0

    def test_get_model_info_invalid(self):
        """Should return None for invalid models"""
        info = get_model_info("nonexistent-model")
        assert info is None

    def test_validate_model_exists(self):
        """Should validate model existence"""
        assert validate_model_exists("gpt-4o-mini") is True
        assert validate_model_exists("nonexistent-model") is False

    def test_get_models_by_provider(self):
        """Should filter models by provider"""
        openai_models = get_models_by_provider(LLMProvider.OPENAI)
        assert len(openai_models) > 0
        assert all(m.provider == LLMProvider.OPENAI for m in openai_models)

    def test_get_default_model(self):
        """Should return default model for each provider"""
        default = get_default_model(LLMProvider.OPENAI)
        assert default is not None
        assert validate_model_exists(default)

    def test_pricing_accuracy(self):
        """Model pricing should be reasonable"""
        info = get_model_info("gpt-4o-mini")
        # gpt-4o-mini should be cheap (< $0.001 per 1K tokens)
        assert info.input_cost_per_1k < 0.001
        assert info.output_cost_per_1k < 0.001

        # Opus should be expensive (> $0.01 per 1K tokens)
        opus = get_model_info("claude-3-opus-20240229")
        assert opus.input_cost_per_1k > 0.01


class TestModelCapabilities:
    """Test capability-based model selection"""

    def test_get_models_by_capability(self):
        """Should return models for each capability"""
        simple_models = get_models_by_capability(ModelCapability.SIMPLE)
        assert len(simple_models) > 0

        complex_models = get_models_by_capability(ModelCapability.COMPLEX)
        assert len(complex_models) > 0

    def test_cheapest_model_selection(self):
        """Should select cheapest model for capability"""
        cheapest = get_cheapest_model(ModelCapability.SIMPLE)
        assert cheapest is not None

        # Should be a local model (free) if available
        info = get_model_info(cheapest)
        # First in SIMPLE tier should be free (llama3 or mistral)
        assert info.input_cost_per_1k == 0.0

    def test_exclude_local_models(self):
        """Should exclude local models when requested"""
        cheapest = get_cheapest_model(
            ModelCapability.SIMPLE,
            exclude_local=True
        )

        if cheapest:  # May be None if only local models available
            info = get_model_info(cheapest)
            assert info.provider != LLMProvider.OLLAMA


class TestLLMConfig:
    """Test LLM configuration validation"""

    def test_valid_config(self):
        """Should create valid config"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            temperature=0.7
        )
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7

    def test_temperature_validation(self):
        """Should validate temperature range"""
        # Valid temperatures
        LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini", temperature=0.0)
        LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini", temperature=1.0)
        LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini", temperature=2.0)

        # Invalid temperatures should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini", temperature=-0.1)

        with pytest.raises(Exception):
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini", temperature=2.1)

    def test_default_values(self):
        """Should use default values"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini"
        )
        assert config.temperature == 0.7  # Default
        assert config.timeout == 120  # Default
        assert config.stream is False  # Default


class TestUsageStats:
    """Test usage statistics and cost calculation"""

    def test_usage_stats_creation(self):
        """Should create usage stats"""
        stats = UsageStats(
            input_tokens=100,
            output_tokens=50
        )
        assert stats.input_tokens == 100
        assert stats.output_tokens == 50

    def test_cost_calculation(self):
        """Should calculate costs correctly"""
        stats = UsageStats(input_tokens=1000, output_tokens=500)
        model_info = get_model_info("gpt-4o-mini")

        stats.calculate_costs(model_info)

        # Verify calculations
        expected_input_cost = 1.0 * model_info.input_cost_per_1k  # 1000/1000 * cost
        expected_output_cost = 0.5 * model_info.output_cost_per_1k  # 500/1000 * cost

        assert abs(stats.input_cost_usd - expected_input_cost) < 0.000001
        assert abs(stats.output_cost_usd - expected_output_cost) < 0.000001
        assert stats.total_tokens == 1500
        assert abs(stats.total_cost_usd - (expected_input_cost + expected_output_cost)) < 0.000001

    def test_zero_tokens(self):
        """Should handle zero tokens"""
        stats = UsageStats()
        model_info = get_model_info("gpt-4o-mini")

        stats.calculate_costs(model_info)

        assert stats.total_cost_usd == 0.0


class TestUsageTracker:
    """Test usage tracking and aggregation"""

    def test_tracker_initialization(self):
        """Should initialize tracker"""
        tracker = UsageTracker()
        assert len(tracker.calls) == 0

    def test_tracker_with_budget(self):
        """Should track budget limit"""
        tracker = UsageTracker(budget_limit_usd=10.0)
        assert tracker.budget_limit_usd == 10.0

    def test_track_single_call(self):
        """Should track a single response"""
        tracker = UsageTracker()

        # Create mock response
        usage = UsageStats(input_tokens=10, output_tokens=5)
        model_info = get_model_info("gpt-4o-mini")
        usage.calculate_costs(model_info)

        response = LLMResponse(
            content="Test response",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            usage=usage,
            latency_ms=1000.0
        )

        tracker.track(response)

        assert len(tracker.calls) == 1
        assert tracker.get_total_cost() > 0.0

    def test_track_multiple_calls(self):
        """Should track multiple responses"""
        tracker = UsageTracker()

        for i in range(3):
            usage = UsageStats(input_tokens=10, output_tokens=5)
            model_info = get_model_info("gpt-4o-mini")
            usage.calculate_costs(model_info)

            response = LLMResponse(
                content=f"Response {i}",
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                usage=usage,
                latency_ms=1000.0
            )

            tracker.track(response)

        assert len(tracker.calls) == 3

    def test_get_stats(self):
        """Should calculate aggregated statistics"""
        tracker = UsageTracker()

        # Track 2 calls
        for i in range(2):
            usage = UsageStats(input_tokens=100, output_tokens=50)
            model_info = get_model_info("gpt-4o-mini")
            usage.calculate_costs(model_info)

            response = LLMResponse(
                content=f"Response {i}",
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                usage=usage,
                latency_ms=1000.0
            )

            tracker.track(response)

        stats = tracker.get_stats()

        assert stats['total_calls'] == 2
        assert stats['total_tokens'] == 300  # (100+50) * 2
        assert stats['input_tokens'] == 200
        assert stats['output_tokens'] == 100
        assert stats['total_cost_usd'] > 0.0
        assert stats['avg_latency_ms'] == 1000.0

    def test_filter_by_provider(self):
        """Should filter stats by provider"""
        tracker = UsageTracker()

        # Track OpenAI call
        usage1 = UsageStats(input_tokens=10, output_tokens=5)
        model1 = get_model_info("gpt-4o-mini")
        usage1.calculate_costs(model1)

        response1 = LLMResponse(
            content="OpenAI response",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            usage=usage1,
            latency_ms=1000.0
        )

        tracker.track(response1)

        # Get OpenAI stats
        stats = tracker.get_stats(provider=LLMProvider.OPENAI)
        assert stats['total_calls'] == 1

        # Get Anthropic stats (should be empty)
        stats = tracker.get_stats(provider=LLMProvider.ANTHROPIC)
        assert stats['total_calls'] == 0

    def test_budget_status(self):
        """Should track budget status"""
        tracker = UsageTracker(budget_limit_usd=1.0)

        usage = UsageStats(input_tokens=100, output_tokens=50)
        model_info = get_model_info("gpt-4o-mini")
        usage.calculate_costs(model_info)

        response = LLMResponse(
            content="Response",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            usage=usage,
            latency_ms=1000.0
        )

        tracker.track(response)

        budget = tracker.get_budget_status()

        assert budget['limit_usd'] == 1.0
        assert budget['used_usd'] > 0.0
        assert budget['remaining_usd'] < 1.0
        assert budget['percentage_used'] > 0.0
        assert budget['is_exceeded'] is False

    def test_cost_breakdown(self):
        """Should provide cost breakdown by model"""
        tracker = UsageTracker()

        # Track two different models
        models = ["gpt-4o-mini", "gpt-3.5-turbo"]

        for model_name in models:
            usage = UsageStats(input_tokens=10, output_tokens=5)
            model_info = get_model_info(model_name)
            usage.calculate_costs(model_info)

            response = LLMResponse(
                content="Response",
                provider=LLMProvider.OPENAI,
                model=model_name,
                usage=usage,
                latency_ms=1000.0
            )

            tracker.track(response)

        breakdown = tracker.get_cost_breakdown()

        assert "openai" in breakdown
        assert "gpt-4o-mini" in breakdown["openai"]
        assert "gpt-3.5-turbo" in breakdown["openai"]

    def test_export_to_csv(self):
        """Should export tracking data to CSV"""
        tracker = UsageTracker()

        usage = UsageStats(input_tokens=10, output_tokens=5)
        model_info = get_model_info("gpt-4o-mini")
        usage.calculate_costs(model_info)

        response = LLMResponse(
            content="Response",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            usage=usage,
            latency_ms=1000.0
        )

        tracker.track(response)

        csv = tracker.export_to_csv()

        assert "timestamp,provider,model" in csv
        assert "openai,gpt-4o-mini" in csv

    def test_tag_tracking(self):
        """Should track responses by tags"""
        tracker = UsageTracker()

        usage = UsageStats(input_tokens=10, output_tokens=5)
        model_info = get_model_info("gpt-4o-mini")
        usage.calculate_costs(model_info)

        response = LLMResponse(
            content="Response",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            usage=usage,
            latency_ms=1000.0
        )

        tracker.track(response, tags=["user:123", "research"])

        # Should be able to retrieve by tag
        user_calls = tracker.get_calls_by_tag("user:123")
        assert len(user_calls) == 1

        research_calls = tracker.get_calls_by_tag("research")
        assert len(research_calls) == 1

    def test_reset_tracker(self):
        """Should reset tracker data"""
        tracker = UsageTracker()

        usage = UsageStats(input_tokens=10, output_tokens=5)
        model_info = get_model_info("gpt-4o-mini")
        usage.calculate_costs(model_info)

        response = LLMResponse(
            content="Response",
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            usage=usage,
            latency_ms=1000.0
        )

        tracker.track(response)
        assert len(tracker.calls) == 1

        tracker.reset()
        assert len(tracker.calls) == 0
