"""
Base schemas for agent responses.

PURPOSE:
    Provides foundational Pydantic models for type-safe, validated agent outputs.
    Like PLC data structure templates - ensures consistent format across all agent responses.

WHAT THIS PROVIDES:
    1. AgentResponse: Base class for all agent responses (success, output, metadata)
    2. ErrorResponse: Specialized response for failures (error_type, retry_possible)
    3. ToolResponse: Standardized tool execution results (tool_name, result, timing)

WHY WE NEED THIS:
    - Type safety: Pydantic validates data at runtime (catch bugs early)
    - Consistency: All agents return same structure (easy to parse)
    - Extensibility: Specialized responses inherit from base (DRY principle)
    - Serialization: Auto-converts to JSON for APIs

PLC ANALOGY:
    Like PLC UDT (User-Defined Type) library:
    - AgentResponse = Generic result UDT (status, value, metadata)
    - ErrorResponse = Fault alarm UDT (alarm type, details, retry)
    - ToolResponse = Function block output UDT (FB name, result, timing)
    - All responses use same base structure (consistent HMI display)
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """
    Base class for all agent responses.

    PURPOSE:
        Provides consistent, type-safe structure for all agent responses.
        Like a PLC standard result UDT - every agent returns same format.

    WHAT THIS CONTAINS:
        - success: Boolean flag (True = completed, False = failed)
        - output: Primary response content (answer, result, error message)
        - metadata: Extensible dict for additional info (confidence, sources, cost, etc.)
        - timestamp: When response generated (datetime, auto-filled)
        - agent_name: Optional identifier of which agent created this

    WHY WE NEED THIS:
        - Consistency: All agents return same structure (easy to parse)
        - Type safety: Pydantic validates at runtime (catch errors early)
        - Inheritance: Specialized responses extend this (ResearchResponse, CodeResponse)
        - Serialization: Auto-converts to JSON for APIs and storage

    VALIDATION:
        Pydantic automatically validates:
        - success must be bool (not string "true")
        - output must be string (not None)
        - metadata must be dict (not list)
        - timestamp must be datetime (not string)

    PLC ANALOGY:
        Like a PLC standard result UDT:
        - success = Done bit (TRUE/FALSE)
        - output = Result value/message
        - metadata = Diagnostic data (cycle time, error codes, etc.)
        - timestamp = PLC real-time clock stamp
        - agent_name = Station ID

    INHERITANCE:
        All specialized agent responses should inherit from this:
        - ResearchResponse(AgentResponse): Adds citations, sources
        - CodeResponse(AgentResponse): Adds files_changed, tests_passed
        - CalendarResponse(AgentResponse): Adds events list

    Examples:
        >>> response = AgentResponse(
        ...     success=True,
        ...     output="The capital of France is Paris",
        ...     metadata={"confidence": 0.95}
        ... )
        >>> print(response.output)
        The capital of France is Paris
        >>> print(response.success)
        True
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

    PURPOSE:
        Specialized response for failures with structured error information.
        Like a PLC fault alarm UDT - provides error type, details, and recovery guidance.

    WHAT THIS ADDS (beyond AgentResponse):
        - error_type: Category of error (validation, timeout, llm_error, tool_error, etc.)
        - error_details: Detailed error message or stack trace (for debugging)
        - retry_possible: Boolean indicating if retrying might succeed

    WHY WE NEED THIS:
        - Structured errors: Categorize failures for better handling
        - Retry logic: Know when to retry vs give up
        - Debugging: Detailed information for troubleshooting
        - Monitoring: Track error patterns and frequencies

    ERROR TYPES (common):
        - "validation": Invalid input parameters
        - "timeout": Operation exceeded time limit
        - "llm_error": LLM API failure
        - "tool_error": Tool execution failure
        - "rate_limit": API rate limit exceeded
        - "auth_error": Authentication/authorization failure

    RETRY GUIDANCE:
        - retry_possible=True: Transient error (timeout, rate limit)
        - retry_possible=False: Permanent error (validation, auth)

    PLC ANALOGY:
        Like a PLC fault alarm UDT:
        - error_type = Fault category (overload, timeout, comm error)
        - error_details = Fault description text
        - retry_possible = Auto-reset vs manual-reset fault
        - success=False = Fault bit set
        - output = Fault message shown on HMI

    VALIDATION:
        Inherits AgentResponse validation, plus:
        - error_type must be non-empty string
        - retry_possible must be bool

    Examples:
        >>> error = ErrorResponse(
        ...     success=False,
        ...     output="Failed to process request",
        ...     error_type="timeout",
        ...     error_details="LLM request timed out after 30s",
        ...     retry_possible=True
        ... )
        >>> print(error.error_type)
        timeout
        >>> if error.retry_possible:
        ...     print("Retry recommended")
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

    PURPOSE:
        Standardizes outputs from tools before incorporation into agent responses.
        Like a PLC function block output UDT - consistent structure for all tool results.

    WHAT THIS CONTAINS:
        - tool_name: Identifier of which tool executed (e.g., "web_search", "calculator")
        - success: Whether tool executed without errors (True/False)
        - result: Tool output (can be any type - string, dict, list, number)
        - error: Optional error message if execution failed
        - execution_time_ms: Optional timing information (milliseconds)

    WHY WE NEED THIS:
        - Standardization: All tools return same format (easy to parse)
        - Debugging: Track which tools succeeded/failed
        - Performance: Measure tool execution times
        - Composition: Multiple tool responses compose into agent response

    TYPICAL USAGE:
        1. Agent invokes tool
        2. Tool wraps output in ToolResponse
        3. Agent aggregates ToolResponses into AgentResponse.metadata
        4. Enables tracking which tools were called and their results

    PLC ANALOGY:
        Like a PLC function block output UDT:
        - tool_name = Function block name (e.g., "TON", "CTU", "MOVE")
        - success = Done bit / Error bit
        - result = Output value/result
        - error = Error status text
        - execution_time_ms = Scan time for this FB

    VALIDATION:
        Pydantic validates:
        - tool_name must be non-empty string
        - success must be bool
        - result can be any type (Any)
        - error can be None or string
        - execution_time_ms can be None or positive float

    EDGE CASES:
        - success=True, error=None: Normal success
        - success=False, error="...": Tool failed with error message
        - success=True, error="warning": Tool succeeded with warning
        - result=None: Valid if tool has no output (e.g., file write)

    Examples:
        >>> # Successful tool execution
        >>> tool_result = ToolResponse(
        ...     tool_name="web_search",
        ...     success=True,
        ...     result="Found 10 results for 'Python tutorial'",
        ...     execution_time_ms=245.8
        ... )

        >>> # Failed tool execution
        >>> tool_error = ToolResponse(
        ...     tool_name="calculator",
        ...     success=False,
        ...     result=None,
        ...     error="Division by zero",
        ...     execution_time_ms=1.2
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
