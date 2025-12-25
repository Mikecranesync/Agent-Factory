"""Tracing and logging hooks for HTTP client with LangSmith integration.

Provides structured logging and optional LangSmith tracing for all HTTP
operations. Gracefully degrades if LangSmith is not configured.
"""

import logging
from typing import Dict, Any, Optional
from .errors import HTTPError

logger = logging.getLogger(__name__)

# Try to import LangSmith/Langfuse for tracing
# Gracefully degrade if not available or not configured
LANGFUSE_ENABLED = False
langfuse = None

try:
    from langfuse import Langfuse
    langfuse = Langfuse()
    LANGFUSE_ENABLED = True
    logger.info("LangSmith tracing enabled for HTTP client")
except ImportError:
    logger.debug("Langfuse not installed - LangSmith tracing disabled")
except Exception as e:
    logger.debug(f"Langfuse initialization failed ({e}) - LangSmith tracing disabled")


def log_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> None:
    """Log outbound HTTP request with LangSmith tracing.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL (should be pre-sanitized)
        headers: Request headers (optional)
        params: Query parameters (optional)
        trace_id: LangSmith trace ID (optional)

    Example:
        >>> log_request("GET", "https://api.example.com/data", trace_id="abc123")
    """
    # Structured logging
    logger.debug(f"HTTP {method} {url}", extra={
        "http_method": method,
        "http_url": url,
        "http_params": params,
        "trace_id": trace_id
    })

    # LangSmith span (if enabled and trace_id provided)
    if LANGFUSE_ENABLED and langfuse and trace_id:
        try:
            langfuse.span(
                name=f"HTTP {method}",
                trace_id=trace_id,
                input={
                    "method": method,
                    "url": url,
                    "params": params
                },
                metadata={
                    "http_method": method,
                    "http_url": url
                }
            )
        except Exception as e:
            logger.debug(f"LangSmith span creation failed: {e}")


def log_response(
    status: int,
    url: str,
    duration_ms: float,
    trace_id: Optional[str] = None
) -> None:
    """Log HTTP response with LangSmith tracing.

    Args:
        status: HTTP status code
        url: Request URL (should be pre-sanitized)
        duration_ms: Request duration in milliseconds
        trace_id: LangSmith trace ID (optional)

    Example:
        >>> log_response(200, "https://api.example.com/data", 523.4, "abc123")
    """
    # Structured logging
    logger.debug(f"HTTP {status} {url} ({duration_ms:.0f}ms)", extra={
        "http_status": status,
        "http_url": url,
        "http_duration_ms": duration_ms,
        "trace_id": trace_id
    })

    # LangSmith metric (if enabled and trace_id provided)
    if LANGFUSE_ENABLED and langfuse and trace_id:
        try:
            langfuse.score(
                trace_id=trace_id,
                name="http_response_time_ms",
                value=duration_ms
            )
        except Exception as e:
            logger.debug(f"LangSmith score recording failed: {e}")


def log_retry(
    attempt: int,
    max_attempts: int,
    error: HTTPError,
    wait_time: float,
    trace_id: Optional[str] = None
) -> None:
    """Log retry attempt with LangSmith tracing.

    Args:
        attempt: Current attempt number (1-indexed)
        max_attempts: Maximum attempts configured
        error: HTTPError that triggered retry
        wait_time: Wait time before next retry (seconds)
        trace_id: LangSmith trace ID (optional)

    Example:
        >>> error = HTTPError(category="timeout", ...)
        >>> log_retry(1, 3, error, 0.5, "abc123")
    """
    # Structured logging
    logger.warning(
        f"HTTP retry {attempt}/{max_attempts} after {error.category} (waiting {wait_time:.1f}s)",
        extra={
            "http_retry_attempt": attempt,
            "http_retry_max": max_attempts,
            "http_error_category": error.category,
            "http_wait_time": wait_time,
            "trace_id": trace_id
        }
    )

    # LangSmith event (if enabled and trace_id provided)
    if LANGFUSE_ENABLED and langfuse and trace_id:
        try:
            langfuse.event(
                trace_id=trace_id,
                name="http_retry",
                metadata={
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "error_category": error.category,
                    "wait_time": wait_time
                }
            )
        except Exception as e:
            logger.debug(f"LangSmith event recording failed: {e}")


def log_error(
    error: HTTPError,
    trace_id: Optional[str] = None
) -> None:
    """Log final HTTP error with LangSmith tracing.

    Args:
        error: HTTPError object with error details
        trace_id: LangSmith trace ID (optional)

    Example:
        >>> error = HTTPError(category="server_error", http_status=500, ...)
        >>> log_error(error, "abc123")
    """
    # Structured logging
    logger.error(f"HTTP error: {error.summary}", extra={
        "http_error_category": error.category,
        "http_status": error.http_status,
        "http_url": error.url,
        "http_method": error.method,
        "trace_id": trace_id
    })

    # LangSmith error tracking (if enabled and trace_id provided)
    if LANGFUSE_ENABLED and langfuse and trace_id:
        try:
            langfuse.score(
                trace_id=trace_id,
                name="http_error",
                value=0,  # 0 = failed
                comment=error.summary,
                metadata={
                    "category": error.category,
                    "status": error.http_status,
                    "url": error.url
                }
            )
        except Exception as e:
            logger.debug(f"LangSmith error tracking failed: {e}")


def is_tracing_enabled() -> bool:
    """Check if LangSmith tracing is enabled.

    Returns:
        True if LangSmith is configured and available, False otherwise

    Example:
        >>> if is_tracing_enabled():
        ...     trace_id = generate_trace_id()
        ...     log_request("GET", url, trace_id=trace_id)
    """
    return LANGFUSE_ENABLED and langfuse is not None


def get_trace_context() -> Dict[str, Any]:
    """Get current trace context if available.

    Returns:
        Dictionary with trace context, or empty dict if tracing disabled

    Example:
        >>> context = get_trace_context()
        >>> if context:
        ...     trace_id = context.get("trace_id")
    """
    if not is_tracing_enabled():
        return {}

    # Could add logic here to get current trace context from thread-local storage
    # or from LangSmith context manager if available
    return {}
