"""
LLM Router - Unified Interface to Multiple LLM Providers

Provides single interface for calling any LLM provider through LiteLLM.
Handles cost tracking, error handling, and response standardization.

Phase 1: Direct routing (use specified model)
Phase 2: Intelligent routing (select cheapest capable model)

Part of Phase 1: LLM Abstraction Layer
"""

from typing import Optional, Dict, Any, List, Iterator
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
    ModelCapability,
    FallbackEvent
)
from .config import (
    get_model_info,
    validate_model_exists,
    get_default_model,
    get_cheapest_model
)
from .cache import ResponseCache
from .streaming import stream_complete, collect_stream, StreamChunk


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
        enable_fallback: bool = False,
        enable_cache: bool = False,
        cache: Optional[ResponseCache] = None
    ):
        """
        Initialize LLM router.

        Args:
            max_retries: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
            enable_fallback: Enable fallback to cheaper models on failure (Phase 2)
            enable_cache: Enable response caching (Phase 2 Day 3)
            cache: Optional ResponseCache instance (creates new if None)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_fallback = enable_fallback
        self.enable_cache = enable_cache
        self.cache = cache if cache is not None else ResponseCache()

    def complete(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using specified model with fallback and caching support.

        Args:
            messages: List of message dicts (role, content)
            config: LLM configuration (model, temperature, etc.)
            **kwargs: Additional provider-specific parameters

        Returns:
            Standardized LLMResponse with content, usage, and cost

        Raises:
            ModelNotFoundError: If model doesn't exist in registry
            ProviderAPIError: If all models (primary + fallbacks) fail

        Example:
            >>> messages = [{"role": "user", "content": "Hello!"}]
            >>> config = LLMConfig(
            ...     provider=LLMProvider.OPENAI,
            ...     model="gpt-4o-mini",
            ...     fallback_models=["gpt-3.5-turbo", "claude-3-haiku-20240307"]
            ... )
            >>> response = router.complete(messages, config)
        """
        # Check cache first (Phase 2 Day 3)
        if self.enable_cache:
            cache_key = self.cache.generate_key(messages, config)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                # Cache hit - return cached response
                return cached_response

        # Build model chain: primary + fallbacks (max 3 total for circuit breaker)
        model_chain = [config.model]
        if self.enable_fallback and config.fallback_models:
            model_chain.extend(config.fallback_models[:2])  # Limit to 2 fallbacks

        fallback_events: List[FallbackEvent] = []
        last_error = None
        overall_start_time = time.time()

        # Try each model in chain
        for attempt_num, model_name in enumerate(model_chain, start=1):
            # Validate model exists
            if not validate_model_exists(model_name):
                continue  # Skip invalid models

            # Get model metadata
            model_info = get_model_info(model_name)
            if not model_info:
                continue

            # Build config for this model
            model_config = LLMConfig(
                provider=model_info.provider,
                model=model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                timeout=config.timeout,
                stream=config.stream,
                metadata=config.metadata
            )

            try:
                # Try this model with retries
                response = self._try_single_model(messages, model_config, model_info, **kwargs)

                # Success! Add fallback metadata if we used a fallback
                if attempt_num > 1:
                    response.fallback_used = True
                    response.metadata["fallback_events"] = [e.model_dump() for e in fallback_events]
                    response.metadata["primary_model"] = config.model

                # Store in cache (Phase 2 Day 3)
                if self.enable_cache:
                    cache_key = self.cache.generate_key(messages, config)
                    response.metadata["cache_hit"] = False
                    response.metadata["cache_key"] = cache_key
                    self.cache.set(cache_key, response)

                return response

            except Exception as e:
                last_error = e

                # Record fallback event if this wasn't the last model
                if attempt_num < len(model_chain):
                    fallback_time_ms = (time.time() - overall_start_time) * 1000
                    fallback_event = FallbackEvent(
                        primary_model=config.model,
                        fallback_model=model_chain[attempt_num] if attempt_num < len(model_chain) else "none",
                        failure_reason=str(e),
                        attempt_number=attempt_num,
                        latency_ms=fallback_time_ms,
                        succeeded=False
                    )
                    fallback_events.append(fallback_event)

        # All models failed - raise error
        models_tried = ", ".join(model_chain)
        raise ProviderAPIError(
            f"All models failed ({models_tried}). Last error: {str(last_error)}"
        ) from last_error

    def _try_single_model(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig,
        model_info: ModelInfo,
        **kwargs
    ) -> LLMResponse:
        """
        Try a single model with retries (Phase 2 Day 2).

        Args:
            messages: Message list
            config: Configuration for this specific model
            model_info: Model metadata
            **kwargs: Additional parameters

        Returns:
            LLMResponse on success

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        # Attempt with retries
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
                last_error = e

                # If final attempt, raise
                if attempt == self.max_retries - 1:
                    raise

                # Wait before retry with exponential backoff
                time.sleep(self.retry_delay * (attempt + 1))

        # Should never reach here, but satisfy type checker
        raise last_error if last_error else ProviderAPIError("Unexpected error")

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

    def complete_stream(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """
        Generate streaming completion (Phase 2 Days 4-5).

        Args:
            messages: List of message dicts (role, content)
            config: LLM configuration (stream=True will be set automatically)
            **kwargs: Additional provider-specific parameters

        Yields:
            StreamChunk objects as they arrive

        Raises:
            ModelNotFoundError: If model doesn't exist in registry
            ProviderAPIError: If streaming fails

        Example:
            >>> messages = [{"role": "user", "content": "Write a story"}]
            >>> config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o-mini")
            >>> for chunk in router.complete_stream(messages, config):
            ...     print(chunk.content, end="", flush=True)

        Note:
            - Streaming responses are NOT cached
            - Fallback is NOT supported for streaming
            - Usage stats may be unavailable depending on provider
        """
        # Validate model exists
        if not validate_model_exists(config.model):
            raise ModelNotFoundError(f"Model '{config.model}' not found in registry")

        # Get model info
        model_info = get_model_info(config.model)
        if not model_info:
            raise ModelNotFoundError(f"Model info not found for '{config.model}'")

        # Force streaming
        config.stream = True

        # Call LiteLLM with streaming
        try:
            raw_stream = self._call_litellm(messages, config, **kwargs)

            # Process stream
            for chunk in stream_complete(raw_stream, config.provider, config.model):
                yield chunk

        except Exception as e:
            raise ProviderAPIError(f"Streaming failed: {str(e)}") from e


def create_router(
    max_retries: int = 3,
    enable_fallback: bool = False,
    enable_cache: bool = False,
    cache: Optional[ResponseCache] = None
) -> LLMRouter:
    """
    Factory function to create LLM router.

    Args:
        max_retries: Number of retry attempts
        enable_fallback: Enable model fallback on failure
        enable_cache: Enable response caching (Phase 2 Day 3)
        cache: Optional ResponseCache instance

    Returns:
        Configured LLMRouter instance

    Example:
        >>> router = create_router(max_retries=3, enable_cache=True)
        >>> # Use router for all LLM calls
    """
    return LLMRouter(
        max_retries=max_retries,
        enable_fallback=enable_fallback,
        enable_cache=enable_cache,
        cache=cache
    )
