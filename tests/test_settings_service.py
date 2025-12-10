"""
Unit tests for Settings Service

Tests:
- Environment variable fallback
- Database cache loading
- Type conversion (bool, int, float)
- Cache expiration and reload
- Setting values programmatically
"""

import os
import pytest
from datetime import timedelta
from agent_factory.core.settings_service import SettingsService


class TestSettingsServiceEnvironmentFallback:
    """Test that settings fall back to environment variables"""

    def test_get_from_environment(self):
        """Should get value from environment variable when DB not available"""
        os.environ["TEST_SETTING"] = "from_env"

        # Create service without Supabase credentials
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get("TEST_SETTING")
        assert value == "from_env"

        # Cleanup
        del os.environ["TEST_SETTING"]

    def test_get_with_default(self):
        """Should return default when setting not found"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get("NONEXISTENT_SETTING", default="default_value")
        assert value == "default_value"

    def test_get_bool_from_environment(self):
        """Should parse boolean from environment variable"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        # Test truthy values
        for truthy in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            os.environ["BOOL_TEST"] = truthy
            assert service.get_bool("BOOL_TEST") is True
            del os.environ["BOOL_TEST"]

        # Test falsy values
        for falsy in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF", "anything"]:
            os.environ["BOOL_TEST"] = falsy
            assert service.get_bool("BOOL_TEST") is False
            del os.environ["BOOL_TEST"]

    def test_get_int_from_environment(self):
        """Should parse integer from environment variable"""
        os.environ["INT_TEST"] = "42"

        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_int("INT_TEST")
        assert value == 42
        assert isinstance(value, int)

        del os.environ["INT_TEST"]

    def test_get_int_with_invalid_value(self):
        """Should return default when environment value is not a valid integer"""
        os.environ["INT_TEST"] = "not_a_number"

        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_int("INT_TEST", default=99)
        assert value == 99

        del os.environ["INT_TEST"]

    def test_get_float_from_environment(self):
        """Should parse float from environment variable"""
        os.environ["FLOAT_TEST"] = "3.14159"

        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_float("FLOAT_TEST")
        assert value == 3.14159
        assert isinstance(value, float)

        del os.environ["FLOAT_TEST"]

    def test_get_float_with_invalid_value(self):
        """Should return default when environment value is not a valid float"""
        os.environ["FLOAT_TEST"] = "not_a_float"

        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_float("FLOAT_TEST", default=1.5)
        assert value == 1.5

        del os.environ["FLOAT_TEST"]


class TestSettingsServiceCategories:
    """Test category-based setting organization"""

    def test_get_with_category(self):
        """Should support category namespacing"""
        os.environ["DEFAULT_MODEL"] = "gpt-4"

        service = SettingsService(supabase_url=None, supabase_key=None)

        # Environment fallback doesn't use category, but API should accept it
        value = service.get("DEFAULT_MODEL", category="llm")
        assert value == "gpt-4"

        del os.environ["DEFAULT_MODEL"]

    def test_get_bool_with_category(self):
        """Should support category with boolean settings"""
        os.environ["USE_HYBRID_SEARCH"] = "true"

        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_bool("USE_HYBRID_SEARCH", category="memory")
        assert value is True

        del os.environ["USE_HYBRID_SEARCH"]

    def test_get_int_with_category(self):
        """Should support category with integer settings"""
        os.environ["BATCH_SIZE"] = "100"

        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_int("BATCH_SIZE", category="memory")
        assert value == 100

        del os.environ["BATCH_SIZE"]


class TestSettingsServiceDefaults:
    """Test default value handling"""

    def test_bool_default_false(self):
        """Should return False by default when setting not found"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_bool("NONEXISTENT_BOOL")
        assert value is False

    def test_bool_default_true(self):
        """Should return True when default=True"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_bool("NONEXISTENT_BOOL", default=True)
        assert value is True

    def test_int_default_zero(self):
        """Should return 0 by default when setting not found"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_int("NONEXISTENT_INT")
        assert value == 0

    def test_int_custom_default(self):
        """Should return custom default when setting not found"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_int("NONEXISTENT_INT", default=42)
        assert value == 42

    def test_float_default_zero(self):
        """Should return 0.0 by default when setting not found"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_float("NONEXISTENT_FLOAT")
        assert value == 0.0

    def test_float_custom_default(self):
        """Should return custom default when setting not found"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        value = service.get_float("NONEXISTENT_FLOAT", default=3.14)
        assert value == 3.14


class TestSettingsServiceRepr:
    """Test string representation"""

    def test_repr_without_database(self):
        """Should show environment-only status when no database"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        repr_str = repr(service)
        assert "environment-only" in repr_str
        assert "cached_settings=0" in repr_str

    def test_repr_format(self):
        """Should have correct format"""
        service = SettingsService(supabase_url=None, supabase_key=None)

        repr_str = repr(service)
        assert repr_str.startswith("<SettingsService")
        assert repr_str.endswith(">")


# Integration tests (require Supabase connection)
class TestSettingsServiceWithDatabase:
    """
    Integration tests that require Supabase connection.

    Skip these if SUPABASE_URL or SUPABASE_KEY not available.
    """

    @pytest.fixture
    def service_with_db(self):
        """Fixture that creates service with database connection"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            pytest.skip("Supabase credentials not available")

        return SettingsService(supabase_url=url, supabase_key=key)

    def test_cache_initialization(self, service_with_db):
        """Should load cache from database on initialization"""
        # This test requires actual database connection
        # Will be skipped if credentials not available
        assert service_with_db.client is not None

    def test_get_from_cache(self, service_with_db):
        """Should get value from cache after initialization"""
        # Assumes DEFAULT_MODEL exists in database
        value = service_with_db.get("DEFAULT_MODEL", category="llm")
        assert value is not None

    def test_reload(self, service_with_db):
        """Should reload cache from database"""
        service_with_db.reload()
        # Should not raise exception

    def test_get_all(self, service_with_db):
        """Should get all settings"""
        all_settings = service_with_db.get_all()
        assert isinstance(all_settings, dict)

    def test_get_all_by_category(self, service_with_db):
        """Should get settings filtered by category"""
        llm_settings = service_with_db.get_all(category="llm")
        assert isinstance(llm_settings, dict)


# Test the singleton instance
class TestSettingsSingleton:
    """Test the global settings singleton"""

    def test_singleton_import(self):
        """Should be able to import the singleton instance"""
        from agent_factory.core.settings_service import settings

        assert settings is not None
        assert isinstance(settings, SettingsService)

    def test_singleton_usage(self):
        """Should be able to use the singleton"""
        from agent_factory.core.settings_service import settings

        # Should not raise exception
        value = settings.get("TEST", default="default")
        assert value == "default"


if __name__ == "__main__":
    # Run tests with: poetry run pytest tests/test_settings_service.py -v
    pytest.main([__file__, "-v"])
