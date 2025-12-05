"""
Agent Factory Schemas Package

Type-safe, validated response schemas for agent outputs.

This package provides Pydantic models for structured agent responses,
enabling:
- Type safety with IDE autocomplete
- Automatic validation of agent outputs
- Consistent response structure across agent types
- Easy serialization to JSON/dict

Usage:
    from agent_factory.schemas import AgentResponse, ResearchResponse, CodeResponse

    # Create a typed response
    response = ResearchResponse(
        success=True,
        output="Paris is the capital of France",
        sources=["Wikipedia"],
        confidence=0.95
    )

    # Access fields with type safety
    print(response.output)  # IDE knows this is a string
    print(response.sources)  # IDE knows this is List[str]

Available Schemas:
    Base:
        - AgentResponse: Base class for all responses
        - ErrorResponse: For failed operations
        - ToolResponse: For tool execution results

    Specialized:
        - ResearchResponse: Research/search agents
        - CodeResponse: Coding/programming agents
        - CreativeResponse: Creative writing agents
        - AnalysisResponse: Analysis/evaluation agents
"""

# Base schemas
from .base import (
    AgentResponse,
    ErrorResponse,
    ToolResponse,
)

# Specialized agent responses
from .agent_responses import (
    ResearchResponse,
    CodeResponse,
    CreativeResponse,
    AnalysisResponse,
)

__all__ = [
    # Base
    "AgentResponse",
    "ErrorResponse",
    "ToolResponse",
    # Specialized
    "ResearchResponse",
    "CodeResponse",
    "CreativeResponse",
    "AnalysisResponse",
]
