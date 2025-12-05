"""
Specialized response schemas for different agent types.

Each schema extends AgentResponse with domain-specific fields
to provide type-safe, validated responses for different agent roles.
"""

from typing import List, Optional
from pydantic import Field

from .base import AgentResponse


class ResearchResponse(AgentResponse):
    """
    Response from research/search agents.

    Extends AgentResponse with research-specific fields like
    sources and confidence scores.

    Attributes:
        sources: List of sources consulted (URLs, documents, etc.)
        confidence: Confidence score (0.0-1.0) in the answer
        search_queries: Queries used to find the information

    Example:
        >>> response = ResearchResponse(
        ...     success=True,
        ...     output="Paris is the capital of France",
        ...     sources=["Wikipedia: France", "Britannica: Paris"],
        ...     confidence=0.98
        ... )
        >>> for source in response.sources:
        ...     print(f"Source: {source}")
    """

    sources: List[str] = Field(
        default_factory=list,
        description="Sources consulted (URLs, documents, references)"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in the answer (0.0-1.0)"
    )
    search_queries: List[str] = Field(
        default_factory=list,
        description="Search queries used to find information"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "output": "The Eiffel Tower was completed in 1889",
                "sources": [
                    "https://en.wikipedia.org/wiki/Eiffel_Tower",
                    "Official Eiffel Tower website"
                ],
                "confidence": 0.95,
                "search_queries": ["when was eiffel tower built"],
                "metadata": {"search_duration_ms": 523},
                "timestamp": "2025-12-05T10:30:00"
            }
        }


class CodeResponse(AgentResponse):
    """
    Response from coding/programming agents.

    Extends AgentResponse with code-specific fields like
    code snippets, language, and explanations.

    Attributes:
        code: The generated or analyzed code
        language: Programming language (python, javascript, etc.)
        explanation: Human-readable explanation of the code
        dependencies: Required libraries or packages
        test_code: Optional test cases for the code

    Example:
        >>> response = CodeResponse(
        ...     success=True,
        ...     output="Function to calculate factorial",
        ...     code="def factorial(n):\\n    return 1 if n <= 1 else n * factorial(n-1)",
        ...     language="python",
        ...     explanation="Recursive implementation of factorial"
        ... )
        >>> print(response.code)
    """

    code: str = Field(
        default="",
        description="The generated or analyzed code"
    )
    language: str = Field(
        default="",
        description="Programming language (python, javascript, etc.)"
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation of the code"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Required libraries or packages"
    )
    test_code: Optional[str] = Field(
        default=None,
        description="Optional test cases for the code"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "output": "Here's a function to check prime numbers",
                "code": "def is_prime(n):\\n    if n < 2: return False\\n    for i in range(2, int(n**0.5)+1):\\n        if n % i == 0: return False\\n    return True",
                "language": "python",
                "explanation": "Checks if a number is prime using trial division",
                "dependencies": [],
                "test_code": "assert is_prime(7) == True",
                "metadata": {},
                "timestamp": "2025-12-05T10:30:00"
            }
        }


class CreativeResponse(AgentResponse):
    """
    Response from creative writing agents.

    Extends AgentResponse with creative content fields like
    genre, style, and word count.

    Attributes:
        genre: Type of creative content (poem, story, essay, etc.)
        style: Writing style or tone (formal, casual, humorous, etc.)
        word_count: Number of words in the output
        prompt_used: The creative prompt that generated this content

    Example:
        >>> response = CreativeResponse(
        ...     success=True,
        ...     output="Roses are red, violets are blue...",
        ...     genre="poem",
        ...     style="humorous",
        ...     word_count=12
        ... )
    """

    genre: str = Field(
        default="",
        description="Type of creative content (poem, story, essay, etc.)"
    )
    style: str = Field(
        default="",
        description="Writing style or tone (formal, casual, humorous, etc.)"
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Number of words in the output"
    )
    prompt_used: Optional[str] = Field(
        default=None,
        description="The creative prompt that generated this content"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "output": "In circuits deep where data flows,\\nA coder types in endless rows...",
                "genre": "poem",
                "style": "whimsical",
                "word_count": 24,
                "prompt_used": "Write a poem about coding",
                "metadata": {"generation_time_ms": 1200},
                "timestamp": "2025-12-05T10:30:00"
            }
        }


class AnalysisResponse(AgentResponse):
    """
    Response from analysis/evaluation agents.

    Extends AgentResponse with analytical fields like
    scores, insights, and recommendations.

    Attributes:
        scores: Numerical scores or metrics (e.g., {"quality": 8.5, "clarity": 9.0})
        insights: Key findings or observations
        recommendations: Suggested actions or improvements
        analysis_type: Type of analysis performed (sentiment, code_review, etc.)

    Example:
        >>> response = AnalysisResponse(
        ...     success=True,
        ...     output="Code quality is good overall",
        ...     scores={"quality": 8.5, "maintainability": 7.0},
        ...     insights=["Good error handling", "Missing type hints"],
        ...     recommendations=["Add type hints", "Increase test coverage"]
        ... )
    """

    scores: dict[str, float] = Field(
        default_factory=dict,
        description="Numerical scores or metrics"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Key findings or observations"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggested actions or improvements"
    )
    analysis_type: str = Field(
        default="",
        description="Type of analysis performed (sentiment, code_review, etc.)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "output": "Overall positive sentiment detected",
                "scores": {"positive": 0.85, "neutral": 0.10, "negative": 0.05},
                "insights": [
                    "Strong positive language in opening",
                    "Minor concerns mentioned in middle"
                ],
                "recommendations": [
                    "Address concerns in follow-up",
                    "Maintain positive tone"
                ],
                "analysis_type": "sentiment",
                "metadata": {},
                "timestamp": "2025-12-05T10:30:00"
            }
        }
