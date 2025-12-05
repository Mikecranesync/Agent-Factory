"""
Tests for agent_factory.schemas module

Tests schema creation, validation, and integration with AgentFactory.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from pydantic import ValidationError

from agent_factory.schemas import (
    AgentResponse,
    ErrorResponse,
    ToolResponse,
    ResearchResponse,
    CodeResponse,
    CreativeResponse,
    AnalysisResponse,
)


class TestAgentResponse:
    """Test base AgentResponse schema."""

    def test_agent_response_creation(self):
        """REQ-SCHEMA-001: Create basic AgentResponse."""
        response = AgentResponse(
            success=True,
            output="Test response"
        )

        assert response.success is True
        assert response.output == "Test response"
        assert isinstance(response.metadata, dict)
        assert isinstance(response.timestamp, datetime)
        assert response.agent_name is None

    def test_agent_response_with_metadata(self):
        """REQ-SCHEMA-002: AgentResponse with metadata."""
        metadata = {"source": "test", "duration_ms": 150.5}
        response = AgentResponse(
            success=True,
            output="Test",
            metadata=metadata,
            agent_name="test_agent"
        )

        assert response.metadata == metadata
        assert response.agent_name == "test_agent"

    def test_agent_response_defaults(self):
        """REQ-SCHEMA-003: Default values work correctly."""
        response = AgentResponse(
            success=True,
            output="Test"
        )

        # Defaults should be set
        assert response.metadata == {}
        assert response.timestamp is not None
        assert response.agent_name is None


class TestErrorResponse:
    """Test ErrorResponse schema."""

    def test_error_response_creation(self):
        """REQ-SCHEMA-004: Create ErrorResponse."""
        error = ErrorResponse(
            success=False,
            output="Operation failed",
            error_type="timeout",
            error_details="Request timed out after 30s",
            retry_possible=True
        )

        assert error.success is False
        assert error.error_type == "timeout"
        assert error.error_details == "Request timed out after 30s"
        assert error.retry_possible is True

    def test_error_response_defaults(self):
        """REQ-SCHEMA-005: ErrorResponse defaults."""
        error = ErrorResponse(
            success=False,
            output="Failed",
            error_type="unknown"
        )

        assert error.error_details is None
        assert error.retry_possible is False


class TestToolResponse:
    """Test ToolResponse schema."""

    def test_tool_response_success(self):
        """REQ-SCHEMA-006: Successful tool response."""
        tool_response = ToolResponse(
            tool_name="calculator",
            success=True,
            result=42,
            execution_time_ms=1.5
        )

        assert tool_response.tool_name == "calculator"
        assert tool_response.success is True
        assert tool_response.result == 42
        assert tool_response.execution_time_ms == 1.5
        assert tool_response.error is None

    def test_tool_response_failure(self):
        """REQ-SCHEMA-007: Failed tool response."""
        tool_response = ToolResponse(
            tool_name="web_search",
            success=False,
            result=None,
            error="Network timeout"
        )

        assert tool_response.success is False
        assert tool_response.error == "Network timeout"


class TestResearchResponse:
    """Test ResearchResponse schema."""

    def test_research_response_creation(self):
        """REQ-SCHEMA-008: Create ResearchResponse."""
        response = ResearchResponse(
            success=True,
            output="Paris is the capital of France",
            sources=["Wikipedia", "Britannica"],
            confidence=0.95,
            search_queries=["capital of France"]
        )

        assert response.output == "Paris is the capital of France"
        assert len(response.sources) == 2
        assert response.confidence == 0.95
        assert response.search_queries == ["capital of France"]

    def test_research_response_confidence_validation(self):
        """REQ-SCHEMA-009: Confidence must be between 0.0 and 1.0."""
        # Valid confidence
        valid = ResearchResponse(
            success=True,
            output="Test",
            confidence=0.5
        )
        assert valid.confidence == 0.5

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            ResearchResponse(
                success=True,
                output="Test",
                confidence=1.5
            )

        # Invalid confidence (negative)
        with pytest.raises(ValidationError):
            ResearchResponse(
                success=True,
                output="Test",
                confidence=-0.5
            )

    def test_research_response_defaults(self):
        """REQ-SCHEMA-010: ResearchResponse defaults."""
        response = ResearchResponse(
            success=True,
            output="Test"
        )

        assert response.sources == []
        assert response.confidence == 0.0
        assert response.search_queries == []


class TestCodeResponse:
    """Test CodeResponse schema."""

    def test_code_response_creation(self):
        """REQ-SCHEMA-011: Create CodeResponse."""
        response = CodeResponse(
            success=True,
            output="Function to check prime numbers",
            code="def is_prime(n):\n    return n > 1",
            language="python",
            explanation="Checks if number is prime",
            dependencies=["math"],
            test_code="assert is_prime(7)"
        )

        assert response.code == "def is_prime(n):\n    return n > 1"
        assert response.language == "python"
        assert response.explanation == "Checks if number is prime"
        assert response.dependencies == ["math"]
        assert response.test_code == "assert is_prime(7)"

    def test_code_response_defaults(self):
        """REQ-SCHEMA-012: CodeResponse defaults."""
        response = CodeResponse(
            success=True,
            output="Test"
        )

        assert response.code == ""
        assert response.language == ""
        assert response.explanation == ""
        assert response.dependencies == []
        assert response.test_code is None


class TestCreativeResponse:
    """Test CreativeResponse schema."""

    def test_creative_response_creation(self):
        """REQ-SCHEMA-013: Create CreativeResponse."""
        response = CreativeResponse(
            success=True,
            output="Roses are red, violets are blue",
            genre="poem",
            style="humorous",
            word_count=8,
            prompt_used="Write a funny poem"
        )

        assert response.genre == "poem"
        assert response.style == "humorous"
        assert response.word_count == 8
        assert response.prompt_used == "Write a funny poem"

    def test_creative_response_word_count_validation(self):
        """REQ-SCHEMA-014: Word count must be non-negative."""
        # Valid word count
        valid = CreativeResponse(
            success=True,
            output="Test",
            word_count=10
        )
        assert valid.word_count == 10

        # Invalid word count (negative)
        with pytest.raises(ValidationError):
            CreativeResponse(
                success=True,
                output="Test",
                word_count=-5
            )


class TestAnalysisResponse:
    """Test AnalysisResponse schema."""

    def test_analysis_response_creation(self):
        """REQ-SCHEMA-015: Create AnalysisResponse."""
        response = AnalysisResponse(
            success=True,
            output="Code quality is good",
            scores={"quality": 8.5, "maintainability": 7.0},
            insights=["Good error handling", "Missing type hints"],
            recommendations=["Add type hints", "Increase test coverage"],
            analysis_type="code_review"
        )

        assert response.scores == {"quality": 8.5, "maintainability": 7.0}
        assert len(response.insights) == 2
        assert len(response.recommendations) == 2
        assert response.analysis_type == "code_review"

    def test_analysis_response_defaults(self):
        """REQ-SCHEMA-016: AnalysisResponse defaults."""
        response = AnalysisResponse(
            success=True,
            output="Test"
        )

        assert response.scores == {}
        assert response.insights == []
        assert response.recommendations == []
        assert response.analysis_type == ""


class TestSchemaInheritance:
    """Test that all specialized schemas inherit from AgentResponse."""

    def test_research_response_is_agent_response(self):
        """REQ-SCHEMA-017: ResearchResponse inherits from AgentResponse."""
        response = ResearchResponse(success=True, output="Test")
        assert isinstance(response, AgentResponse)

    def test_code_response_is_agent_response(self):
        """REQ-SCHEMA-018: CodeResponse inherits from AgentResponse."""
        response = CodeResponse(success=True, output="Test")
        assert isinstance(response, AgentResponse)

    def test_creative_response_is_agent_response(self):
        """REQ-SCHEMA-019: CreativeResponse inherits from AgentResponse."""
        response = CreativeResponse(success=True, output="Test")
        assert isinstance(response, AgentResponse)

    def test_analysis_response_is_agent_response(self):
        """REQ-SCHEMA-020: AnalysisResponse inherits from AgentResponse."""
        response = AnalysisResponse(success=True, output="Test")
        assert isinstance(response, AgentResponse)

    def test_error_response_is_agent_response(self):
        """REQ-SCHEMA-021: ErrorResponse inherits from AgentResponse."""
        response = ErrorResponse(success=False, output="Error", error_type="test")
        assert isinstance(response, AgentResponse)


class TestSchemaSerialization:
    """Test schema serialization to dict/JSON."""

    def test_agent_response_to_dict(self):
        """REQ-SCHEMA-022: AgentResponse can serialize to dict."""
        response = AgentResponse(
            success=True,
            output="Test output",
            metadata={"key": "value"}
        )

        data = response.model_dump()

        assert data["success"] is True
        assert data["output"] == "Test output"
        assert data["metadata"] == {"key": "value"}
        assert "timestamp" in data

    def test_research_response_to_dict(self):
        """REQ-SCHEMA-023: ResearchResponse serializes with all fields."""
        response = ResearchResponse(
            success=True,
            output="Test",
            sources=["Source1"],
            confidence=0.9
        )

        data = response.model_dump()

        assert data["sources"] == ["Source1"]
        assert data["confidence"] == 0.9
