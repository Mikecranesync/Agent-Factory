"""
Pydantic models for equipment manual data.

Supports both simple retrieval AND diagnostic logic extraction.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


class ManualType(str, Enum):
    """Types of equipment manuals."""
    INSTALLATION = "installation"
    SERVICE = "service"
    TROUBLESHOOTING = "troubleshooting"
    WIRING = "wiring"
    PARTS = "parts"
    MAINTENANCE = "maintenance"
    OPERATORS = "operators"
    SAFETY = "safety"


class DiagnosticStepCondition(str, Enum):
    """Possible conditions in diagnostic flow."""
    IF_YES = "if_yes"
    IF_NO = "if_no"
    IF_SYMPTOM = "if_symptom"
    IF_READING = "if_reading"
    ELSE = "else"


class DiagnosticStep(BaseModel):
    """
    A single step in a diagnostic troubleshooting flow.

    Example:
        {
            "step_id": "1",
            "question": "Is the motor hot to touch?",
            "conditions": {
                "if_yes": "Motor overload likely - check amperage",
                "if_no": "goto step_2"
            },
            "safety_warning": "CRITICAL: Lock out power before inspection"
        }
    """
    step_id: str = Field(..., description="Unique step identifier (e.g., '1', '2a', '3')")
    question: str = Field(..., description="Diagnostic question to ask user")
    conditions: Dict[str, str] = Field(
        ...,
        description="Conditional branches (if_yes/if_no/if_symptom → action or goto)"
    )
    safety_warning: Optional[str] = Field(
        None,
        description="OSHA-compliant safety warning for this step"
    )
    tools_required: List[str] = Field(
        default_factory=list,
        description="Tools needed for this diagnostic step"
    )
    expected_values: Optional[Dict[str, str]] = Field(
        None,
        description="Expected readings/values (e.g., voltage ranges)"
    )


class DiagnosticFlow(BaseModel):
    """
    Complete diagnostic troubleshooting decision tree.

    This is the SECRET WEAPON - not just facts, but LOGIC.
    """
    error_code: Optional[str] = Field(None, description="Equipment error code (if applicable)")
    symptom: str = Field(..., description="Primary symptom being diagnosed")
    equipment_model: str = Field(..., description="Specific equipment model this applies to")
    steps: List[DiagnosticStep] = Field(..., description="Ordered diagnostic steps")
    possible_causes: List[str] = Field(
        default_factory=list,
        description="List of possible root causes"
    )
    resolution_actions: List[str] = Field(
        default_factory=list,
        description="Actions to resolve each possible cause"
    )
    safety_requirements: List[str] = Field(
        default_factory=list,
        description="Overall safety requirements (PPE, lockout/tagout, etc.)"
    )
    estimated_time_minutes: Optional[int] = Field(
        None,
        description="Estimated time to complete diagnosis"
    )
    skill_level: Optional[str] = Field(
        None,
        description="Required technician skill level (beginner/intermediate/expert)"
    )


class ManualMetadata(BaseModel):
    """Metadata extracted from equipment manual."""
    manufacturer: str = Field(..., description="Equipment manufacturer (ABB, Siemens, etc.)")
    equipment_model: str = Field(..., description="Model number/identifier")
    equipment_name: str = Field(..., description="Human-readable equipment name")
    manual_type: ManualType = Field(..., description="Type of manual")
    manual_title: str = Field(..., description="Full manual title")
    manual_version: Optional[str] = Field(None, description="Manual version/revision")
    publication_date: Optional[datetime] = Field(None, description="Manual publication date")
    page_count: Optional[int] = Field(None, description="Total pages in manual")
    language: str = Field(default="en", description="Manual language (ISO 639-1 code)")

    # Quality scores
    quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Quality assessment (0-1, higher is better)"
    )
    completeness_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Completeness of manual (0-1)"
    )

    # Discovery metadata
    source_url: Optional[HttpUrl] = Field(None, description="Original source URL")
    discovered_at: datetime = Field(default_factory=datetime.utcnow, description="Discovery timestamp")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class EquipmentManual(BaseModel):
    """
    Complete equipment manual with metadata AND diagnostic logic.

    This model supports TWO use cases:
    1. Simple search/retrieval (metadata + raw content)
    2. Diagnostic conversations (diagnostic_flows)
    """
    # Identifiers
    id: Optional[str] = Field(None, description="Unique manual ID (UUID in database)")
    manual_id: str = Field(..., description="Human-readable manual identifier")

    # Metadata
    metadata: ManualMetadata = Field(..., description="Manual metadata")

    # Raw content (for search/retrieval)
    raw_content: Optional[str] = Field(
        None,
        description="Raw text extracted from manual (for vector search)"
    )
    chunks: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Text chunks with embeddings (for RAG)"
    )

    # Diagnostic logic (CORE VALUE)
    diagnostic_flows: List[DiagnosticFlow] = Field(
        default_factory=list,
        description="Extracted diagnostic troubleshooting flows"
    )

    # Specs and facts
    specifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Technical specifications (voltage, torque, dimensions, etc.)"
    )
    error_codes: Dict[str, str] = Field(
        default_factory=dict,
        description="Error code definitions"
    )
    maintenance_schedule: Optional[Dict[str, Any]] = Field(
        None,
        description="Recommended maintenance intervals"
    )
    parts_list: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Parts catalog with part numbers"
    )

    # File storage
    file_path: Optional[str] = Field(None, description="Local file path (if downloaded)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    file_hash: Optional[str] = Field(None, description="SHA-256 hash for deduplication")

    # Usage tracking (for Stream 2 - Query Intelligence)
    view_count: int = Field(default=0, description="How many times this manual was accessed")
    diagnostic_session_count: int = Field(
        default=0,
        description="How many diagnostic sessions used this manual"
    )
    last_accessed: Optional[datetime] = Field(
        None,
        description="Last access timestamp"
    )

    # Database fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "manual_id": "ABB-ACH580-SERVICE-v2.1",
                "metadata": {
                    "manufacturer": "ABB",
                    "equipment_model": "ACH580",
                    "equipment_name": "ACH580 Variable Speed Drive",
                    "manual_type": "service",
                    "manual_title": "ACH580 VFD Service Manual",
                    "quality_score": 0.85,
                    "source_url": "https://library.abb.com/...",
                },
                "diagnostic_flows": [
                    {
                        "error_code": "2210",
                        "symptom": "Motor running hot with buzzing sound",
                        "equipment_model": "ACH580",
                        "steps": [
                            {
                                "step_id": "1",
                                "question": "Is the motor hot to touch (>60°C)?",
                                "conditions": {
                                    "if_yes": "Likely motor overload - check amperage",
                                    "if_no": "goto step_2"
                                },
                                "safety_warning": "CRITICAL: Lock out power before inspection",
                                "tools_required": ["Multimeter", "Infrared thermometer"]
                            },
                            {
                                "step_id": "2",
                                "question": "Check motor amperage - is it >110% rated current?",
                                "conditions": {
                                    "if_yes": "Overload confirmed - check mechanical load",
                                    "if_no": "goto step_3"
                                },
                                "expected_values": {
                                    "rated_current": "32A",
                                    "max_safe": "35A"
                                }
                            }
                        ],
                        "possible_causes": [
                            "Mechanical overload",
                            "Bearing failure",
                            "Phase imbalance"
                        ],
                        "safety_requirements": [
                            "Lockout/tagout power",
                            "Wear insulated gloves",
                            "Use safety glasses"
                        ]
                    }
                ],
                "error_codes": {
                    "2210": "Motor overload protection triggered",
                    "2211": "Motor phase loss detected"
                },
                "specifications": {
                    "rated_voltage": "400V",
                    "rated_current": "32A",
                    "rated_power": "22kW"
                }
            }
        }


class ManualSearchQuery(BaseModel):
    """Query model for searching manuals."""
    query: str = Field(..., description="Search query (symptoms, error codes, procedures)")
    manufacturer: Optional[str] = Field(None, description="Filter by manufacturer")
    equipment_model: Optional[str] = Field(None, description="Filter by equipment model")
    manual_type: Optional[ManualType] = Field(None, description="Filter by manual type")
    limit: int = Field(default=5, ge=1, le=50, description="Number of results to return")


class ManualSearchResult(BaseModel):
    """Single search result."""
    manual: EquipmentManual = Field(..., description="Matched manual")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1, higher is better)"
    )
    matched_section: Optional[str] = Field(
        None,
        description="Excerpt from matched section"
    )


class DiagnosticSessionLog(BaseModel):
    """
    Log entry for a diagnostic conversation session.

    This is Stream 2 - Query Intelligence.
    Powers pattern learning and identifies valuable equipment.
    """
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier (hashed for privacy)")

    # Initial query
    initial_symptom: str = Field(..., description="User's initial symptom description")
    equipment_model: Optional[str] = Field(None, description="Equipment model (if known)")
    error_code: Optional[str] = Field(None, description="Error code (if provided)")

    # Diagnostic flow
    steps_taken: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of diagnostic steps executed"
    )
    manuals_referenced: List[str] = Field(
        default_factory=list,
        description="Manual IDs referenced during session"
    )

    # Outcome
    resolution_found: bool = Field(default=False, description="Was issue resolved?")
    root_cause: Optional[str] = Field(None, description="Identified root cause")
    actions_taken: List[str] = Field(
        default_factory=list,
        description="Actions user took to resolve"
    )

    # Session metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    duration_minutes: Optional[int] = Field(None)

    # Learning data
    user_feedback: Optional[str] = Field(
        None,
        description="User feedback on diagnostic quality"
    )
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="User rating (1-5 stars)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "diag-2025-12-08-abc123",
                "user_id": "user-hash-xyz",
                "initial_symptom": "ACH580 VFD showing error 2210 with buzzing motor",
                "equipment_model": "ACH580",
                "error_code": "2210",
                "steps_taken": [
                    {"step": "1", "question": "Is motor hot?", "answer": "Yes"},
                    {"step": "2", "question": "Amperage reading?", "answer": "38A"}
                ],
                "resolution_found": True,
                "root_cause": "Mechanical overload due to seized bearing",
                "actions_taken": [
                    "Locked out power",
                    "Inspected bearings",
                    "Replaced bearing",
                    "Reset VFD"
                ],
                "rating": 5,
                "user_feedback": "Saved me 2 hours of guessing!"
            }
        }
