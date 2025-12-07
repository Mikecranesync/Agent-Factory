"""
Usage Tracker - Cost and Performance Monitoring

Tracks LLM usage across multiple calls for cost monitoring,
budget alerts, and optimization insights.

Supports per-user, per-team, and per-agent tracking for
multi-tenant SaaS (Phase 9).

Part of Phase 1: LLM Abstraction Layer
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .types import LLMResponse, LLMProvider, UsageStats


class UsageTracker:
    """
    Track LLM usage and costs across multiple calls.

    Provides aggregated statistics for monitoring, budgeting,
    and optimization. Supports filtering by provider, model,
    time range, and custom tags.

    Example:
        >>> tracker = UsageTracker()
        >>> # Track each LLM call
        >>> tracker.track(response1)
        >>> tracker.track(response2)
        >>> # Get statistics
        >>> stats = tracker.get_stats()
        >>> print(f"Total cost: ${stats['total_cost_usd']:.2f}")
        >>> print(f"Total calls: {stats['total_calls']}")
    """

    def __init__(self, budget_limit_usd: Optional[float] = None):
        """
        Initialize usage tracker.

        Args:
            budget_limit_usd: Optional budget limit for alerts
        """
        self.calls: List[LLMResponse] = []
        self.budget_limit_usd = budget_limit_usd
        self._by_provider: Dict[LLMProvider, List[LLMResponse]] = defaultdict(list)
        self._by_model: Dict[str, List[LLMResponse]] = defaultdict(list)
        self._tags: Dict[str, List[LLMResponse]] = defaultdict(list)

    def track(
        self,
        response: LLMResponse,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Track an LLM response.

        Args:
            response: LLMResponse to track
            tags: Optional tags for categorization (e.g., ["user:123", "agent:bob"])

        Example:
            >>> tracker.track(response, tags=["user:john", "research"])
        """
        # Add to main list
        self.calls.append(response)

        # Index by provider
        self._by_provider[response.provider].append(response)

        # Index by model
        self._by_model[response.model].append(response)

        # Index by tags
        if tags:
            for tag in tags:
                self._tags[tag].append(response)

        # Check budget limit
        if self.budget_limit_usd:
            total_cost = self.get_total_cost()
            if total_cost >= self.budget_limit_usd:
                # TODO: Trigger alert (Phase 6)
                pass

    def get_stats(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        tag: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated usage statistics.

        Args:
            provider: Filter by provider
            model: Filter by model
            tag: Filter by tag
            since: Only include calls after this timestamp

        Returns:
            Dictionary with usage statistics

        Example:
            >>> stats = tracker.get_stats(provider=LLMProvider.OPENAI)
            >>> print(f"OpenAI cost: ${stats['total_cost_usd']:.2f}")
        """
        # Filter calls
        calls = self._filter_calls(provider, model, tag, since)

        if not calls:
            return {
                "total_calls": 0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "avg_latency_ms": 0.0,
                "providers": {},
                "models": {},
            }

        # Aggregate usage
        total_usage = UsageStats()
        total_latency = 0.0
        provider_costs: Dict[str, float] = defaultdict(float)
        model_costs: Dict[str, float] = defaultdict(float)

        for call in calls:
            total_usage.input_tokens += call.usage.input_tokens
            total_usage.output_tokens += call.usage.output_tokens
            total_usage.total_tokens += call.usage.total_tokens
            total_usage.total_cost_usd += call.usage.total_cost_usd
            total_latency += call.latency_ms

            # Handle both string and enum provider values
            provider_key = call.provider if isinstance(call.provider, str) else call.provider.value
            provider_costs[provider_key] += call.usage.total_cost_usd
            model_costs[call.model] += call.usage.total_cost_usd

        return {
            "total_calls": len(calls),
            "total_cost_usd": total_usage.total_cost_usd,
            "total_tokens": total_usage.total_tokens,
            "input_tokens": total_usage.input_tokens,
            "output_tokens": total_usage.output_tokens,
            "avg_latency_ms": total_latency / len(calls),
            "avg_cost_per_call": total_usage.total_cost_usd / len(calls),
            "providers": dict(provider_costs),
            "models": dict(model_costs),
            "time_range": {
                "first_call": calls[0].timestamp.isoformat() if calls else None,
                "last_call": calls[-1].timestamp.isoformat() if calls else None,
            }
        }

    def get_total_cost(self) -> float:
        """
        Get total cost across all tracked calls.

        Returns:
            Total cost in USD
        """
        return sum(call.usage.total_cost_usd for call in self.calls)

    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get budget status and remaining amount.

        Returns:
            Budget status information

        Example:
            >>> status = tracker.get_budget_status()
            >>> print(f"Used: ${status['used_usd']:.2f} / ${status['limit_usd']:.2f}")
            >>> print(f"Remaining: ${status['remaining_usd']:.2f}")
        """
        total_cost = self.get_total_cost()

        return {
            "limit_usd": self.budget_limit_usd,
            "used_usd": total_cost,
            "remaining_usd": (self.budget_limit_usd - total_cost) if self.budget_limit_usd else None,
            "percentage_used": (total_cost / self.budget_limit_usd * 100) if self.budget_limit_usd else None,
            "is_exceeded": (total_cost >= self.budget_limit_usd) if self.budget_limit_usd else False,
        }

    def get_calls_by_provider(self, provider: LLMProvider) -> List[LLMResponse]:
        """Get all calls for a specific provider."""
        return self._by_provider.get(provider, [])

    def get_calls_by_model(self, model: str) -> List[LLMResponse]:
        """Get all calls for a specific model."""
        return self._by_model.get(model, [])

    def get_calls_by_tag(self, tag: str) -> List[LLMResponse]:
        """Get all calls with a specific tag."""
        return self._tags.get(tag, [])

    def get_cost_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get detailed cost breakdown by provider and model.

        Returns:
            Nested dict with costs by provider and model

        Example:
            >>> breakdown = tracker.get_cost_breakdown()
            >>> print(breakdown)
            {
                "openai": {
                    "gpt-4o-mini": 0.05,
                    "gpt-4o": 0.25
                },
                "anthropic": {
                    "claude-3-haiku-20240307": 0.03
                }
            }
        """
        breakdown: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for call in self.calls:
            # Handle both string and enum provider values
            provider_key = call.provider if isinstance(call.provider, str) else call.provider.value
            model_key = call.model
            breakdown[provider_key][model_key] += call.usage.total_cost_usd

        return dict(breakdown)

    def export_to_csv(self) -> str:
        """
        Export tracking data to CSV format.

        Returns:
            CSV string with all call data

        Example:
            >>> csv = tracker.export_to_csv()
            >>> with open('usage_log.csv', 'w') as f:
            ...     f.write(csv)
        """
        # CSV header
        lines = [
            "timestamp,provider,model,input_tokens,output_tokens,total_tokens,"
            "input_cost_usd,output_cost_usd,total_cost_usd,latency_ms,finish_reason"
        ]

        # Add each call
        for call in self.calls:
            # Handle both string and enum provider values
            provider_key = call.provider if isinstance(call.provider, str) else call.provider.value

            lines.append(
                f"{call.timestamp.isoformat()},"
                f"{provider_key},"
                f"{call.model},"
                f"{call.usage.input_tokens},"
                f"{call.usage.output_tokens},"
                f"{call.usage.total_tokens},"
                f"{call.usage.input_cost_usd:.6f},"
                f"{call.usage.output_cost_usd:.6f},"
                f"{call.usage.total_cost_usd:.6f},"
                f"{call.latency_ms:.2f},"
                f"{call.finish_reason or ''}"
            )

        return "\n".join(lines)

    def reset(self) -> None:
        """Clear all tracking data."""
        self.calls.clear()
        self._by_provider.clear()
        self._by_model.clear()
        self._tags.clear()

    def _filter_calls(
        self,
        provider: Optional[LLMProvider],
        model: Optional[str],
        tag: Optional[str],
        since: Optional[datetime]
    ) -> List[LLMResponse]:
        """Internal method to filter calls by criteria."""
        # Start with appropriate subset
        if tag:
            calls = self._tags.get(tag, [])
        elif model:
            calls = self._by_model.get(model, [])
        elif provider:
            calls = self._by_provider.get(provider, [])
        else:
            calls = self.calls

        # Apply time filter if specified
        if since:
            calls = [c for c in calls if c.timestamp >= since]

        return calls


# Global tracker instance (optional singleton pattern)
_global_tracker: Optional[UsageTracker] = None


def get_global_tracker(budget_limit_usd: Optional[float] = None) -> UsageTracker:
    """
    Get or create global usage tracker instance.

    Singleton pattern for application-wide tracking.

    Args:
        budget_limit_usd: Budget limit (only used on first call)

    Returns:
        Global UsageTracker instance

    Example:
        >>> tracker = get_global_tracker(budget_limit_usd=10.0)
        >>> # Use same tracker everywhere
        >>> tracker2 = get_global_tracker()
        >>> assert tracker is tracker2
    """
    global _global_tracker

    if _global_tracker is None:
        _global_tracker = UsageTracker(budget_limit_usd=budget_limit_usd)

    return _global_tracker


def reset_global_tracker() -> None:
    """Reset global tracker to None (for testing)."""
    global _global_tracker
    _global_tracker = None
