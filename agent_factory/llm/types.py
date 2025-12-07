"""
LLM Types - Pydantic Models for Multi-Provider LLM Abstraction

This module provides standardized data structures for working with multiple
LLM providers through a unified interface. Supports cost tracking, usage
monitoring, and provider-agnostic responses.

Part of Phase 1: LLM Abstraction Layer
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    """
    Supported LLM providers.

    Each provider requires corresponding API keys in environment:
    - OPENAI: OPENAI_API_KEY
    - ANTHROPIC: ANTHROPIC_API_KEY
    - GOOGLE: GOOGLE_API_KEY
    - OLLAMA: No key required (local)
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class ModelCapability(str, Enum):
    """Model capability categories for routing decisions (Phase 2)"""
    SIMPLE = "simple"          # Basic queries, low complexity
    MODERATE = "moderate"      # Standard reasoning tasks
    COMPLEX = "complex"        # Advanced reasoning, research
    CODING = "coding"          # Code generation and analysis
    RESEARCH = "research"      # Multi-step research workflows


class ModelInfo(BaseModel):
    """
    Metadata about an LLM model.

    Used for cost calculation and routing decisions.
    Prices are in USD per 1,000 tokens.
    """
    provider: LLMProvider
    model_name: str
    input_cost_per_1k: float = Field(
        ...,
        description="Cost per 1K input tokens in USD",
        ge=0.0
    )
    output_cost_per_1k: float = Field(
        ...,
        description="Cost per 1K output tokens in USD",
        ge=0.0
    )
    context_window: int = Field(
        ...,
        description="Maximum context window size in tokens",
        gt=0
    )
    capability: ModelCapability = ModelCapability.MODERATE
    supports_streaming: bool = True
    supports_function_calling: bool = False

    class Config:
        use_enum_values = True


class UsageStats(BaseModel):
    """
    Token usage and cost tracking for LLM calls.

    Automatically calculated from provider responses.
    Enables budget monitoring and cost optimization.
    """
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    input_cost_usd: float = Field(default=0.0, ge=0.0)
    output_cost_usd: float = Field(default=0.0, ge=0.0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)

    def calculate_costs(self, model_info: ModelInfo) -> None:
        """
        Calculate costs based on token usage and model pricing.

        Args:
            model_info: Model metadata with pricing information
        """
        self.total_tokens = self.input_tokens + self.output_tokens
        self.input_cost_usd = (self.input_tokens / 1000) * model_info.input_cost_per_1k
        self.output_cost_usd = (self.output_tokens / 1000) * model_info.output_cost_per_1k
        self.total_cost_usd = self.input_cost_usd + self.output_cost_usd


class LLMResponse(BaseModel):
    """
    Standardized response from any LLM provider.

    Provides unified interface regardless of underlying provider.
    Includes cost tracking and performance metrics.
    """
    content: str = Field(..., description="Generated text content")
    provider: LLMProvider = Field(..., description="LLM provider used")
    model: str = Field(..., description="Specific model name")
    usage: UsageStats = Field(default_factory=UsageStats)
    latency_ms: float = Field(..., description="Response time in milliseconds", ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    finish_reason: Optional[str] = Field(
        None,
        description="Why generation stopped (stop, length, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific metadata"
    )

    class Config:
        use_enum_values = True


class LLMConfig(BaseModel):
    """
    Configuration for LLM requests.

    Used to specify model, parameters, and behavior for each request.
    Supports all common parameters across providers.
    """
    provider: LLMProvider
    model: str
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0)"
    )
    max_tokens: Optional[int] = Field(
        None,
        gt=0,
        description="Maximum tokens to generate"
    )
    top_p: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold"
    )
    timeout: int = Field(
        default=120,
        gt=0,
        description="Request timeout in seconds"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming responses"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional configuration options"
    )

    class Config:
        use_enum_values = True


class RouteDecision(BaseModel):
    """
    Record of routing decision for transparency (Phase 2).

    Tracks which model was selected and why, enabling
    debugging and optimization of routing strategies.
    """
    selected_provider: LLMProvider
    selected_model: str
    reason: str = Field(..., description="Why this model was chosen")
    alternatives_considered: List[str] = Field(
        default_factory=list,
        description="Other models that were considered"
    )
    estimated_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated cost for this request"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
