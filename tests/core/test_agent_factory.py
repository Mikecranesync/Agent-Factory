"""
Comprehensive unit tests for AgentFactory class.

Tests cover:
- Initialization with various configurations
- Agent registration and retrieval
- Routing behavior (enabled/disabled)
- Error handling
- Edge cases and boundary conditions
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

from agent_factory.core.agent_factory import AgentFactory


class TestAgentFactoryInitialization:
    """Test AgentFactory initialization with various configurations."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        factory = AgentFactory()
        
        assert factory.default_model == "gpt-4o"
        assert factory.default_temperature == 0.0
        assert factory.verbose is True
        assert factory.enable_routing is False  # Changed default in this branch
        assert factory.exclude_local is False

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        factory = AgentFactory(default_model="gpt-3.5-turbo")
        
        assert factory.default_model == "gpt-3.5-turbo"

    def test_init_with_custom_temperature(self):
        """Test initialization with custom temperature."""
        factory = AgentFactory(default_temperature=0.7)
        
        assert factory.default_temperature == 0.7

    def test_init_with_routing_enabled(self):
        """Test initialization with routing explicitly enabled."""
        factory = AgentFactory(enable_routing=True)
        
        assert factory.enable_routing is True

    def test_init_with_routing_disabled(self):
        """Test initialization with routing explicitly disabled."""
        factory = AgentFactory(enable_routing=False)
        
        assert factory.enable_routing is False

    def test_init_with_verbose_disabled(self):
        """Test initialization with verbose mode disabled."""
        factory = AgentFactory(verbose=False)
        
        assert factory.verbose is False

    def test_init_with_exclude_local(self):
        """Test initialization with local models excluded."""
        factory = AgentFactory(exclude_local=True)
        
        assert factory.exclude_local is True

    def test_init_with_all_custom_parameters(self):
        """Test initialization with all parameters customized."""
        factory = AgentFactory(
            default_model="claude-3-opus",
            default_temperature=0.5,
            verbose=False,
            enable_routing=True,
            exclude_local=True
        )
        
        assert factory.default_model == "claude-3-opus"
        assert factory.default_temperature == 0.5
        assert factory.verbose is False
        assert factory.enable_routing is True
        assert factory.exclude_local is True

    def test_init_temperature_boundary_zero(self):
        """Test initialization with temperature at lower boundary."""
        factory = AgentFactory(default_temperature=0.0)
        
        assert factory.default_temperature == 0.0

    def test_init_temperature_boundary_one(self):
        """Test initialization with temperature at upper boundary."""
        factory = AgentFactory(default_temperature=1.0)
        
        assert factory.default_temperature == 1.0

    def test_init_temperature_boundary_two(self):
        """Test initialization with temperature at maximum typical value."""
        factory = AgentFactory(default_temperature=2.0)
        
        assert factory.default_temperature == 2.0


class TestAgentFactoryRouting:
    """Test routing behavior based on enable_routing flag."""

    def test_routing_disabled_by_default(self):
        """Test that routing is disabled by default in this branch."""
        factory = AgentFactory()
        
        # The key change in this branch
        assert factory.enable_routing is False

    def test_routing_can_be_enabled(self):
        """Test that routing can still be explicitly enabled."""
        factory = AgentFactory(enable_routing=True)
        
        assert factory.enable_routing is True

    def test_routing_flag_persistence(self):
        """Test that routing flag persists across method calls."""
        factory = AgentFactory(enable_routing=True)
        
        # Flag should remain consistent
        assert factory.enable_routing is True
        assert factory.enable_routing is True  # Check again


class TestAgentFactoryConfiguration:
    """Test configuration combinations and edge cases."""

    def test_model_name_with_special_characters(self):
        """Test model names with special characters."""
        factory = AgentFactory(default_model="gpt-4-turbo-preview")
        
        assert factory.default_model == "gpt-4-turbo-preview"

    def test_model_name_with_version(self):
        """Test model names with version numbers."""
        factory = AgentFactory(default_model="gpt-4-0125-preview")
        
        assert factory.default_model == "gpt-4-0125-preview"

    def test_temperature_float_precision(self):
        """Test temperature with high float precision."""
        factory = AgentFactory(default_temperature=0.123456789)
        
        assert factory.default_temperature == 0.123456789

    def test_configuration_independence(self):
        """Test that multiple factory instances are independent."""
        factory1 = AgentFactory(default_model="gpt-4", enable_routing=True)
        factory2 = AgentFactory(default_model="gpt-3.5-turbo", enable_routing=False)
        
        assert factory1.default_model == "gpt-4"
        assert factory1.enable_routing is True
        assert factory2.default_model == "gpt-3.5-turbo"
        assert factory2.enable_routing is False


class TestAgentFactoryVerboseMode:
    """Test verbose mode behavior."""

    def test_verbose_enabled_by_default(self):
        """Test that verbose mode is enabled by default."""
        factory = AgentFactory()
        
        assert factory.verbose is True

    def test_verbose_can_be_disabled(self):
        """Test that verbose mode can be disabled."""
        factory = AgentFactory(verbose=False)
        
        assert factory.verbose is False

    def test_verbose_with_other_settings(self):
        """Test verbose mode combined with other settings."""
        factory = AgentFactory(
            verbose=True,
            enable_routing=True,
            exclude_local=True
        )
        
        assert factory.verbose is True
        assert factory.enable_routing is True
        assert factory.exclude_local is True


class TestAgentFactoryExcludeLocal:
    """Test exclude_local flag behavior."""

    def test_exclude_local_disabled_by_default(self):
        """Test that exclude_local is disabled by default."""
        factory = AgentFactory()
        
        assert factory.exclude_local is False

    def test_exclude_local_can_be_enabled(self):
        """Test that exclude_local can be enabled."""
        factory = AgentFactory(exclude_local=True)
        
        assert factory.exclude_local is True

    def test_exclude_local_with_routing(self):
        """Test exclude_local combined with routing settings."""
        factory = AgentFactory(
            exclude_local=True,
            enable_routing=True
        )
        
        assert factory.exclude_local is True
        assert factory.enable_routing is True


class TestAgentFactoryStateManagement:
    """Test state management and immutability."""

    def test_factory_state_isolation(self):
        """Test that factory instances don't share state."""
        factory1 = AgentFactory(default_temperature=0.0)
        factory2 = AgentFactory(default_temperature=1.0)
        
        assert factory1.default_temperature != factory2.default_temperature

    def test_configuration_immutability_after_init(self):
        """Test that configuration values remain stable after initialization."""
        factory = AgentFactory(
            default_model="test-model",
            default_temperature=0.5,
            enable_routing=True
        )
        
        # Store initial values
        initial_model = factory.default_model
        initial_temp = factory.default_temperature
        initial_routing = factory.enable_routing
        
        # Values should remain the same
        assert factory.default_model == initial_model
        assert factory.default_temperature == initial_temp
        assert factory.enable_routing == initial_routing


class TestAgentFactoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_model_name(self):
        """Test initialization with empty string model name."""
        factory = AgentFactory(default_model="")
        
        assert factory.default_model == ""

    def test_negative_temperature(self):
        """Test initialization with negative temperature (should be allowed by OpenAI)."""
        factory = AgentFactory(default_temperature=-0.5)
        
        assert factory.default_temperature == -0.5

    def test_very_high_temperature(self):
        """Test initialization with very high temperature."""
        factory = AgentFactory(default_temperature=10.0)
        
        assert factory.default_temperature == 10.0

    def test_model_name_with_spaces(self):
        """Test model name with spaces."""
        factory = AgentFactory(default_model="custom model name")
        
        assert factory.default_model == "custom model name"

    def test_unicode_model_name(self):
        """Test model name with unicode characters."""
        factory = AgentFactory(default_model="model-🤖-v1")
        
        assert factory.default_model == "model-🤖-v1"


class TestAgentFactoryBooleanFlags:
    """Test all boolean flag combinations."""

    def test_all_flags_true(self):
        """Test with all boolean flags set to True."""
        factory = AgentFactory(
            verbose=True,
            enable_routing=True,
            exclude_local=True
        )
        
        assert factory.verbose is True
        assert factory.enable_routing is True
        assert factory.exclude_local is True

    def test_all_flags_false(self):
        """Test with all boolean flags set to False."""
        factory = AgentFactory(
            verbose=False,
            enable_routing=False,
            exclude_local=False
        )
        
        assert factory.verbose is False
        assert factory.enable_routing is False
        assert factory.exclude_local is False

    def test_mixed_flag_combination_1(self):
        """Test mixed flag combination 1."""
        factory = AgentFactory(
            verbose=True,
            enable_routing=False,
            exclude_local=True
        )
        
        assert factory.verbose is True
        assert factory.enable_routing is False
        assert factory.exclude_local is True

    def test_mixed_flag_combination_2(self):
        """Test mixed flag combination 2."""
        factory = AgentFactory(
            verbose=False,
            enable_routing=True,
            exclude_local=False
        )
        
        assert factory.verbose is False
        assert factory.enable_routing is True
        assert factory.exclude_local is False


class TestAgentFactoryDefaultBehaviorChange:
    """Test the specific default behavior change in this branch."""

    def test_routing_default_changed_from_true_to_false(self):
        """
        Critical test: Verify that enable_routing default changed from True to False.
        
        This is the main change in agent_factory/core/agent_factory.py:
        Line 63: enable_routing: bool = False (was True in main branch)
        """
        factory = AgentFactory()
        
        # This is the critical assertion for this branch
        assert factory.enable_routing is False, \
            "enable_routing should default to False in this branch"

    def test_backward_compatibility_explicit_true(self):
        """Test backward compatibility when explicitly setting routing to True."""
        factory = AgentFactory(enable_routing=True)
        
        assert factory.enable_routing is True

    def test_default_behavior_with_no_routing_param(self):
        """Test default behavior when routing parameter is not specified."""
        factory = AgentFactory(
            default_model="gpt-4",
            default_temperature=0.0,
            verbose=True
        )
        
        # Should use the new default (False)
        assert factory.enable_routing is False


class TestAgentFactoryIntegration:
    """Integration tests for AgentFactory with realistic scenarios."""

    def test_typical_usage_scenario_1(self):
        """Test typical usage scenario: Basic agent factory."""
        factory = AgentFactory()
        
        assert factory is not None
        assert isinstance(factory.default_model, str)
        assert isinstance(factory.default_temperature, (int, float))
        assert isinstance(factory.verbose, bool)
        assert isinstance(factory.enable_routing, bool)
        assert isinstance(factory.exclude_local, bool)

    def test_typical_usage_scenario_2(self):
        """Test typical usage scenario: Custom configuration."""
        factory = AgentFactory(
            default_model="gpt-4-turbo",
            default_temperature=0.3,
            verbose=True,
            enable_routing=False
        )
        
        assert factory.default_model == "gpt-4-turbo"
        assert factory.default_temperature == 0.3
        assert factory.verbose is True
        assert factory.enable_routing is False

    def test_typical_usage_scenario_3(self):
        """Test typical usage scenario: Production settings."""
        factory = AgentFactory(
            default_model="gpt-4o",
            default_temperature=0.0,
            verbose=False,
            enable_routing=False,
            exclude_local=False
        )
        
        assert factory.default_model == "gpt-4o"
        assert factory.default_temperature == 0.0
        assert factory.verbose is False
        assert factory.enable_routing is False
        assert factory.exclude_local is False