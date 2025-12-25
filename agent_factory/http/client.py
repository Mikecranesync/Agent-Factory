"""Main HTTP client with retry, timeout, and redirect handling.

Provides HTTPClient class that wraps requests library with production-ready
error handling, retry logic, and structured error reporting.
"""

import time
import requests
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

from .config import HTTPClientConfig, API_CONFIG
from .errors import (
    HTTPError,
    HTTPClientError,
    TimeoutError,
    ConnectionError,
    RateLimitError,
    ServerError,
    ClientError,
    TooManyRedirectsError,
    DeserializationError
)
from .retry import create_retry_decorator
from .tracing import log_request, log_response, log_error, log_retry


@dataclass
class HTTPResponse:
    """Structured HTTP response object.

    Attributes:
        ok: True if request succeeded, False if error occurred
        status_code: HTTP status code
        data: Parsed response body (JSON dict or text string)
        headers: Response headers as dictionary
        raw: Original requests.Response object (if successful)
        error: HTTPError object (if failed)
    """
    ok: bool
    status_code: int
    data: Optional[Any]
    headers: Dict[str, str]
    raw: Optional[requests.Response]
    error: Optional[HTTPError] = None


class HTTPClient:
    """Resilient HTTP client with retry, timeout, and redirect handling.

    Features:
    - Automatic retry with exponential backoff
    - Configurable timeouts (connect, read, total)
    - Redirect handling with loop detection
    - Rate limit detection (HTTP 429)
    - Structured error objects for triage
    - LangSmith tracing integration
    - Connection pooling via requests.Session

    Example:
        >>> from agent_factory.http import HTTPClient, API_CONFIG
        >>> client = HTTPClient(API_CONFIG)
        >>> response = client.get("https://api.example.com/data")
        >>> if response.ok:
        ...     print(response.data)
        ... else:
        ...     print(f"Error: {response.error.summary}")
    """

    def __init__(self, config: Optional[HTTPClientConfig] = None):
        """Initialize HTTP client.

        Args:
            config: HTTPClientConfig object. If None, uses default API_CONFIG
        """
        self.config = config or API_CONFIG
        self.session = requests.Session()

        # Configure session-level redirect handling
        self.session.max_redirects = self.config.redirect.max_redirects

        # Create retry decorator from config
        self._retry_decorator = create_retry_decorator(self.config.retry)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[Union[float, tuple]] = None,
        retry: Optional[bool] = None,
        trace_id: Optional[str] = None
    ) -> HTTPResponse:
        """Make HTTP request with automatic retry and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            headers: Optional request headers
            params: Optional query parameters
            json: Optional JSON request body
            data: Optional raw request body
            timeout: Optional timeout override (seconds or (connect, read) tuple)
            retry: Optional retry override (default: True)
            trace_id: Optional LangSmith trace ID

        Returns:
            HTTPResponse object with structured result

        Example:
            >>> response = client.request("POST", url, json={"key": "value"})
            >>> if response.ok:
            ...     print(response.data)
        """
        # Determine timeout value
        if timeout is None:
            timeout_tuple = (self.config.timeout.connect, self.config.timeout.read)
        elif isinstance(timeout, (int, float)):
            timeout_tuple = (timeout, timeout)
        else:
            timeout_tuple = timeout

        # Log request
        if self.config.enable_logging:
            log_request(method, self._sanitize_url(url), headers, params, trace_id)

        # Track request timing
        start_time = time.time()

        try:
            # Apply retry if enabled (default: True)
            if retry is None or retry:
                raw_response = self._do_request_with_retry(
                    method, url, headers, params, json, data, timeout_tuple, trace_id
                )
            else:
                raw_response = self._do_request(
                    method, url, headers, params, json, data, timeout_tuple
                )

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            if self.config.enable_logging:
                log_response(raw_response.status_code, self._sanitize_url(url), duration_ms, trace_id)

            # Parse and return response
            return self._parse_response(raw_response)

        except HTTPClientError as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            if self.config.enable_logging:
                log_error(e.error, trace_id)

            # Return error response
            return HTTPResponse(
                ok=False,
                status_code=e.error.http_status or 0,
                data=None,
                headers={},
                raw=None,
                error=e.error
            )

    def _do_request_with_retry(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        params: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        data: Optional[Any],
        timeout: tuple,
        trace_id: Optional[str]
    ) -> requests.Response:
        """Execute request with retry decorator applied.

        This method is decorated by tenacity retry logic from config.

        Args:
            Same as _do_request plus trace_id

        Returns:
            requests.Response object

        Raises:
            HTTPClientError: On final failure after all retries exhausted
        """
        # Apply retry decorator dynamically
        @self._retry_decorator
        def _retry_wrapper():
            return self._do_request(method, url, headers, params, json, data, timeout)

        return _retry_wrapper()

    def _do_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        params: Optional[Dict[str, Any]],
        json: Optional[Dict[str, Any]],
        data: Optional[Any],
        timeout: tuple
    ) -> requests.Response:
        """Execute single HTTP request with error mapping.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            json: JSON request body
            data: Raw request body
            timeout: (connect_timeout, read_timeout) tuple

        Returns:
            requests.Response object

        Raises:
            TimeoutError: On timeout
            ConnectionError: On connection failure
            RateLimitError: On HTTP 429
            ServerError: On HTTP 5xx
            ClientError: On HTTP 4xx (except 429)
            TooManyRedirectsError: On redirect loop
        """
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout,
                allow_redirects=self.config.redirect.follow
            )

            # Check for rate limiting (HTTP 429)
            if response.status_code == 429:
                retry_after = self._parse_retry_after(response.headers)
                raise RateLimitError(HTTPError(
                    category="rate_limited",
                    http_status=429,
                    url=self._sanitize_url(url),
                    method=method,
                    request_id=response.headers.get("X-Request-ID"),
                    summary=f"Rate limited. Retry after {retry_after}s" if retry_after else "Rate limited",
                    raw_error=None,
                    retry_after=retry_after
                ))

            # Check for server errors (5xx - retryable)
            if 500 <= response.status_code < 600:
                raise ServerError(HTTPError(
                    category="server_error",
                    http_status=response.status_code,
                    url=self._sanitize_url(url),
                    method=method,
                    request_id=response.headers.get("X-Request-ID"),
                    summary=f"Server error: HTTP {response.status_code}",
                    raw_error=None,
                    retry_after=None
                ))

            # Check for client errors (4xx - non-retryable except 429)
            if 400 <= response.status_code < 500 and response.status_code != 429:
                raise ClientError(HTTPError(
                    category="client_error",
                    http_status=response.status_code,
                    url=self._sanitize_url(url),
                    method=method,
                    request_id=response.headers.get("X-Request-ID"),
                    summary=f"Client error: HTTP {response.status_code}",
                    raw_error=None,
                    retry_after=None
                ))

            # Success - return response
            return response

        except requests.exceptions.Timeout as e:
            raise TimeoutError(HTTPError(
                category="timeout",
                http_status=None,
                url=self._sanitize_url(url),
                method=method,
                request_id=None,
                summary=f"Request timeout after {timeout[1]}s",
                raw_error=e,
                retry_after=None
            ))

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(HTTPError(
                category="connection_error",
                http_status=None,
                url=self._sanitize_url(url),
                method=method,
                request_id=None,
                summary=f"Connection failed: {str(e)[:100]}",
                raw_error=e,
                retry_after=None
            ))

        except requests.exceptions.TooManyRedirects as e:
            raise TooManyRedirectsError(HTTPError(
                category="too_many_redirects",
                http_status=None,
                url=self._sanitize_url(url),
                method=method,
                request_id=None,
                summary=f"Too many redirects (max: {self.config.redirect.max_redirects})",
                raw_error=e,
                retry_after=None
            ))

    def _parse_response(self, response: requests.Response) -> HTTPResponse:
        """Parse HTTP response with deserialization error handling.

        Args:
            response: requests.Response object

        Returns:
            HTTPResponse object with parsed data

        Raises:
            DeserializationError: If response parsing fails
        """
        try:
            # Try to parse as JSON if content-type indicates JSON
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type or "text/json" in content_type:
                data = response.json()
            else:
                # Otherwise return as text
                data = response.text

            return HTTPResponse(
                ok=True,
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
                raw=response,
                error=None
            )

        except Exception as e:
            raise DeserializationError(HTTPError(
                category="deserialization_error",
                http_status=response.status_code,
                url=self._sanitize_url(response.url),
                method=response.request.method,
                request_id=response.headers.get("X-Request-ID"),
                summary=f"Failed to parse response: {str(e)[:100]}",
                raw_error=e,
                retry_after=None
            ))

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """Remove secrets from URL for safe logging.

        Args:
            url: Original URL

        Returns:
            Sanitized URL with query params masked

        Example:
            >>> HTTPClient._sanitize_url("https://api.example.com/data?token=secret123")
            "https://api.example.com/data?..."
        """
        # Remove query params that might contain tokens/secrets
        if "?" in url:
            base_url = url.split("?")[0]
            return f"{base_url}?..."
        return url

    @staticmethod
    def _parse_retry_after(headers: Dict[str, str]) -> Optional[int]:
        """Parse Retry-After header from rate limit response.

        Args:
            headers: Response headers dictionary

        Returns:
            Retry-after value in seconds, or None if not present

        Example:
            >>> headers = {"Retry-After": "60"}
            >>> HTTPClient._parse_retry_after(headers)
            60
        """
        # Check standard Retry-After header
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after and retry_after.isdigit():
            return int(retry_after)

        # Check X-RateLimit-Reset header (GitHub, Twitter style)
        reset_header = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        if reset_header and reset_header.isdigit():
            # Convert Unix timestamp to seconds from now
            reset_time = int(reset_header)
            current_time = int(time.time())
            if reset_time > current_time:
                return reset_time - current_time

        return None

    # Convenience methods for common HTTP methods

    def get(self, url: str, **kwargs) -> HTTPResponse:
        """Make GET request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to request()

        Returns:
            HTTPResponse object
        """
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> HTTPResponse:
        """Make POST request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to request()

        Returns:
            HTTPResponse object
        """
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> HTTPResponse:
        """Make PUT request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to request()

        Returns:
            HTTPResponse object
        """
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> HTTPResponse:
        """Make DELETE request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to request()

        Returns:
            HTTPResponse object
        """
        return self.request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs) -> HTTPResponse:
        """Make PATCH request.

        Args:
            url: Request URL
            **kwargs: Additional arguments passed to request()

        Returns:
            HTTPResponse object
        """
        return self.request("PATCH", url, **kwargs)
