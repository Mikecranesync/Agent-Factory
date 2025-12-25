"""Agent Factory HTTP Client - Resilient HTTP with retry, timeout, and tracing.

This module provides a production-ready HTTP client with:
- Automatic retry with exponential backoff
- Configurable timeouts (connect, read, total)
- Redirect handling with loop detection
- Rate limit detection (HTTP 429)
- Structured error objects for triage
- LangSmith tracing integration
- Connection pooling

Quick Start:
    >>> from agent_factory.http import get_client, CONFIGS
    >>>
    >>> # Use default API config
    >>> client = get_client()
    >>> response = client.get("https://api.example.com/data")
    >>>
    >>> if response.ok:
    ...     print(response.data)
    ... else:
    ...     print(f"Error: {response.error.summary}")

Service-Specific Configs:
    >>> # For LLM APIs (longer timeouts)
    >>> llm_client = get_client(CONFIGS["llm"])
    >>>
    >>> # For databases (shorter timeouts)
    >>> db_client = get_client(CONFIGS["database"])
    >>>
    >>> # For web scraping (longest timeouts)
    >>> scraper_client = get_client(CONFIGS["scraper"])
"""

from typing import Optional

from .client import HTTPClient, HTTPResponse
from .config import (
    HTTPClientConfig,
    TimeoutConfig,
    RetryConfig,
    RedirectConfig,
    CONFIGS,
    LLM_CONFIG,
    DATABASE_CONFIG,
    API_CONFIG,
    SCRAPER_CONFIG,
    get_config
)
from .errors import (
    HTTPError,
    HTTPClientError,
    TimeoutError,
    ConnectionError,
    RateLimitError,
    ServerError,
    ClientError,
    TooManyRedirectsError,
    DeserializationError,
    CATEGORY_TIMEOUT,
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_RATE_LIMITED,
    CATEGORY_SERVER_ERROR,
    CATEGORY_CLIENT_ERROR,
    CATEGORY_TOO_MANY_REDIRECTS,
    CATEGORY_DESERIALIZATION_ERROR,
    RETRYABLE_CATEGORIES
)
from .retry import (
    create_retry_decorator,
    should_retry_error,
    get_retry_wait_time,
    format_retry_message
)
from .tracing import (
    log_request,
    log_response,
    log_retry,
    log_error,
    is_tracing_enabled,
    get_trace_context
)


# Global default client instance
_default_client: Optional[HTTPClient] = None


def get_client(config: Optional[HTTPClientConfig] = None) -> HTTPClient:
    """Get or create global HTTP client instance.

    Args:
        config: Optional HTTPClientConfig. If None, uses default API_CONFIG.
                If provided, creates a new client with that config.

    Returns:
        HTTPClient instance

    Example:
        >>> # Get default client (API config)
        >>> client = get_client()
        >>>
        >>> # Get client with custom config
        >>> client = get_client(CONFIGS["llm"])
    """
    global _default_client

    if config is not None:
        # Always create new client when config provided
        return HTTPClient(config)

    # Create default client if not exists
    if _default_client is None:
        _default_client = HTTPClient(API_CONFIG)

    return _default_client


def reset_default_client() -> None:
    """Reset the global default client instance.

    Useful for testing or when you want to force creation of a new client
    with updated configuration.

    Example:
        >>> reset_default_client()
        >>> client = get_client()  # Creates new client
    """
    global _default_client
    _default_client = None


# Convenience functions using default client

def get(url: str, **kwargs) -> HTTPResponse:
    """Make GET request using default client.

    Args:
        url: Request URL
        **kwargs: Additional arguments passed to HTTPClient.get()

    Returns:
        HTTPResponse object

    Example:
        >>> from agent_factory.http import get
        >>> response = get("https://api.example.com/data")
        >>> if response.ok:
        ...     print(response.data)
    """
    return get_client().get(url, **kwargs)


def post(url: str, **kwargs) -> HTTPResponse:
    """Make POST request using default client.

    Args:
        url: Request URL
        **kwargs: Additional arguments passed to HTTPClient.post()

    Returns:
        HTTPResponse object

    Example:
        >>> from agent_factory.http import post
        >>> response = post("https://api.example.com/data", json={"key": "value"})
        >>> if response.ok:
        ...     print(response.data)
    """
    return get_client().post(url, **kwargs)


def put(url: str, **kwargs) -> HTTPResponse:
    """Make PUT request using default client.

    Args:
        url: Request URL
        **kwargs: Additional arguments passed to HTTPClient.put()

    Returns:
        HTTPResponse object
    """
    return get_client().put(url, **kwargs)


def delete(url: str, **kwargs) -> HTTPResponse:
    """Make DELETE request using default client.

    Args:
        url: Request URL
        **kwargs: Additional arguments passed to HTTPClient.delete()

    Returns:
        HTTPResponse object
    """
    return get_client().delete(url, **kwargs)


def patch(url: str, **kwargs) -> HTTPResponse:
    """Make PATCH request using default client.

    Args:
        url: Request URL
        **kwargs: Additional arguments passed to HTTPClient.patch()

    Returns:
        HTTPResponse object
    """
    return get_client().patch(url, **kwargs)


# Public API exports
__all__ = [
    # Client classes
    "HTTPClient",
    "HTTPResponse",

    # Configuration
    "HTTPClientConfig",
    "TimeoutConfig",
    "RetryConfig",
    "RedirectConfig",
    "CONFIGS",
    "LLM_CONFIG",
    "DATABASE_CONFIG",
    "API_CONFIG",
    "SCRAPER_CONFIG",
    "get_config",

    # Error types
    "HTTPError",
    "HTTPClientError",
    "TimeoutError",
    "ConnectionError",
    "RateLimitError",
    "ServerError",
    "ClientError",
    "TooManyRedirectsError",
    "DeserializationError",

    # Error categories (constants)
    "CATEGORY_TIMEOUT",
    "CATEGORY_CONNECTION_ERROR",
    "CATEGORY_RATE_LIMITED",
    "CATEGORY_SERVER_ERROR",
    "CATEGORY_CLIENT_ERROR",
    "CATEGORY_TOO_MANY_REDIRECTS",
    "CATEGORY_DESERIALIZATION_ERROR",
    "RETRYABLE_CATEGORIES",

    # Retry utilities
    "create_retry_decorator",
    "should_retry_error",
    "get_retry_wait_time",
    "format_retry_message",

    # Tracing utilities
    "log_request",
    "log_response",
    "log_retry",
    "log_error",
    "is_tracing_enabled",
    "get_trace_context",

    # Client management
    "get_client",
    "reset_default_client",

    # Convenience functions
    "get",
    "post",
    "put",
    "delete",
    "patch"
]


# Version information
__version__ = "1.0.0"
__author__ = "Agent Factory Team"
__license__ = "MIT"
