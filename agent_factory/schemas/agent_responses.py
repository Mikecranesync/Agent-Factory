"""
Specialized response schemas for different agent types.

PURPOSE:
    Provides domain-specific response schemas that extend AgentResponse base class.
    Like specialized PLC UDTs for different machine types - each adds relevant fields.

WHAT THIS PROVIDES:
    - ResearchResponse: For search/research agents (sources, confidence, queries)
    - CodeResponse: For coding agents (code, language, dependencies, tests)
    - CreativeResponse: For writing agents (genre, style, word_count)
    - AnalysisResponse: For analysis agents (scores, insights, recommendations)

WHY WE NEED THIS:
    - Type safety: Each agent type has validated structure
    - Domain-specific: Fields relevant to agent's task
    - Inheritance: Reuses AgentResponse (success, output, metadata)
    - Extensibility: Easy to add new specialized responses

PLC ANALOGY:
    Like specialized PLC UDTs for different equipment:
    - ResearchResponse = Search system UDT (results, sources, confidence)
    - CodeResponse = Compiler output UDT (code, language, errors, warnings)
    - CreativeResponse = Text generator UDT (content, style, length)
    - AnalysisResponse = Quality check UDT (scores, faults, recommendations)
"""

from typing import List, Optional
from pydantic import Field

from .base import AgentResponse


class ResearchResponse(AgentResponse):
    """
    Response from research/search agents.

    PURPOSE:
        Research agent responses with sources, confidence, and search queries.
        Like PLC search system UDT - tracks what was found, where, and how confident.

    WHAT THIS ADDS:
        - sources: List of sources consulted (URLs, documents, databases)
        - confidence: Confidence score (0.0-1.0) in the answer accuracy
        - search_queries: Queries used to find the information

    WHY WE NEED THIS:
        - Transparency: User knows where answer came from
        - Trust: Confidence score helps assess reliability
        - Debugging: See what queries were used
        - Audit: Trail of sources for verification

    PLC ANALOGY:
        Like PLC search/retrieval system UDT:
        - sources = Data source IDs (database tables, sensors polled)
        - confidence = Data quality score (0-100%)
        - search_queries = Search parameters used
        - output = Search result data

    Example:
        >>> response = ResearchResponse(
        ...     success=True,
        ...     output="Paris is the capital of France",
        ...     sources=["Wikipedia: France", "Britannica: Paris"],
        ...     confidence=0.98,
        ...     search_queries=["capital of France"]
        ... )
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

    PURPOSE:
        Coding agent responses with code, language, dependencies, and tests.
        Like PLC compiler output UDT - code generated, language, errors, warnings.

    WHAT THIS ADDS:
        - code: The generated or analyzed code
        - language: Programming language (python, javascript, etc.)
        - explanation: Human-readable explanation
        - dependencies: Required libraries/packages
        - test_code: Optional test cases

    PLC ANALOGY:
        Like PLC compiler output UDT:
        - code = Generated ladder logic/ST code
        - language = PLC language (ladder, ST, FBD)
        - explanation = Code comments/documentation
        - dependencies = Required function blocks/libraries
        - test_code = Test scenarios for validation
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

    PURPOSE:
        Creative writing responses with genre, style, and word count metadata.
        Like PLC text generation system UDT - tracks content type, style, length.

    WHAT THIS ADDS:
        - genre: Content type (poem, story, essay, etc.)
        - style: Writing tone (formal, casual, humorous, etc.)
        - word_count: Number of words generated
        - prompt_used: Original prompt

    PLC ANALOGY:
        Like PLC text/label generation UDT:
        - genre = Output format (alarm text, report, log entry)
        - style = Message severity (info, warning, critical)
        - word_count = Message length (characters)
        - prompt_used = Template used
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

    PURPOSE:
        Analysis agent responses with scores, insights, and recommendations.
        Like PLC quality check system UDT - scores, faults found, corrective actions.

    WHAT THIS ADDS:
        - scores: Numerical metrics (e.g., {"quality": 8.5, "clarity": 9.0})
        - insights: Key findings or observations
        - recommendations: Suggested actions/improvements
        - analysis_type: Type of analysis (sentiment, code_review, etc.)

    PLC ANALOGY:
        Like PLC quality control system UDT:
        - scores = Measurement values (dimensions, tolerances)
        - insights = Defects detected (out of spec, warnings)
        - recommendations = Corrective actions (adjust machine, replace tool)
        - analysis_type = Inspection type (visual, dimensional, functional)
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
