"""
Unit tests for telegram integration __init__.py module.

Tests the removal of ScaffoldHandlers and NLTaskParser from exports.
"""

import pytest


class TestTelegramIntegrationImports:
    """Test telegram integration module imports."""

    def test_telegram_bot_importable(self):
        """Test TelegramBot can be imported."""
        from agent_factory.integrations.telegram import TelegramBot
        assert TelegramBot is not None

    def test_telegram_config_importable(self):
        """Test TelegramConfig can be imported."""
        from agent_factory.integrations.telegram import TelegramConfig
        assert TelegramConfig is not None

    def test_session_manager_importable(self):
        """Test TelegramSessionManager can be imported."""
        from agent_factory.integrations.telegram import TelegramSessionManager
        assert TelegramSessionManager is not None

    def test_response_formatter_importable(self):
        """Test ResponseFormatter can be imported."""
        from agent_factory.integrations.telegram import ResponseFormatter
        assert ResponseFormatter is not None

    def test_all_contains_only_valid_exports(self):
        """Test __all__ contains only expected exports."""
        from agent_factory.integrations.telegram import __all__
        
        expected_exports = {
            'TelegramBot',
            'TelegramConfig',
            'TelegramSessionManager',
            'ResponseFormatter'
        }
        
        assert set(__all__) == expected_exports


class TestRemovedExports:
    """Test that removed exports are no longer available."""

    def test_scaffold_handlers_not_in_all(self):
        """Test ScaffoldHandlers not in __all__."""
        from agent_factory.integrations import telegram
        
        assert 'ScaffoldHandlers' not in telegram.__all__

    def test_nl_task_parser_not_in_all(self):
        """Test NLTaskParser not in __all__."""
        from agent_factory.integrations import telegram
        
        assert 'NLTaskParser' not in telegram.__all__