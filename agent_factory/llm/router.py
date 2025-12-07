"""
LLM Router - Unified Interface to Multiple LLM Providers

Provides single interface for calling any LLM provider through LiteLLM.
Handles cost tracking, error handling, and response standardization.

Phase 1: Direct routing (use specified model)
Phase 2: Intelligent routing (select cheapest capable model)

Part of Phase 1: LLM Abstraction Layer
"""

from typing import Optional, Dict, Any, List
import time
from datetime import datetime

try:
    from litellm import completion
except ImportError:
    raise ImportError(
        "LiteLLM not installed. Run: poetry add litellm==1.30.0"
    )

from .types import (
    LLMConfig,
    LLMResponse,
    LLMProvider,
    ModelInfo,
    UsageStats,
    ModelCapability
)
from .config import (
    get_model_info,
    validate_model_exists,
    get_default_model,
    get_cheapest_model
)


class LLMRouterError(Exception):
    """Base exception for LLM router errors"""
    pass


class ModelNotFoundError(LLMRouterError):
    """Raised when requested model doesn't exist in registry"""
    pass


class ProviderAPIError(LLMRouterError):
    """Raised when provider API call fails"""
    pass


class LLMRouter:
    """
    Unified router for multiple LLM providers.

    Features:
    - Automatic cost tracking on every call
    - Standardized response format
    - Error handling with retries
    - Support for streaming (future)
    - Foundation for intelligent routing (Phase 2)

    Example:
        >>> router = LLMRouter()
        >>> config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
        >>> response = router.complete("Hello, world!", config)
        >>> print(f"Cost: ${response.usage.total_cost_usd:.4f}")
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_fallback: bool = False
    ):
        """
        Initialize LLM router.

        Args:
            max_retries: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
            enable_fallback: Enable fallback to cheaper models on failure (Phase 2)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_fallback = enable_fallback

    def complete(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using specified model.

        Args:
            messages: List of message dicts (role, content)
            config: LLM configuration (model, temperature, etc.)
            **kwargs: Additional provider-specific parameters

        Returns:
            Standardized LLMResponse with content, usage, and cost

        Raises:
            ModelNotFoundError: If model doesn't exist in registry
            ProviderAPIError: If API call fails after retries

        Example:
            >>> messages = [{"role": "user", "content": "Hello!"}]
            >>> config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
            >>> response = router.complete(messages, config)
        """
        # Validate model exists
        if not validate_model_exists(config.model):
            raise ModelNotFoundError(
                f"Model '{config.model}' not found in registry. "
                f"Available models: {list(get_model_info(m) for m in ['gpt-4o-mini', 'claude-3-haiku-20240307'])}"
            )

        # Get model metadata for cost calculation
        model_info = get_model_info(config.model)
        if not model_info:
            raise ModelNotFoundError(f"Model info not found for '{config.model}'")

        # Attempt completion with retries
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                # Call LiteLLM
                response = self._call_litellm(messages, config, **kwargs)

                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000

                # Extract and standardize response
                return self._build_llm_response(response, config, model_info, latency_ms)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed
                    raise ProviderAPIError(
                        f"Failed to complete after {self.max_retries} attempts: {str(e)}"
                    ) from e

                # Wait before retry
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

        # Should never reach here, but satisfy type checker
        raise ProviderAPIError("Unexpected error in completion")

    def _call_litellm(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig,
        **kwargs
    ) -> Any:
        """
        Internal method to call LiteLLM completion API.

        Args:
            messages: Message list
            config: LLM configuration
            **kwargs: Additional parameters

        Returns:
            Raw LiteLLM response object
        """
        # Build LiteLLM parameters
        # Note: LLMProvider is str Enum, so config.provider is already a string
        provider_str = config.provider if isinstance(config.provider, str) else config.provider.value

        params = {
            "model": f"{provider_str}/{config.model}",
            "messages": messages,
            "temperature": config.temperature,
            "timeout": config.timeout,
            **kwargs
        }

        # Add optional parameters if specified
        if config.max_tokens:
            params["max_tokens"] = config.max_tokens

        if config.top_p is not None:
            params["top_p"] = config.top_p

        if config.stream:
            params["stream"] = True

        # Call LiteLLM (handles provider-specific API calls)
        return completion(**params)

    def _build_llm_response(
        self,
        raw_response: Any,
        config: LLMConfig,
        model_info: ModelInfo,
        latency_ms: float
    ) -> LLMResponse:
        """
        Convert raw LiteLLM response to standardized LLMResponse.

        Args:
            raw_response: Raw response from LiteLLM
            config: Request configuration
            model_info: Model metadata for cost calculation
            latency_ms: Response latency in milliseconds

        Returns:
            Standardized LLMResponse with cost tracking
        """
        # Extract content
        content = raw_response.choices[0].message.content

        # Extract usage stats
        usage_data = raw_response.usage
        usage = UsageStats(
            input_tokens=getattr(usage_data, 'prompt_tokens', 0),
            output_tokens=getattr(usage_data, 'completion_tokens', 0),
        )

        # Calculate costs
        usage.calculate_costs(model_info)

        # Extract finish reason
        finish_reason = getattr(
            raw_response.choices[0],
            'finish_reason',
            None
        )

        # Build response
        return LLMResponse(
            content=content,
            provider=config.provider,
            model=config.model,
            usage=usage,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
            finish_reason=finish_reason,
            metadata={
                "raw_model": getattr(raw_response, 'model', config.model),
                "request_id": getattr(raw_response, 'id', None),
            }
        )

    def route_by_capability(
        self,
        messages: List[Dict[str, str]],
        capability: ModelCapability,
        exclude_local: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Route request to cheapest model for capability (Phase 2 feature).

        Selects the most cost-effective model that meets the
        required capability level.

        Args:
            messages: Message list
            capability: Required capability level
            exclude_local: Exclude local Ollama models
            **kwargs: Additional parameters

        Returns:
            LLMResponse from selected model

        Example:
            >>> response = router.route_by_capability(
            ...     messages=[{"role": "user", "content": "Simple task"}],
            ...     capability=ModelCapability.SIMPLE
            ... )
            >>> print(f"Used: {response.model} (${response.usage.total_cost_usd:.4f})")
        """
        # Get cheapest model for capability
        model_name = get_cheapest_model(capability, exclude_local=exclude_local)

        if not model_name:
            raise ModelNotFoundError(
                f"No models available for capability: {capability}"
            )

        # Get model info to determine provider
        model_info = get_model_info(model_name)
        if not model_info:
            raise ModelNotFoundError(f"Model info not found for '{model_name}'")

        # Build config for selected model
        config = LLMConfig(
            provider=model_info.provider,
            model=model_name,
            temperature=kwargs.pop('temperature', 0.7),
            max_tokens=kwargs.pop('max_tokens', None)
        )

        # Call with selected model
        return self.complete(messages, config, **kwargs)


def create_router(
    max_retries: int = 3,
    enable_fallback: bool = False
) -> LLMRouter:
    """
    Factory function to create LLM router.

    Args:
        max_retries: Number of retry attempts
        enable_fallback: Enable model fallback on failure

    Returns:
        Configured LLMRouter instance

    Example:
        >>> router = create_router(max_retries=3)
        >>> # Use router for all LLM calls
    """
    return LLMRouter(
        max_retries=max_retries,
        enable_fallback=enable_fallback
    )
