"""
Unit Tests for HTTP Client Layer

Tests cover:
- Successful requests
- Timeout with retry
- Rate limiting (HTTP 429)
- Client errors (HTTP 4xx) - no retry
- Server errors (HTTP 5xx) - with retry
- Too many redirects
- Connection errors
- Deserialization errors
- Configuration handling
- Error categorization
"""

import pytest
from unittest.mock import Mock, patch
import requests
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError, TooManyRedirects

from agent_factory.http import (
    HTTPClient,
    HTTPResponse,
    HTTPClientConfig,
    TimeoutConfig,
    RetryConfig,
    RedirectConfig,
    CONFIGS
)
from agent_factory.http.errors import (
    TimeoutError,
    ConnectionError,
    RateLimitError,
    ServerError,
    ClientError,
    TooManyRedirectsError,
    DeserializationError,
    HTTPError
)


class TestSuccessfulRequests:
    """Test successful HTTP requests"""

    def test_successful_get_request(self):
        """Test successful GET request returns proper response"""
        client = HTTPClient()

        # Mock the session.request method
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = {"status": "ok"}
            mock_request.return_value = mock_response

            response = client.get("https://api.example.com/test")

            assert response.ok
            assert response.status_code == 200
            assert response.data == {"status": "ok"}
            assert response.error is None

    def test_successful_post_request(self):
        """Test successful POST request with JSON body"""
        client = HTTPClient()

        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = {"created": True, "id": 123}
            mock_request.return_value = mock_response

            response = client.post("https://api.example.com/create", json={"name": "test"})

            assert response.ok
            assert response.status_code == 201
            assert response.data == {"created": True, "id": 123}


class TestTimeoutHandling:
    """Test timeout handling with retry"""

    def test_timeout_triggers_retry(self):
        """Test that timeout errors trigger automatic retry"""
        config = HTTPClientConfig(
            timeout=TimeoutConfig(connect=1.0, read=2.0),
            retry=RetryConfig(max_attempts=3, initial_wait=0.1)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            # Simulate timeout on all attempts
            mock_request.side_effect = Timeout("Connection timed out")

            response = client.get("https://api.example.com/slow")

            # Should have tried 3 times
            assert mock_request.call_count == 3
            assert not response.ok
            assert response.error.category == "timeout"
            assert "timeout" in response.error.summary.lower()

    def test_timeout_then_success(self):
        """Test that retry succeeds after transient timeout"""
        config = HTTPClientConfig(
            retry=RetryConfig(max_attempts=3, initial_wait=0.1)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            # First 2 attempts timeout, 3rd succeeds
            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.headers = {'content-type': 'application/json'}
            mock_success.json.return_value = {"status": "ok"}

            mock_request.side_effect = [
                Timeout("Timeout 1"),
                Timeout("Timeout 2"),
                mock_success
            ]

            response = client.get("https://api.example.com/flaky")

            assert response.ok
            assert response.status_code == 200
            assert mock_request.call_count == 3


class TestRateLimiting:
    """Test HTTP 429 rate limit handling"""

    def test_rate_limit_triggers_retry(self):
        """Test that 429 responses trigger retry with backoff"""
        config = HTTPClientConfig(
            retry=RetryConfig(max_attempts=3, initial_wait=0.1)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            # Simulate rate limiting
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.headers = {'Retry-After': '1', 'X-Request-ID': 'test-123'}
            mock_request.return_value = mock_429

            response = client.get("https://api.example.com/limited")

            # Should retry 3 times
            assert mock_request.call_count == 3
            assert not response.ok
            assert response.error.category == "rate_limited"
            assert response.error.http_status == 429

    def test_rate_limit_with_retry_after_header(self):
        """Test parsing of Retry-After header"""
        client = HTTPClient()

        with patch.object(client.session, 'request') as mock_request:
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.headers = {'Retry-After': '60'}
            mock_request.return_value = mock_429

            response = client.get("https://api.example.com/limited")

            assert not response.ok
            assert response.error.retry_after == 60


class TestClientErrors:
    """Test HTTP 4xx client errors (should NOT retry)"""

    def test_client_error_no_retry(self):
        """Test that 4xx errors do NOT trigger retry"""
        client = HTTPClient()

        with patch.object(client.session, 'request') as mock_request:
            mock_400 = Mock()
            mock_400.status_code = 400
            mock_400.headers = {}
            mock_request.return_value = mock_400

            response = client.get("https://api.example.com/bad-request")

            # Should only try once (no retry for 4xx)
            assert mock_request.call_count == 1
            assert not response.ok
            assert response.error.category == "client_error"
            assert response.error.http_status == 400

    def test_404_not_found(self):
        """Test 404 Not Found error"""
        client = HTTPClient()

        with patch.object(client.session, 'request') as mock_request:
            mock_404 = Mock()
            mock_404.status_code = 404
            mock_404.headers = {}
            mock_request.return_value = mock_404

            response = client.get("https://api.example.com/missing")

            assert not response.ok
            assert response.error.category == "client_error"
            assert response.error.http_status == 404


class TestServerErrors:
    """Test HTTP 5xx server errors (should retry)"""

    def test_server_error_triggers_retry(self):
        """Test that 5xx errors trigger automatic retry"""
        config = HTTPClientConfig(
            retry=RetryConfig(max_attempts=3, initial_wait=0.1)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            mock_500 = Mock()
            mock_500.status_code = 500
            mock_500.headers = {}
            mock_request.return_value = mock_500

            response = client.get("https://api.example.com/error")

            # Should retry 3 times
            assert mock_request.call_count == 3
            assert not response.ok
            assert response.error.category == "server_error"
            assert response.error.http_status == 500

    def test_server_error_then_success(self):
        """Test successful retry after transient 5xx error"""
        config = HTTPClientConfig(
            retry=RetryConfig(max_attempts=3, initial_wait=0.1)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            # First 2 attempts fail with 503, 3rd succeeds
            mock_503 = Mock()
            mock_503.status_code = 503
            mock_503.headers = {}

            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.headers = {'content-type': 'application/json'}
            mock_success.json.return_value = {"status": "ok"}

            mock_request.side_effect = [mock_503, mock_503, mock_success]

            response = client.get("https://api.example.com/flaky")

            assert response.ok
            assert response.status_code == 200
            assert mock_request.call_count == 3


class TestConnectionErrors:
    """Test network connection errors"""

    def test_connection_error_triggers_retry(self):
        """Test that connection errors trigger retry"""
        config = HTTPClientConfig(
            retry=RetryConfig(max_attempts=3, initial_wait=0.1)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            mock_request.side_effect = RequestsConnectionError("Network unreachable")

            response = client.get("https://api.example.com/unreachable")

            assert mock_request.call_count == 3
            assert not response.ok
            assert response.error.category == "connection_error"
            assert "connection failed" in response.error.summary.lower()


class TestRedirects:
    """Test redirect handling"""

    def test_too_many_redirects(self):
        """Test that redirect loops are detected"""
        config = HTTPClientConfig(
            redirect=RedirectConfig(follow=True, max_redirects=5)
        )
        client = HTTPClient(config)

        with patch.object(client.session, 'request') as mock_request:
            mock_request.side_effect = TooManyRedirects("Too many redirects")

            response = client.get("https://api.example.com/redirect-loop")

            assert not response.ok
            assert response.error.category == "too_many_redirects"


class TestDeserialization:
    """Test response parsing and deserialization"""

    def test_json_parsing_success(self):
        """Test successful JSON parsing"""
        client = HTTPClient()

        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = {"key": "value"}
            mock_request.return_value = mock_response

            response = client.get("https://api.example.com/data")

            assert response.ok
            assert response.data == {"key": "value"}

    def test_text_response(self):
        """Test plain text response handling"""
        client = HTTPClient()

        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'text/plain'}
            mock_response.text = "Plain text response"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_request.return_value = mock_response

            response = client.get("https://api.example.com/text")

            assert response.ok
            assert response.data == "Plain text response"


class TestConfiguration:
    """Test configuration handling"""

    def test_default_config(self):
        """Test client uses default API config"""
        client = HTTPClient()

        assert client.config.timeout.connect == 5.0
        assert client.config.timeout.read == 10.0
        assert client.config.retry.max_attempts == 3

    def test_custom_config(self):
        """Test client accepts custom config"""
        config = HTTPClientConfig(
            timeout=TimeoutConfig(connect=2.0, read=5.0),
            retry=RetryConfig(max_attempts=5, initial_wait=1.0)
        )
        client = HTTPClient(config)

        assert client.config.timeout.connect == 2.0
        assert client.config.timeout.read == 5.0
        assert client.config.retry.max_attempts == 5

    def test_predefined_configs(self):
        """Test all predefined configs are available"""
        assert "llm" in CONFIGS
        assert "database" in CONFIGS
        assert "api" in CONFIGS
        assert "scraper" in CONFIGS

        # Verify LLM config has longer timeouts
        assert CONFIGS["llm"].timeout.read == 60.0

        # Verify database config has shorter timeouts
        assert CONFIGS["database"].timeout.read == 5.0


class TestConvenienceMethods:
    """Test convenience methods (get, post, put, delete, patch)"""

    def test_post_method(self):
        """Test POST convenience method"""
        client = HTTPClient()

        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = HTTPResponse(
                ok=True,
                status_code=201,
                data={"created": True},
                headers={},
                raw=None
            )

            response = client.post("https://api.example.com/create", json={"name": "test"})

            mock_request.assert_called_once()
            assert response.status_code == 201

    def test_put_method(self):
        """Test PUT convenience method"""
        client = HTTPClient()

        with patch.object(client, 'request') as mock_request:
            mock_request.return_value = HTTPResponse(
                ok=True,
                status_code=200,
                data={"updated": True},
                headers={},
                raw=None
            )

            response = client.put("https://api.example.com/update/123", json={"name": "updated"})

            assert response.status_code == 200


class TestURLSanitization:
    """Test URL sanitization for logging"""

    def test_url_sanitization(self):
        """Test query params are removed from URLs for safe logging"""
        from agent_factory.http.client import HTTPClient as RawHTTPClient

        # Test sanitization
        url_with_secret = "https://api.example.com/data?token=secret123&key=abc"
        sanitized = RawHTTPClient._sanitize_url(url_with_secret)

        assert "token=secret123" not in sanitized
        assert "key=abc" not in sanitized
        assert "https://api.example.com/data?" in sanitized

    def test_url_without_params(self):
        """Test URLs without query params remain unchanged"""
        from agent_factory.http.client import HTTPClient as RawHTTPClient

        url = "https://api.example.com/data"
        sanitized = RawHTTPClient._sanitize_url(url)

        assert sanitized == url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
