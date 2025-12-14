"""
State model for Rivet KB ingestion pipeline
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RivetState(BaseModel):
    """
    Shared state object for the KB ingestion graph

    Tracks the complete lifecycle of a document through:
    1. Discovery (finding source URL)
    2. Download (fetching document)
    3. Parsing (extracting structured atoms)
    4. Critique (validation)
    5. Indexing (storing in Postgres+pgvector)
    """

    # Job metadata
    job_id: str = Field(..., description="Unique job identifier")
    workflow: str = Field(default="kb_ingest", description="Workflow type")

    # Source information
    source_url: Optional[str] = Field(None, description="URL of source document")
    source_type: Optional[str] = Field(None, description="Type: pdf, html, markdown")

    # Document content
    raw_document: Optional[str] = Field(None, description="Extracted plain text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Vendor, product, etc.")

    # Parsed output
    atoms: List[Dict[str, Any]] = Field(default_factory=list, description="Structured knowledge atoms")

    # Tracking and diagnostics
    logs: List[str] = Field(default_factory=list, description="Processing logs")
    errors: List[str] = Field(default_factory=list, description="Error messages")

    # Statistics
    atoms_created: int = Field(default=0, description="Number of atoms extracted")
    atoms_indexed: int = Field(default=0, description="Number of atoms stored in DB")

    class Config:
        arbitrary_types_allowed = True
