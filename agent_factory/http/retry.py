"""Retry strategy implementation using tenacity library.

Provides retry decorators configured from RetryConfig objects. Uses
tenacity library (already installed) for robust retry logic with
exponential backoff and jitter.
"""

from typing import Callable
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState
)
import logging

from .config import RetryConfig
from .errors import (
    HTTPClientError,
    TimeoutError,
    ConnectionError,
    RateLimitError,
    ServerError,
    ClientError,
    TooManyRedirectsError,
    DeserializationError
)

logger = logging.getLogger(__name__)


# Map error categories to exception types
CATEGORY_TO_EXCEPTION = {
    "timeout": TimeoutError,
    "connection_error": ConnectionError,
    "rate_limited": RateLimitError,
    "server_error": ServerError,
    "client_error": ClientError,
    "too_many_redirects": TooManyRedirectsError,
    "deserialization_error": DeserializationError
}


def create_retry_decorator(config: RetryConfig) -> Callable:
    """Create a tenacity retry decorator from config.

    Args:
        config: RetryConfig object specifying retry behavior

    Returns:
        Configured tenacity retry decorator

    Example:
        >>> config = RetryConfig(max_attempts=3, initial_wait=0.5)
        >>> retry_decorator = create_retry_decorator(config)
        >>> @retry_decorator
        ... def make_request():
        ...     # Request logic here
        ...     pass
    """
    # Build list of exception types to retry on
    retry_exceptions = []
    for category in config.retry_on:
        exception_type = CATEGORY_TO_EXCEPTION.get(category)
        if exception_type:
            retry_exceptions.append(exception_type)

    # If no specific exceptions configured, retry on all HTTPClientError
    if not retry_exceptions:
        retry_exceptions = [HTTPClientError]

    # Choose wait strategy based on jitter setting
    if config.jitter:
        wait_strategy = wait_exponential_jitter(
            initial=config.initial_wait,
            max=config.max_wait,
            exp_base=config.exponential_base
        )
    else:
        wait_strategy = wait_exponential(
            multiplier=config.initial_wait,
            max=config.max_wait,
            exp_base=config.exponential_base
        )

    # Build retry decorator
    return retry(
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_strategy,
        retry=retry_if_exception_type(tuple(retry_exceptions)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True  # Re-raise final exception after all retries exhausted
    )


def should_retry_error(error: HTTPClientError, retry_categories: list[str]) -> bool:
    """Determine if an error should be retried based on its category.

    Args:
        error: HTTPClientError exception
        retry_categories: List of error categories that should be retried

    Returns:
        True if error should be retried, False otherwise

    Example:
        >>> error = RateLimitError(HTTPError(...))
        >>> should_retry_error(error, ["rate_limited", "timeout"])
        True
    """
    if not hasattr(error, "error") or not hasattr(error.error, "category"):
        return False

    return error.error.category in retry_categories


def get_retry_wait_time(attempt: int, config: RetryConfig) -> float:
    """Calculate wait time for a specific retry attempt.

    Args:
        attempt: Retry attempt number (1-indexed)
        config: RetryConfig object

    Returns:
        Wait time in seconds

    Example:
        >>> config = RetryConfig(initial_wait=0.5, exponential_base=2.0, max_wait=10.0)
        >>> get_retry_wait_time(1, config)  # First retry
        0.5
        >>> get_retry_wait_time(2, config)  # Second retry
        1.0
        >>> get_retry_wait_time(3, config)  # Third retry
        2.0
    """
    wait_time = config.initial_wait * (config.exponential_base ** (attempt - 1))
    return min(wait_time, config.max_wait)


def format_retry_message(error: HTTPClientError, attempt: int, max_attempts: int, wait_time: float) -> str:
    """Format a human-readable retry message.

    Args:
        error: HTTPClientError that triggered retry
        attempt: Current attempt number
        max_attempts: Maximum attempts configured
        wait_time: Wait time before next retry

    Returns:
        Formatted retry message

    Example:
        >>> error = ServerError(HTTPError(category="server_error", ...))
        >>> format_retry_message(error, 1, 3, 0.5)
        "HTTP retry 1/3 after server_error (waiting 0.5s)"
    """
    category = error.error.category if hasattr(error, "error") else "unknown"
    return f"HTTP retry {attempt}/{max_attempts} after {category} (waiting {wait_time:.1f}s)"
