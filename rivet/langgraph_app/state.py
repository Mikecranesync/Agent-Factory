"""
State model for Rivet ingestion workflow

Defines the shared state object passed between LangGraph nodes.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RivetState(BaseModel):
    """Shared state for KB ingestion graph"""

    # Job metadata
    job_id: str = Field(..., description="Unique job identifier")
    workflow: str = Field(default="kb_ingest", description="Workflow type")

    # Source data
    source_url: Optional[str] = Field(None, description="URL of document to ingest")
    raw_document: Optional[str] = Field(None, description="Extracted plain text from document")

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (vendor, product, manual type, etc.)"
    )

    # Processed atoms
    atoms: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Structured knowledge atoms extracted from document"
    )

    # Logging & errors
    logs: List[str] = Field(default_factory=list, description="Processing logs")
    errors: List[str] = Field(default_factory=list, description="Error messages")

    # Processing stats
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Processing statistics (tokens, time, etc.)"
    )

    class Config:
        arbitrary_types_allowed = True


class KnowledgeAtom(BaseModel):
    """Schema for a knowledge atom (fault, pattern, procedure, etc.)"""

    atom_type: str = Field(..., description="Type: fault, pattern, procedure, concept")
    vendor: Optional[str] = Field(None, description="Equipment vendor")
    product: Optional[str] = Field(None, description="Product/platform name")

    # Content fields
    title: str = Field(..., description="Descriptive title")
    summary: str = Field(..., description="Brief summary")
    content: str = Field(..., description="Full content/description")

    # Fault-specific
    code: Optional[str] = Field(None, description="Error/fault code")
    symptoms: List[str] = Field(default_factory=list, description="Observable symptoms")
    causes: List[str] = Field(default_factory=list, description="Possible causes")
    fixes: List[str] = Field(default_factory=list, description="Remediation steps")

    # Pattern-specific
    pattern_type: Optional[str] = Field(None, description="Pattern category")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")
    steps: List[str] = Field(default_factory=list, description="Implementation steps")

    # Metadata
    keywords: List[str] = Field(default_factory=list, description="Search keywords")
    difficulty: Optional[str] = Field(None, description="beginner/intermediate/advanced")
    source_url: Optional[str] = Field(None, description="Source document URL")
    source_pages: Optional[str] = Field(None, description="Page numbers in source")

    class Config:
        schema_extra = {
            "example": {
                "atom_type": "fault",
                "vendor": "allen_bradley",
                "product": "ControlLogix",
                "title": "Motor Fault: Overcurrent Trip",
                "summary": "Motor trips on overcurrent protection",
                "content": "When motor draws excessive current...",
                "code": "F0010",
                "symptoms": ["Motor stops suddenly", "Alarm light flashing"],
                "causes": ["Mechanical jam", "Phase loss", "Short circuit"],
                "fixes": ["Check for obstructions", "Test all phases", "Inspect wiring"],
                "keywords": ["motor", "overcurrent", "trip", "fault"],
                "difficulty": "intermediate"
            }
        }
