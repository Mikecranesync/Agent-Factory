"""Structured error types for HTTP client operations.

Provides a hierarchy of exception types for different HTTP failure scenarios,
with structured error objects that can be logged and analyzed by triage systems.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HTTPError:
    """Structured error information for HTTP operations.

    This object contains all relevant information about an HTTP error in a
    structured format that can be consumed by logging, tracing, and triage
    systems.

    Attributes:
        category: Error type (timeout, connection_error, rate_limited, etc.)
        http_status: HTTP status code if applicable
        url: Sanitized URL (secrets removed for logging safety)
        method: HTTP method (GET, POST, etc.)
        request_id: Request ID from response headers if available
        summary: Human-readable error summary for operators
        raw_error: Original exception object if available
        retry_after: Seconds to wait before retry (for rate limiting)
    """
    category: str
    http_status: Optional[int]
    url: str
    method: str
    request_id: Optional[str]
    summary: str
    raw_error: Optional[Exception]
    retry_after: Optional[int]


class HTTPClientError(Exception):
    """Base exception for all HTTP client errors.

    All HTTP client exceptions carry a structured HTTPError object that
    contains detailed information about the failure for logging and analysis.
    """

    def __init__(self, error: HTTPError):
        """Initialize with structured error object.

        Args:
            error: HTTPError object with structured error information
        """
        self.error = error
        super().__init__(error.summary)


class TimeoutError(HTTPClientError):
    """Request timeout error.

    Raised when:
    - Connection timeout exceeded
    - Read timeout exceeded
    - Total request time exceeded

    This error is retryable by default.
    """
    pass


class ConnectionError(HTTPClientError):
    """Network or connection error.

    Raised when:
    - DNS resolution failed
    - Connection refused
    - Network unreachable
    - SSL/TLS errors

    This error is retryable by default.
    """
    pass


class RateLimitError(HTTPClientError):
    """Rate limit exceeded (HTTP 429).

    Raised when:
    - Server returns HTTP 429 (Too Many Requests)
    - Rate limit headers indicate exhaustion

    This error is retryable with exponential backoff.
    The error object contains retry_after value if provided by server.
    """
    pass


class ServerError(HTTPClientError):
    """Server-side error (HTTP 5xx).

    Raised when:
    - Server returns HTTP 500 (Internal Server Error)
    - Server returns HTTP 502 (Bad Gateway)
    - Server returns HTTP 503 (Service Unavailable)
    - Server returns HTTP 504 (Gateway Timeout)
    - Any other 5xx status code

    This error is retryable by default (server issues are often transient).
    """
    pass


class ClientError(HTTPClientError):
    """Client-side error (HTTP 4xx except 429).

    Raised when:
    - Server returns HTTP 400 (Bad Request)
    - Server returns HTTP 401 (Unauthorized)
    - Server returns HTTP 403 (Forbidden)
    - Server returns HTTP 404 (Not Found)
    - Any other 4xx status code (except 429)

    This error is NOT retryable by default (client errors need fixing).
    """
    pass


class TooManyRedirectsError(HTTPClientError):
    """Too many redirects encountered.

    Raised when:
    - Redirect chain exceeds max_redirects limit
    - Circular redirect detected

    This error is NOT retryable (indicates misconfiguration).
    """
    pass


class DeserializationError(HTTPClientError):
    """Response deserialization failed.

    Raised when:
    - JSON parsing failed (malformed JSON)
    - Content-Type mismatch
    - Encoding errors

    This error is NOT retryable (response is corrupt or unexpected).
    """
    pass


# Error category constants
CATEGORY_TIMEOUT = "timeout"
CATEGORY_CONNECTION_ERROR = "connection_error"
CATEGORY_RATE_LIMITED = "rate_limited"
CATEGORY_SERVER_ERROR = "server_error"
CATEGORY_CLIENT_ERROR = "client_error"
CATEGORY_TOO_MANY_REDIRECTS = "too_many_redirects"
CATEGORY_DESERIALIZATION_ERROR = "deserialization_error"

# Retryable error categories (used by retry logic)
RETRYABLE_CATEGORIES = {
    CATEGORY_TIMEOUT,
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_RATE_LIMITED,
    CATEGORY_SERVER_ERROR
}
