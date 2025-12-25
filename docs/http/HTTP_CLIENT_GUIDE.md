# HTTP Client Guide

## Overview

Agent Factory uses a centralized, resilient HTTP client layer for all external API calls.

**Features:**
- Automatic retry with exponential backoff
- Configurable timeouts (connect, read, total)
- Redirect handling with loop detection
- Rate limit detection (HTTP 429)
- Structured error objects for triage
- LangSmith tracing integration
- Connection pooling

---

## Quick Start

### Basic Usage
```python
from agent_factory.http import get_client, CONFIGS

# Use default "api" config
client = get_client()
response = client.get("https://api.example.com/data")

if response.ok:
    print(response.data)
else:
    print(f"Error: {response.error.summary}")
```

### Service-Specific Configs
```python
# For LLM APIs (longer timeouts)
llm_client = get_client(CONFIGS["llm"])

# For database/Ollama (shorter timeouts)
db_client = get_client(CONFIGS["database"])

# For web scraping (longest timeouts)
scraper_client = get_client(CONFIGS["scraper"])
```

---

## Configuration

### Predefined Configs

| Config | Use Case | Connect Timeout | Read Timeout | Retry Attempts |
|--------|----------|----------------|--------------|----------------|
| `llm` | LLM APIs (Claude, GPT) | 5s | 60s | 3 |
| `database` | PostgreSQL, Ollama | 2s | 5s | 2 |
| `api` | General APIs | 5s | 10s | 3 |
| `scraper` | Web scraping, PDFs | 10s | 30s | 3 |

### Custom Configuration
```python
from agent_factory.http import HTTPClient, HTTPClientConfig, TimeoutConfig, RetryConfig

config = HTTPClientConfig(
    timeout=TimeoutConfig(
        connect=5.0,  # Seconds to establish connection
        read=10.0,    # Seconds to read response
        total=30.0    # Max wall-clock time including retries
    ),
    retry=RetryConfig(
        max_attempts=3,        # Number of retry attempts
        initial_wait=0.5,      # Initial backoff delay (seconds)
        max_wait=10.0,         # Maximum backoff delay (seconds)
        exponential_base=2.0,  # Backoff multiplier
        jitter=True            # Add randomness to backoff
    )
)

client = HTTPClient(config)
```

---

## Error Handling

### Structured Error Objects

All errors produce a structured `HTTPError` object:
```python
@dataclass
class HTTPError:
    category: str           # Error type (timeout, rate_limited, etc.)
    http_status: int        # HTTP status code (if any)
    url: str                # Sanitized URL (secrets removed)
    method: str             # HTTP method (GET, POST, etc.)
    request_id: str         # Request ID from headers (if available)
    summary: str            # Human-readable summary
    raw_error: Exception    # Original exception
    retry_after: int        # Seconds to wait (for rate limiting)
```

### Error Categories

| Category | Retryable | HTTP Status | Description |
|----------|-----------|-------------|-------------|
| `timeout` | ✅ Yes | None | Connect or read timeout |
| `connection_error` | ✅ Yes | None | Network/DNS failure |
| `rate_limited` | ✅ Yes | 429 | HTTP 429 Too Many Requests |
| `server_error` | ✅ Yes | 5xx | HTTP 500-599 errors |
| `client_error` | ❌ No | 4xx | HTTP 400-499 errors (except 429) |
| `too_many_redirects` | ❌ No | None | Redirect loop detected |
| `deserialization_error` | ❌ No | 2xx | Response parsing failed |

### Example Error Handling
```python
response = client.post(url, json=data)

if not response.ok:
    error = response.error

    # Log to triage system
    logger.error(f"API call failed: {error.summary}", extra={
        "error_category": error.category,
        "http_status": error.http_status,
        "url": error.url
    })

    # Handle specific errors
    if error.category == "rate_limited":
        print(f"Rate limited. Retry after {error.retry_after}s")
    elif error.category == "timeout":
        print("Request timed out after retries")
    elif error.category == "client_error":
        print(f"Bad request: {error.http_status}")
```

---

## Retry Logic

### Automatic Retry

The HTTP client automatically retries for:
- `timeout` - Connect or read timeout
- `connection_error` - Network failures
- `server_error` - HTTP 5xx
- `rate_limited` - HTTP 429

It does NOT retry for:
- `client_error` - HTTP 4xx (except 429)
- `deserialization_error` - Response parsing failed
- `too_many_redirects` - Redirect loop

### Exponential Backoff

Retry delays increase exponentially with optional jitter:

| Attempt | Delay (No Jitter) | Delay (With Jitter) |
|---------|------------------|---------------------|
| 1 | 0.5s | 0.3s - 0.7s |
| 2 | 1.0s | 0.7s - 1.3s |
| 3 | 2.0s | 1.5s - 2.5s |

**Why Jitter?** Prevents thundering herd when many clients retry simultaneously.

### Disable Retry

For specific requests where retry is not desired:
```python
response = client.get(url, retry=False)
```

---

## Redirects

### Configuration
```python
from agent_factory.http import RedirectConfig

config = HTTPClientConfig(
    redirect=RedirectConfig(
        follow=True,        # Follow redirects
        max_redirects=5     # Maximum redirect hops
    )
)
```

### Redirect Loop Detection

If a request redirects more than `max_redirects` times, the client raises `TooManyRedirectsError`:
```python
response = client.get(url)

if response.error and response.error.category == "too_many_redirects":
    print(f"Redirect loop detected (max: 5 hops)")
```

---

## Logging and Tracing

### LangSmith Integration

All HTTP operations are automatically traced with LangSmith (if configured):

```bash
# .env
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Graceful Degradation:** If LangSmith is not configured, tracing is silently disabled (HTTP client works normally).

### Structured Logs

All requests log structured fields:
- `http_method` - GET, POST, etc.
- `http_url` - Sanitized URL (secrets removed)
- `http_status` - HTTP status code
- `http_duration_ms` - Request duration
- `http_error_category` - Error type (if failed)
- `http_retry_attempt` - Retry count (if retried)

Example:
```python
logger.info("HTTP GET https://api.example.com/data?... (523ms)", extra={
    "http_method": "GET",
    "http_url": "https://api.example.com/data?...",
    "http_status": 200,
    "http_duration_ms": 523.4
})
```

---

## Rate Limiting

### HTTP 429 Detection

The client automatically detects HTTP 429 responses and:
1. Parses `Retry-After` header
2. Includes retry delay in error object
3. Automatically retries with exponential backoff

```python
response = client.get(url)

if response.error and response.error.category == "rate_limited":
    retry_after = response.error.retry_after or 60
    print(f"Rate limited. Retry after {retry_after}s")
```

### Retry-After Header Parsing

Supports two formats:
- **Seconds:** `Retry-After: 60`
- **Unix Timestamp:** `X-RateLimit-Reset: 1704067200`

---

## Advanced Usage

### Custom Timeouts

Override timeout per request:
```python
# Single timeout value (applies to both connect and read)
response = client.get(url, timeout=30.0)

# Separate connect and read timeouts
response = client.get(url, timeout=(5.0, 30.0))
```

### Headers and Parameters
```python
# Custom headers
response = client.get(url, headers={"Authorization": "Bearer token123"})

# Query parameters
response = client.get(url, params={"page": 1, "limit": 50})

# JSON body
response = client.post(url, json={"key": "value"})
```

### Global Client vs Per-Request Client
```python
# Global client (singleton, reuses connection pool)
from agent_factory.http import get_client

client = get_client()
response = client.get(url)

# Per-request client (new instance each time)
from agent_factory.http import get

response = get(url)
```

---

## Migration Guide

### Before (Direct requests)
```python
import requests

response = requests.get(url, timeout=10)
response.raise_for_status()
data = response.json()
```

### After (Resilient client)
```python
from agent_factory.http import get_client

client = get_client()
response = client.get(url)

if response.ok:
    data = response.data
else:
    logger.error(f"Request failed: {response.error.summary}")
```

### Benefits
- Automatic retry on transient failures
- Structured error logging
- Rate limit detection
- Connection pooling
- LangSmith tracing

---

## Best Practices

1. **Use service-specific configs** - Choose the right timeout/retry profile for your use case
2. **Handle errors explicitly** - Don't assume `response.ok == True`
3. **Log structured errors** - Include `error.category` and `error.http_status` in logs
4. **Respect rate limits** - Check `error.retry_after` for 429 responses
5. **Sanitize URLs in logs** - Client automatically removes query params with secrets
6. **Use connection pooling** - Reuse the same client instance across requests

---

## Troubleshooting

### Request Times Out
```python
# Increase timeout
client = get_client(CONFIGS["scraper"])  # 30s read timeout

# Or override per request
response = client.get(url, timeout=60.0)
```

### Too Many Redirects
```python
# Increase redirect limit
config = HTTPClientConfig(
    redirect=RedirectConfig(max_redirects=10)
)
client = HTTPClient(config)
```

### Rate Limited
```python
# Check retry_after value
if response.error.category == "rate_limited":
    retry_after = response.error.retry_after or 60
    time.sleep(retry_after)
```

### JSON Parsing Fails
```python
# Check content type
if response.ok:
    if "application/json" in response.raw.headers.get("content-type", ""):
        data = response.data  # Parsed JSON
    else:
        text = response.data  # Plain text
```

---

## Examples

### VPS KB Client (Ollama)
```python
from agent_factory.http import HTTPClient, CONFIGS

class VPSKBClient:
    def __init__(self):
        # Use API config (5s connect, 10s read)
        self.http_client = HTTPClient(CONFIGS["api"])

    def _get_embedding(self, query: str):
        response = self.http_client.post(
            f"{self.ollama_url}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": query}
        )

        if not response.ok:
            logger.error(f"Ollama failed: {response.error.summary}")
            return []

        return response.data.get("embedding", [])
```

### GitHub Actions Integration
```python
from agent_factory.http import HTTPClient, CONFIGS

class GitHubActions:
    def __init__(self):
        self.http_client = HTTPClient(CONFIGS["api"])

    async def _trigger_workflow(self, workflow: str):
        response = self.http_client.post(
            url,
            json=data,
            headers={"Authorization": f"token {self.token}"}
        )

        if not response.ok:
            logger.error(f"GitHub API failed: {response.error.summary}")
            return None

        return await self._get_latest_run_id()
```

### Content Ingestion (Web Scraping)
```python
from agent_factory.http import HTTPClient, CONFIGS

# Use scraper config (10s connect, 30s read)
http_client = HTTPClient(CONFIGS["scraper"])

def _download_pdf(url: str):
    response = http_client.get(url)

    if not response.ok:
        logger.error(f"PDF download failed: {response.error.summary}")
        return ""

    # Save PDF
    with open(output_path, 'wb') as f:
        f.write(response.raw.content)
```

---

## API Reference

### HTTPClient

```python
class HTTPClient:
    def __init__(self, config: Optional[HTTPClientConfig] = None)

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
    ) -> HTTPResponse

    def get(self, url: str, **kwargs) -> HTTPResponse
    def post(self, url: str, **kwargs) -> HTTPResponse
    def put(self, url: str, **kwargs) -> HTTPResponse
    def delete(self, url: str, **kwargs) -> HTTPResponse
    def patch(self, url: str, **kwargs) -> HTTPResponse
```

### HTTPResponse

```python
@dataclass
class HTTPResponse:
    ok: bool                        # True if successful, False if error
    status_code: int                # HTTP status code
    data: Optional[Any]             # Parsed JSON or text
    headers: Dict[str, str]         # Response headers
    raw: Optional[requests.Response] # Original response object
    error: Optional[HTTPError]      # Error details (if failed)
```

### HTTPError

```python
@dataclass
class HTTPError:
    category: str           # Error type (timeout, rate_limited, etc.)
    http_status: Optional[int]  # HTTP status code (if any)
    url: str                # Sanitized URL (secrets removed)
    method: str             # HTTP method (GET, POST, etc.)
    request_id: Optional[str]   # Request ID from headers
    summary: str            # Human-readable summary
    raw_error: Optional[Exception]  # Original exception
    retry_after: Optional[int]  # Seconds to wait (for rate limiting)
```

---

## Testing

### Unit Tests

```python
from agent_factory.http import HTTPClient
from unittest.mock import patch, Mock

def test_successful_request():
    client = HTTPClient()

    with patch.object(client.session, 'request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

        response = client.get("https://api.example.com/test")

        assert response.ok
        assert response.data == {"status": "ok"}
```

### Integration Tests

See `tests/http/test_integration.py` for examples of testing migrated components.

---

## Performance

### Connection Pooling

The HTTP client uses `requests.Session` for connection pooling:
- Reuses TCP connections
- Reduces handshake overhead
- Improves throughput for multiple requests

### Latency Overhead

HTTP client adds minimal overhead:
- **Retry logic:** <10ms per request
- **Error handling:** <1ms per request
- **LangSmith tracing:** <5ms per request (if enabled)

99.9% of request time is API call time, not client overhead.

---

## Security

### URL Sanitization

The client automatically removes query parameters from URLs before logging:
```python
# Original URL
url = "https://api.example.com/data?token=secret123&key=abc"

# Logged URL (secrets removed)
logged_url = "https://api.example.com/data?..."
```

### Credential Handling

Never include credentials in query parameters. Use headers instead:
```python
# ❌ Bad (credentials in URL)
response = client.get("https://api.example.com/data?token=secret123")

# ✅ Good (credentials in headers)
response = client.get("https://api.example.com/data", headers={"Authorization": "Bearer secret123"})
```

---

## Support

For issues or questions:
1. Check this guide first
2. Review `tests/http/test_client.py` for examples
3. Check `agent_factory/http/client.py` source code
4. Ask in #agent-factory Slack channel

---

**Last Updated:** 2025-12-23
