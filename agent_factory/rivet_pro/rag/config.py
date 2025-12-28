"""
RAG Configuration for RIVET Pro

Defines collection names, metadata schemas, and coverage thresholds for KB queries.

Phase 2/8 of RIVET Pro Multi-Agent Backend.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# ============================================================================
# Collection Names
# ============================================================================

# Supabase table name for knowledge atoms
COLLECTION_NAME = "knowledge_atoms"

# ============================================================================
# Search Configuration
# ============================================================================

# Default number of documents to retrieve
DEFAULT_TOP_K = 8

# Minimum similarity score for semantic search (cosine similarity)
MIN_SIMILARITY_SCORE = 0.7

# Maximum number of documents to return per vendor
MAX_DOCS_PER_VENDOR = 20

# ============================================================================
# Coverage Estimation Thresholds
# ============================================================================

# KB coverage thresholds (number of docs found)
COVERAGE_THRESHOLDS = {
    "strong": 8,    # 8+ docs -> strong coverage
    "thin": 3,      # 3-7 docs -> thin coverage
    "none": 0       # 0-2 docs -> no coverage
}

# Confidence penalty multipliers based on coverage
COVERAGE_CONFIDENCE_MULTIPLIERS = {
    "strong": 1.0,    # No penalty
    "thin": 0.8,      # 20% penalty
    "none": 0.5       # 50% penalty
}

# ============================================================================
# Metadata Schema for Retrieved Documents
# ============================================================================

class RetrievedDoc(BaseModel):
    """
    Single retrieved document from knowledge base.

    Returned by search_docs() for use in SME agent prompts.
    """

    # Document identification
    atom_id: str = Field(..., description="Unique knowledge atom ID")

    # Core content
    title: str = Field(..., description="Document title")
    summary: str = Field(..., description="Brief summary (1-2 sentences)")
    content: str = Field(..., description="Full text content")

    # Classification
    atom_type: str = Field(..., description="Type: concept, procedure, fault, specification")
    vendor: Optional[str] = Field(None, description="Manufacturer: siemens, rockwell, abb, etc.")
    equipment_type: Optional[str] = Field(None, description="Equipment: vfd, plc, hmi, etc.")

    # Retrieval metadata
    similarity_score: Optional[float] = Field(None, description="Semantic similarity score (0-1)")
    keywords: List[str] = Field(default_factory=list, description="Searchable keywords")

    # Citation information
    source: Optional[str] = Field(None, description="Source document (manual, URL)")
    page_number: Optional[int] = Field(None, description="Page number in source")

    # Quality indicators
    difficulty: Optional[str] = Field(None, description="beginner, intermediate, advanced")
    safety_level: Optional[str] = Field(None, description="info, caution, warning, danger")

    # Technical metadata
    fault_codes: List[str] = Field(default_factory=list, description="Associated fault codes")
    models: List[str] = Field(default_factory=list, description="Equipment models")

    class Config:
        json_schema_extra = {
            "example": {
                "atom_id": "siemens:g120c:f3002",
                "title": "G120C Fault F3002 - DC Bus Overvoltage",
                "summary": "Overvoltage on DC bus, typically caused by regen braking or supply issues.",
                "content": "F3002 indicates DC link voltage exceeded 840V. Check input voltage...",
                "atom_type": "fault",
                "vendor": "siemens",
                "equipment_type": "vfd",
                "similarity_score": 0.92,
                "keywords": ["overvoltage", "DC bus", "F3002", "G120C"],
                "source": "SINAMICS G120C Operating Instructions",
                "page_number": 127,
                "difficulty": "intermediate",
                "safety_level": "warning",
                "fault_codes": ["F3002"],
                "models": ["G120C", "G120"]
            }
        }


# ============================================================================
# RAG Configuration Class
# ============================================================================

class RAGConfig(BaseModel):
    """
    Runtime configuration for RAG retrieval.

    Can be customized per agent or per query.
    """

    # Search parameters
    top_k: int = Field(DEFAULT_TOP_K, description="Number of docs to retrieve", ge=1, le=50)
    min_similarity: float = Field(MIN_SIMILARITY_SCORE, description="Minimum similarity score", ge=0.0, le=1.0)

    # Filtering
    vendor_filter: Optional[str] = Field(None, description="Filter by vendor")
    equipment_filter: Optional[str] = Field(None, description="Filter by equipment type")
    atom_type_filter: Optional[List[str]] = Field(None, description="Filter by atom types")

    # Coverage estimation
    use_coverage_estimation: bool = Field(True, description="Estimate KB coverage")
    coverage_threshold_strong: int = Field(COVERAGE_THRESHOLDS["strong"], ge=1)
    coverage_threshold_thin: int = Field(COVERAGE_THRESHOLDS["thin"], ge=1)

    # Performance
    use_hybrid_search: bool = Field(True, description="Use hybrid semantic + keyword search")
    use_reranking: bool = Field(False, description="Rerank results with LLM (expensive)")

    class Config:
        json_schema_extra = {
            "example": {
                "top_k": 8,
                "min_similarity": 0.7,
                "vendor_filter": "siemens",
                "equipment_filter": "vfd",
                "atom_type_filter": ["fault", "procedure"],
                "use_coverage_estimation": True,
                "use_hybrid_search": True
            }
        }


# ============================================================================
# Agent-Specific Search Profiles
# ============================================================================

# Siemens SME - Prioritize Siemens-specific content
SIEMENS_AGENT_CONFIG = RAGConfig(
    vendor_filter="siemens",
    atom_type_filter=["fault", "procedure", "concept"],
    top_k=10
)

# Rockwell SME - Prioritize Rockwell-specific content
ROCKWELL_AGENT_CONFIG = RAGConfig(
    vendor_filter="rockwell",
    atom_type_filter=["fault", "procedure", "concept"],
    top_k=10
)

# Generic PLC SME - No vendor filter, broad search
GENERIC_AGENT_CONFIG = RAGConfig(
    vendor_filter=None,
    atom_type_filter=["concept", "procedure", "pattern"],
    top_k=12
)

# Safety Agent - Prioritize safety warnings
SAFETY_AGENT_CONFIG = RAGConfig(
    vendor_filter=None,
    atom_type_filter=["fault", "procedure"],
    top_k=8,
    min_similarity=0.8  # Higher threshold for safety-critical info
)

# Agent-specific configurations
AGENT_CONFIGS = {
    "siemens": SIEMENS_AGENT_CONFIG,
    "rockwell": ROCKWELL_AGENT_CONFIG,
    "generic_plc": GENERIC_AGENT_CONFIG,
    "safety": SAFETY_AGENT_CONFIG
}
