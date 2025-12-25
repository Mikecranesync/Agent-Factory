"""Configuration system for HTTP client.

Provides configuration dataclasses for timeouts, retries, redirects, and
complete HTTP client configuration. Includes 4 predefined configs optimized
for different service types (LLM APIs, databases, general APIs, web scraping).
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Callable, List


@dataclass
class TimeoutConfig:
    """Timeout configuration for HTTP requests.

    Attributes:
        connect: Maximum time to wait for connection establishment (seconds)
        read: Maximum time to wait for response after connection (seconds)
        total: Maximum total time for entire request including retries (seconds)
    """
    connect: float = 5.0
    read: float = 10.0
    total: float = 30.0

    @classmethod
    def from_env(cls) -> "TimeoutConfig":
        """Load timeout configuration from environment variables.

        Environment variables:
            HTTP_CONNECT_TIMEOUT: Connect timeout in seconds (default: 5.0)
            HTTP_READ_TIMEOUT: Read timeout in seconds (default: 10.0)
            HTTP_TOTAL_TIMEOUT: Total timeout in seconds (default: 30.0)
        """
        return cls(
            connect=float(os.getenv("HTTP_CONNECT_TIMEOUT", "5.0")),
            read=float(os.getenv("HTTP_READ_TIMEOUT", "10.0")),
            total=float(os.getenv("HTTP_TOTAL_TIMEOUT", "30.0"))
        )


@dataclass
class RetryConfig:
    """Retry policy configuration.

    Attributes:
        max_attempts: Maximum number of retry attempts (including initial attempt)
        initial_wait: Initial wait time before first retry (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        jitter: Add random jitter to backoff to avoid thundering herd
        retry_on: List of error categories that should trigger retry
    """
    max_attempts: int = 3
    initial_wait: float = 0.5
    max_wait: float = 10.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: List[str] = field(default_factory=lambda: [
        "timeout",
        "connection_error",
        "server_error",
        "rate_limited"
    ])

    @classmethod
    def from_env(cls) -> "RetryConfig":
        """Load retry configuration from environment variables.

        Environment variables:
            HTTP_MAX_RETRIES: Max retry attempts (default: 3)
            HTTP_INITIAL_BACKOFF: Initial backoff in seconds (default: 0.5)
            HTTP_MAX_BACKOFF: Max backoff in seconds (default: 10.0)
        """
        return cls(
            max_attempts=int(os.getenv("HTTP_MAX_RETRIES", "3")),
            initial_wait=float(os.getenv("HTTP_INITIAL_BACKOFF", "0.5")),
            max_wait=float(os.getenv("HTTP_MAX_BACKOFF", "10.0"))
        )


@dataclass
class RedirectConfig:
    """Redirect handling configuration.

    Attributes:
        follow: Whether to follow redirects automatically
        max_redirects: Maximum number of redirects to follow
    """
    follow: bool = True
    max_redirects: int = 5

    @classmethod
    def from_env(cls) -> "RedirectConfig":
        """Load redirect configuration from environment variables.

        Environment variables:
            HTTP_FOLLOW_REDIRECTS: Whether to follow redirects (default: true)
            HTTP_MAX_REDIRECTS: Max redirects to follow (default: 5)
        """
        follow_str = os.getenv("HTTP_FOLLOW_REDIRECTS", "true").lower()
        return cls(
            follow=follow_str in ("true", "1", "yes"),
            max_redirects=int(os.getenv("HTTP_MAX_REDIRECTS", "5"))
        )


@dataclass
class HTTPClientConfig:
    """Complete HTTP client configuration.

    Attributes:
        timeout: Timeout configuration
        retry: Retry policy configuration
        redirect: Redirect handling configuration
        service_name: Optional service name for logging/tracing
        enable_logging: Whether to enable structured logging
        logger: Optional custom logger function
    """
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    redirect: RedirectConfig = field(default_factory=RedirectConfig)
    service_name: Optional[str] = None
    enable_logging: bool = True
    logger: Optional[Callable] = None

    @classmethod
    def from_env(cls, service_name: Optional[str] = None) -> "HTTPClientConfig":
        """Load complete configuration from environment variables.

        Args:
            service_name: Optional service name for logging

        Environment variables:
            HTTP_ENABLE_LOGGING: Whether to enable logging (default: true)
            Plus all timeout, retry, and redirect env vars
        """
        logging_str = os.getenv("HTTP_ENABLE_LOGGING", "true").lower()
        enable_logging = logging_str in ("true", "1", "yes")

        return cls(
            timeout=TimeoutConfig.from_env(),
            retry=RetryConfig.from_env(),
            redirect=RedirectConfig.from_env(),
            service_name=service_name,
            enable_logging=enable_logging
        )


# Predefined configurations for different service types

LLM_CONFIG = HTTPClientConfig(
    timeout=TimeoutConfig(
        connect=5.0,
        read=60.0,   # LLMs can take time to generate responses
        total=90.0
    ),
    retry=RetryConfig(
        max_attempts=3,
        initial_wait=1.0,  # Longer initial wait for expensive LLM calls
        max_wait=20.0
    ),
    redirect=RedirectConfig(follow=True, max_redirects=3),
    service_name="llm"
)

DATABASE_CONFIG = HTTPClientConfig(
    timeout=TimeoutConfig(
        connect=2.0,    # Databases should connect quickly
        read=5.0,       # Short read timeout for fast queries
        total=10.0
    ),
    retry=RetryConfig(
        max_attempts=2,  # Fewer retries for database operations
        initial_wait=0.2,
        max_wait=2.0
    ),
    redirect=RedirectConfig(follow=False, max_redirects=0),  # Databases don't redirect
    service_name="database"
)

API_CONFIG = HTTPClientConfig(
    timeout=TimeoutConfig(
        connect=5.0,
        read=10.0,
        total=30.0
    ),
    retry=RetryConfig(
        max_attempts=3,
        initial_wait=0.5,
        max_wait=10.0
    ),
    redirect=RedirectConfig(follow=True, max_redirects=5),
    service_name="api"
)

SCRAPER_CONFIG = HTTPClientConfig(
    timeout=TimeoutConfig(
        connect=10.0,    # Web servers can be slow
        read=30.0,       # Large pages take time to transfer
        total=60.0
    ),
    retry=RetryConfig(
        max_attempts=3,
        initial_wait=2.0,  # Longer backoff for web scraping
        max_wait=20.0
    ),
    redirect=RedirectConfig(follow=True, max_redirects=10),  # Websites redirect more
    service_name="scraper"
)

# Config registry - maps service type names to config objects
CONFIGS = {
    "llm": LLM_CONFIG,
    "database": DATABASE_CONFIG,
    "api": API_CONFIG,
    "scraper": SCRAPER_CONFIG
}


def get_config(service_type: str = "api") -> HTTPClientConfig:
    """Get predefined configuration for a service type.

    Args:
        service_type: Type of service (llm, database, api, scraper)

    Returns:
        HTTPClientConfig object for the specified service type

    Raises:
        ValueError: If service_type is not recognized
    """
    if service_type not in CONFIGS:
        raise ValueError(
            f"Unknown service type: {service_type}. "
            f"Valid types: {', '.join(CONFIGS.keys())}"
        )
    return CONFIGS[service_type]
