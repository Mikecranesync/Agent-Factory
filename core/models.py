"""
Core Pydantic Models for Agent Factory

Implements the Universal Knowledge Atom Standard (ATOM_SPEC_UNIVERSAL.md)
for all data types across RIVET, PLC Tutor, and Agent Factory verticals.

Based on:
- IEEE Learning Object Metadata (LOM)
- LRMI / OER Schema
- JSON-LD 1.1 + JSON Schema + Schema.org

All models are Pydantic v2 compatible with full validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from uuid import uuid4


# ============================================================================
# Base Types & Enums
# ============================================================================

class RelationType(str, Enum):
    """Types of relationships between learning objects"""
    IS_PART_OF = "isPartOf"
    HAS_PART = "hasPart"
    REQUIRES = "requires"
    IS_REQUIRED_BY = "isRequiredBy"
    IS_VERSION_OF = "isVersionOf"
    HAS_VERSION = "hasVersion"
    REFERENCES = "references"
    IS_REFERENCED_BY = "isReferencedBy"
    TEACHES = "teaches"
    ASSESSES = "assesses"
    SIMULATES = "simulates"


class EducationalLevel(str, Enum):
    """Educational difficulty levels"""
    INTRO = "intro"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Status(str, Enum):
    """Lifecycle status of knowledge atoms"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


# ============================================================================
# Shared Models
# ============================================================================

class Identifier(BaseModel):
    """External identifier for a learning object"""
    catalog: str = Field(..., description="Identifier namespace (e.g., 'ISBN', 'DOI', 'UUID')")
    entry: str = Field(..., description="Identifier value in that namespace")


class Relation(BaseModel):
    """Relationship between learning objects"""
    kind: RelationType = Field(..., description="Type of relationship")
    target_id: str = Field(..., description="ID of related learning object")
    description: Optional[str] = Field(None, description="Human-readable description of relation")


class Contributor(BaseModel):
    """Person or organization who contributed to this learning object"""
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., description="Role (author, editor, reviewer, publisher, etc.)")
    email: Optional[str] = None
    organization: Optional[str] = None


# ============================================================================
# LearningObject (Base Class)
# ============================================================================

class LearningObject(BaseModel):
    """
    Base class for all knowledge atoms (IEEE LOM-inspired).

    Follows IEEE 1484.12.1-2002 Learning Object Metadata standard
    with extensions for educational applications.
    """

    # Identity
    id: str = Field(
        default_factory=lambda: f"atom:{uuid4().hex[:12]}",
        description="Unique identifier (e.g., 'plc:ab:timer-on-delay')"
    )
    identifiers: List[Identifier] = Field(
        default_factory=list,
        description="External identifiers (ISBN, DOI, etc.)"
    )
    title: str = Field(..., min_length=3, max_length=200, description="Human-readable title")
    description: str = Field(..., min_length=10, max_length=2000, description="Detailed description")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")

    # Lifecycle
    version: str = Field(default="1.0.0", description="Semantic version (major.minor.patch)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: Status = Field(default=Status.DRAFT, description="Lifecycle status")

    # Contributors
    authors: List[str] = Field(default_factory=list, description="Primary authors")
    contributors: List[Contributor] = Field(default_factory=list, description="All contributors")

    # Sources
    source_urls: List[HttpUrl] = Field(default_factory=list, description="Authoritative sources")
    citation: Optional[str] = Field(None, description="Formal citation (APA, IEEE, etc.)")

    # Educational
    educational_level: EducationalLevel = Field(
        default=EducationalLevel.INTRO,
        description="Difficulty level"
    )
    learning_resource_type: str = Field(
        ...,
        description="Type (explanation, example, exercise, simulation, etc.)"
    )
    typical_learning_time_minutes: int = Field(
        ge=1,
        le=480,
        description="Expected learning time in minutes"
    )
    intended_audience: List[str] = Field(
        default_factory=list,
        description="Target audience (student, technician, engineer, manager)"
    )

    # Prerequisites & Objectives
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Atom IDs that should be learned first"
    )
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="What learner will be able to do after completing this"
    )

    # Graph Structure
    relations: List[Relation] = Field(
        default_factory=list,
        description="Relationships to other atoms"
    )
    tags: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible metadata (vendor, platform, topic, etc.)"
    )

    # AI/ML
    embedding: Optional[List[float]] = Field(
        None,
        description="Vector embedding (1536-dim for OpenAI text-embedding-3-small)"
    )
    embedding_model: Optional[str] = Field(
        None,
        description="Model used to generate embedding"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "plc:generic:ohms-law",
                "title": "Ohm's Law: V=I×R",
                "description": "The fundamental relationship between voltage, current, and resistance.",
                "keywords": ["ohms law", "electricity", "V=IR", "voltage", "current", "resistance"],
                "educational_level": "intro",
                "learning_resource_type": "explanation",
                "typical_learning_time_minutes": 10,
                "prerequisites": ["plc:generic:voltage", "plc:generic:current", "plc:generic:resistance"],
                "learning_objectives": [
                    "Calculate voltage given current and resistance",
                    "Calculate current given voltage and resistance",
                    "Calculate resistance given voltage and current"
                ]
            }
        }


# ============================================================================
# PLCAtom (PLC/Automation-Specific)
# ============================================================================

class PLCAtom(LearningObject):
    """
    PLC and industrial automation knowledge atom.

    Extends LearningObject with PLC-specific fields:
    - Vendor/platform information
    - PLC language (ladder, ST, FBD, etc.)
    - Code snippets
    - I/O signal definitions
    - Safety hazards
    """

    # Domain
    domain: Literal[
        "electricity",
        "plc",
        "drives",
        "safety",
        "ai_agent",
        "networking",
        "hmi_scada",
        "motion_control"
    ] = Field(..., description="Technical domain")

    # Vendor/Platform
    vendor: Literal["siemens", "allen_bradley", "generic", "other"] = Field(
        default="generic",
        description="PLC vendor"
    )
    platform: Optional[str] = Field(
        None,
        description="Specific platform (e.g., 'ControlLogix', 'S7-1200')"
    )

    # Programming
    plc_language: Optional[Literal["ladder", "stl", "fbd", "scl", "st"]] = Field(
        None,
        description="PLC programming language"
    )
    code_snippet: Optional[str] = Field(
        None,
        description="Canonical example code"
    )

    # I/O & Signals
    io_signals: List[str] = Field(
        default_factory=list,
        description="Tags/signals involved (e.g., 'Start_PB', 'Motor_Run')"
    )

    # Safety
    hazards: List[str] = Field(
        default_factory=list,
        description="Safety warnings and hazards"
    )
    safety_level: Literal["info", "caution", "warning", "danger"] = Field(
        default="info",
        description="Safety criticality level"
    )

    # Assessment
    quiz_question_ids: List[str] = Field(
        default_factory=list,
        description="Associated quiz questions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "plc:ab:motor-start-stop-seal",
                "title": "3-Wire Motor Start/Stop/Seal-In",
                "description": "Basic motor control with maintained contact seal-in",
                "domain": "plc",
                "vendor": "allen_bradley",
                "platform": "ControlLogix",
                "plc_language": "ladder",
                "code_snippet": """
Rung 0:
    ----] [--------]/[--------( )----
    Start_PB    Stop_PB    Motor_Run

    ----] [--------------------
    Motor_Run (seal-in)
                """,
                "io_signals": ["Start_PB", "Stop_PB", "Motor_Run"],
                "hazards": [
                    "Stop button must be NC for fail-safe operation",
                    "Seal-in contact must be sized for coil current"
                ],
                "safety_level": "caution",
                "educational_level": "intro",
                "learning_resource_type": "example",
                "typical_learning_time_minutes": 15
            }
        }


# ============================================================================
# RIVETAtom (Industrial Maintenance/Troubleshooting)
# ============================================================================

class RootCause(BaseModel):
    """Root cause of a maintenance issue"""
    cause: str = Field(..., description="What causes this symptom")
    likelihood: Literal["common", "occasional", "rare"] = Field(
        default="common",
        description="How common this root cause is"
    )
    verification: str = Field(
        ...,
        description="How to verify this is the actual cause"
    )


class CorrectiveAction(BaseModel):
    """Action to fix a maintenance issue"""
    action: str = Field(..., description="What to do to fix the issue")
    difficulty: Literal["easy", "moderate", "difficult"] = Field(
        default="moderate",
        description="Skill level required"
    )
    estimated_time_minutes: int = Field(
        ...,
        ge=1,
        description="Time to complete action"
    )
    tools_required: List[str] = Field(
        default_factory=list,
        description="Tools needed"
    )
    safety_warnings: List[str] = Field(
        default_factory=list,
        description="Safety precautions"
    )


class RIVETAtom(LearningObject):
    """
    Industrial maintenance and troubleshooting knowledge atom.

    Designed for RIVET platform (maintenance DAAS).
    Includes 6-stage validation pipeline for safety-critical content.
    """

    # Equipment
    equipment_class: str = Field(
        ...,
        description="Type of equipment (motor, pump, conveyor, etc.)"
    )
    manufacturer: Optional[str] = Field(None, description="Equipment manufacturer")
    model: Optional[str] = Field(None, description="Specific model number")

    # Problem Definition
    symptoms: List[str] = Field(
        ...,
        min_length=1,
        description="Observable symptoms (e.g., 'motor won't start')"
    )

    # Diagnosis
    root_causes: List[RootCause] = Field(
        default_factory=list,
        description="Possible root causes ranked by likelihood"
    )
    diagnostic_steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step diagnostic procedure"
    )

    # Resolution
    corrective_actions: List[CorrectiveAction] = Field(
        default_factory=list,
        description="Actions to fix the issue"
    )

    # Context
    constraints: List[str] = Field(
        default_factory=list,
        description="Constraints (equipment must be de-energized, etc.)"
    )

    # Safety
    safety_level: Literal["info", "caution", "warning", "danger"] = Field(
        default="caution",
        description="Safety criticality level"
    )
    lockout_tagout_required: bool = Field(
        default=True,
        description="Whether LOTO is required"
    )

    # Validation (6-stage pipeline)
    validation_stage: int = Field(
        default=1,
        ge=1,
        le=6,
        description="Current validation stage (1=raw, 6=fully validated)"
    )
    validation_notes: List[str] = Field(
        default_factory=list,
        description="Notes from validation process"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rivet:motor:won-t-start",
                "title": "3-Phase Motor Won't Start",
                "description": "Motor hums but doesn't rotate, or doesn't energize at all",
                "equipment_class": "ac_induction_motor",
                "symptoms": [
                    "Motor hums but doesn't rotate",
                    "Contactor energizes but motor doesn't start",
                    "Motor overload trips immediately"
                ],
                "root_causes": [
                    {
                        "cause": "Single-phase condition (one leg of 3-phase power lost)",
                        "likelihood": "common",
                        "verification": "Measure voltage at motor terminals (expect 3-phase balanced)"
                    },
                    {
                        "cause": "Mechanical binding or seized bearings",
                        "likelihood": "occasional",
                        "verification": "Manually rotate shaft (should turn freely)"
                    }
                ],
                "diagnostic_steps": [
                    "Verify power at disconnect (expect 480VAC 3-phase)",
                    "Check contactor operation (should close when energized)",
                    "Measure voltage at motor terminals (expect 480VAC on all 3 phases)",
                    "Check motor rotation by hand (should rotate freely)"
                ],
                "safety_level": "danger",
                "lockout_tagout_required": True,
                "validation_stage": 3
            }
        }


# ============================================================================
# Curriculum Organization
# ============================================================================

class Module(BaseModel):
    """Collection of atoms organized into a learning module"""

    id: str = Field(
        default_factory=lambda: f"module:{uuid4().hex[:12]}",
        description="Unique module identifier"
    )
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)

    atom_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of atom IDs in this module"
    )

    educational_level: EducationalLevel = Field(
        default=EducationalLevel.INTRO,
        description="Overall difficulty level"
    )

    estimated_hours: float = Field(
        ...,
        ge=0.5,
        le=100.0,
        description="Total time to complete module"
    )

    prerequisites: List[str] = Field(
        default_factory=list,
        description="Module IDs that should be completed first"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Course(BaseModel):
    """Collection of modules organized into a course"""

    id: str = Field(
        default_factory=lambda: f"course:{uuid4().hex[:12]}",
        description="Unique course identifier"
    )
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)

    module_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of module IDs in this course"
    )

    estimated_hours: float = Field(
        ...,
        ge=1.0,
        le=500.0,
        description="Total time to complete course"
    )

    price_usd: Optional[float] = Field(
        None,
        ge=0.0,
        description="Course price (null = free)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Video Production Models
# ============================================================================

class VideoScript(BaseModel):
    """Script for a video, generated from knowledge atoms"""

    id: str = Field(
        default_factory=lambda: f"script:{uuid4().hex[:12]}",
        description="Unique script identifier"
    )

    title: str = Field(..., min_length=3, max_length=200, description="Video title")
    description: str = Field(..., min_length=10, max_length=5000, description="Video description (YouTube)")

    # Script Content
    outline: List[str] = Field(
        ...,
        min_length=1,
        description="Bullet-point outline of video sections"
    )
    script_text: str = Field(
        ...,
        min_length=100,
        description="Full narration script with personality markers"
    )
    visual_cues: List[str] = Field(
        default_factory=list,
        description="Visual elements needed (diagrams, code, footage)"
    )

    # Metadata
    atom_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Atoms this video teaches"
    )
    educational_level: EducationalLevel = Field(
        default=EducationalLevel.INTRO,
        description="Difficulty level"
    )
    duration_minutes: int = Field(
        ...,
        ge=3,
        le=30,
        description="Target video duration"
    )

    # SEO
    keywords: List[str] = Field(
        default_factory=list,
        description="Target SEO keywords"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="YouTube tags"
    )

    # Status
    status: Literal["draft", "approved", "in_production", "published"] = Field(
        default="draft",
        description="Script status"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "script:ohms-law-video",
                "title": "Ohm's Law - The Foundation of Electrical Engineering (#3)",
                "description": "Master Ohm's Law (V=I×R) with clear explanations and real-world examples...",
                "outline": [
                    "Hook: This one equation solves 90% of electrical problems",
                    "What is Ohm's Law? (V=I×R)",
                    "Example: Calculate voltage drop across resistor",
                    "Practice: Solve for current given voltage and resistance",
                    "Recap and quiz question"
                ],
                "script_text": "[enthusiastic] This one equation solves 90% of electrical problems...",
                "atom_ids": ["plc:generic:ohms-law"],
                "educational_level": "intro",
                "duration_minutes": 8,
                "keywords": ["ohms law", "V=IR", "electrical calculations"],
                "tags": ["ohms law", "electricity", "electrical engineering", "tutorial"]
            }
        }


class UploadJob(BaseModel):
    """YouTube upload job ready for publishing"""

    id: str = Field(
        default_factory=lambda: f"upload:{uuid4().hex[:12]}",
        description="Unique upload job identifier"
    )

    channel: Literal["industrial_skills_hub", "rivet_troubleshooting"] = Field(
        ...,
        description="Target YouTube channel"
    )

    video_script_id: str = Field(..., description="Associated script ID")

    # Media Files
    audio_path: str = Field(..., description="Path to narration audio (MP3)")
    video_path: str = Field(..., description="Path to final video (MP4)")
    thumbnail_path: str = Field(..., description="Path to thumbnail (JPG/PNG)")

    # YouTube Metadata
    youtube_title: str = Field(..., min_length=3, max_length=100)
    youtube_description: str = Field(..., min_length=10, max_length=5000)
    tags: List[str] = Field(default_factory=list, max_length=500)

    playlist_ids: List[str] = Field(
        default_factory=list,
        description="YouTube playlist IDs to add video to"
    )

    # Publishing
    visibility: Literal["public", "unlisted", "private"] = Field(
        default="public",
        description="Video visibility"
    )
    scheduled_time: Optional[datetime] = Field(
        None,
        description="When to publish (null = publish immediately)"
    )

    # Status
    status: Literal["pending", "uploading", "processing", "published", "failed"] = Field(
        default="pending",
        description="Upload status"
    )
    youtube_video_id: Optional[str] = Field(
        None,
        description="YouTube video ID (populated after upload)"
    )
    error_message: Optional[str] = Field(None, description="Error details if failed")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_at: Optional[datetime] = None


# ============================================================================
# Agent Communication Models
# ============================================================================

class AgentMessage(BaseModel):
    """Message between agents (stored in Supabase agent_messages table)"""

    id: str = Field(
        default_factory=lambda: f"msg:{uuid4().hex[:12]}",
        description="Unique message identifier"
    )

    from_agent: str = Field(..., description="Sending agent name")
    to_agent: str = Field(..., description="Receiving agent name")

    message_type: Literal["task", "notification", "error", "query"] = Field(
        ...,
        description="Message type"
    )

    payload: Dict[str, Any] = Field(
        ...,
        description="Message payload (task details, error info, etc.)"
    )

    status: Literal["pending", "processing", "completed", "failed"] = Field(
        default="pending",
        description="Message status"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class AgentStatus(BaseModel):
    """Agent health status (stored in Supabase agent_status table)"""

    agent_name: str = Field(..., description="Agent identifier")

    status: Literal["running", "idle", "error", "stopped"] = Field(
        ...,
        description="Current agent status"
    )

    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)

    tasks_completed_today: int = Field(default=0, ge=0)
    tasks_failed_today: int = Field(default=0, ge=0)

    current_task: Optional[str] = Field(None, description="Currently executing task")
    error_message: Optional[str] = Field(None, description="Error details if status=error")


# ============================================================================
# Validation Functions
# ============================================================================

def validate_atom_prerequisites(atom: LearningObject) -> bool:
    """
    Validate that prerequisite atoms exist and don't create circular dependencies.

    Note: This is a placeholder. Full implementation requires database access
    to check atom existence and build dependency graph.
    """
    # TODO: Implement in agent logic with database access
    return True


def validate_safety_level(atom: PLCAtom | RIVETAtom) -> bool:
    """
    Ensure safety-critical atoms have appropriate warnings.

    Rules:
    - safety_level="danger" → must have hazards list with items
    - lockout_tagout_required=True → must mention in constraints
    """
    if atom.safety_level == "danger" and not atom.hazards:
        raise ValueError("Atoms with safety_level='danger' must have hazards listed")

    if isinstance(atom, RIVETAtom) and atom.lockout_tagout_required:
        loto_mentioned = any("lockout" in c.lower() or "tagout" in c.lower() or "LOTO" in c
                            for c in atom.constraints)
        if not loto_mentioned:
            raise ValueError("Atoms requiring LOTO must mention it in constraints")

    return True


# ============================================================================
# Export All Models
# ============================================================================

__all__ = [
    # Enums
    "RelationType",
    "EducationalLevel",
    "Status",

    # Base Models
    "Identifier",
    "Relation",
    "Contributor",

    # Learning Objects
    "LearningObject",
    "PLCAtom",
    "RIVETAtom",

    # Supporting Models
    "RootCause",
    "CorrectiveAction",

    # Curriculum
    "Module",
    "Course",

    # Video Production
    "VideoScript",
    "UploadJob",

    # Agent Communication
    "AgentMessage",
    "AgentStatus",

    # Validation
    "validate_atom_prerequisites",
    "validate_safety_level",
]
