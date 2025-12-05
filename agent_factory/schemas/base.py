"""
Base schemas for agent responses.

Provides foundational Pydantic models for type-safe agent outputs.
All agent-specific response types inherit from AgentResponse.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """
    Base class for all agent responses.

    Provides consistent structure across all agent types with:
    - Success/failure status
    - Primary output content
    - Extensible metadata
    - Timestamp for tracking

    All specialized agent responses (ResearchResponse, CodeResponse, etc.)
    should inherit from this class.

    Attributes:
        success: Whether the agent successfully completed the task
        output: Primary response content (answer, result, error message)
        metadata: Additional context, sources, confidence scores, etc.
        timestamp: When the response was generated
        agent_name: Optional name of the agent that generated this response

    Example:
        >>> response = AgentResponse(
        ...     success=True,
        ...     output="The capital of France is Paris",
        ...     metadata={"confidence": 0.95}
        ... )
        >>> print(response.output)
        The capital of France is Paris
    """

    success: bool = Field(
        description="Whether the agent successfully completed the task"
    )
    output: str = Field(
        description="Primary response content"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context and information"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this response was generated"
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Name of the agent that generated this response"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "output": "Task completed successfully",
                "metadata": {"duration_ms": 150.5},
                "timestamp": "2025-12-05T10:30:00",
                "agent_name": "research_agent"
            }
        }


class ErrorResponse(AgentResponse):
    """
    Response for failed operations.

    Extends AgentResponse with error-specific fields to provide
    detailed information about failures.

    Attributes:
        error_type: Category of error (validation, timeout, llm_error, etc.)
        error_details: Detailed error message or stack trace
        retry_possible: Whether retrying the operation might succeed

    Example:
        >>> error = ErrorResponse(
        ...     success=False,
        ...     output="Failed to process request",
        ...     error_type="timeout",
        ...     error_details="LLM request timed out after 30s",
        ...     retry_possible=True
        ... )
    """

    error_type: str = Field(
        description="Category of error (validation, timeout, llm_error, etc.)"
    )
    error_details: Optional[str] = Field(
        default=None,
        description="Detailed error message or stack trace"
    )
    retry_possible: bool = Field(
        default=False,
        description="Whether retrying the operation might succeed"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": False,
                "output": "Request failed",
                "error_type": "timeout",
                "error_details": "Operation exceeded 30 second limit",
                "retry_possible": True,
                "metadata": {},
                "timestamp": "2025-12-05T10:30:00"
            }
        }


class ToolResponse(BaseModel):
    """
    Response from individual tool execution.

    Used to standardize outputs from tools before they're incorporated
    into agent responses.

    Attributes:
        tool_name: Name of the tool that executed
        success: Whether the tool executed successfully
        result: Tool output or result
        error: Error message if execution failed
        execution_time_ms: How long the tool took to execute

    Example:
        >>> tool_result = ToolResponse(
        ...     tool_name="web_search",
        ...     success=True,
        ...     result="Found 10 results for 'Python tutorial'",
        ...     execution_time_ms=245.8
        ... )
    """

    tool_name: str = Field(
        description="Name of the tool that executed"
    )
    success: bool = Field(
        description="Whether the tool executed successfully"
    )
    result: Any = Field(
        description="Tool output or result"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="How long the tool took to execute"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "tool_name": "calculator",
                "success": True,
                "result": 42,
                "error": None,
                "execution_time_ms": 1.2
            }
        }
