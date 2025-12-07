"""
LLM Abstraction Layer - Multi-Provider LLM Interface

Unified interface for multiple LLM providers with automatic cost tracking.

Phase 1: Direct routing with cost tracking
Phase 2: Intelligent routing based on task complexity

Usage:
    >>> from agent_factory.llm import LLMRouter, LLMConfig, LLMProvider
    >>>
    >>> router = LLMRouter()
    >>> config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
    >>> messages = [{"role": "user", "content": "Hello!"}]
    >>> response = router.complete(messages, config)
    >>> print(f"Cost: ${response.usage.total_cost_usd:.4f}")
"""

from .types import (
    LLMProvider,
    ModelCapability,
    ModelInfo,
    UsageStats,
    LLMResponse,
    LLMConfig,
    RouteDecision,
)

from .config import (
    MODEL_REGISTRY,
    DEFAULT_MODELS,
    ROUTING_TIERS,
    get_model_info,
    get_default_model,
    get_models_by_provider,
    get_models_by_capability,
    validate_model_exists,
    get_cheapest_model,
)

from .router import (
    LLMRouter,
    LLMRouterError,
    ModelNotFoundError,
    ProviderAPIError,
    create_router,
)

from .tracker import (
    UsageTracker,
    get_global_tracker,
    reset_global_tracker,
)

__all__ = [
    # Enums
    "LLMProvider",
    "ModelCapability",
    # Data Models
    "ModelInfo",
    "UsageStats",
    "LLMResponse",
    "LLMConfig",
    "RouteDecision",
    # Configuration
    "MODEL_REGISTRY",
    "DEFAULT_MODELS",
    "ROUTING_TIERS",
    "get_model_info",
    "get_default_model",
    "get_models_by_provider",
    "get_models_by_capability",
    "validate_model_exists",
    "get_cheapest_model",
    # Router
    "LLMRouter",
    "LLMRouterError",
    "ModelNotFoundError",
    "ProviderAPIError",
    "create_router",
    # Tracker
    "UsageTracker",
    "get_global_tracker",
    "reset_global_tracker",
]
