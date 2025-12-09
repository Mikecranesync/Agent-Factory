"""
Industrial Maintenance Knowledge Atom - Pydantic Models

PURPOSE:
    Type-safe Python representations of Knowledge Atoms based on v1.0 standard.
    Like PLC UDT library - ensures consistent data structures across all systems.

WHAT THIS PROVIDES:
    1. KnowledgeAtom: Main model for industrial maintenance knowledge units
    2. ManufacturerReference: Manufacturer metadata (name, URL)
    3. ProductFamily: Product family metadata (name, identifier)
    4. KnowledgeSource: Provenance tracking (source tier, platform, author)
    5. Quality: Confidence scoring and corroboration tracking
    6. ConfidenceComponents: Granular confidence breakdown
    7. VectorEmbedding: Embedding metadata (model, dimension)
    8. Corroboration: Supporting evidence from other sources

WHY WE NEED THIS:
    - Data quality: Validates against industry standards (Schema.org, JSON-LD)
    - Type safety: Pydantic validates at runtime (catch errors early)
    - Interoperability: Compatible with major platforms (Stripe, GitHub, Google)
    - Future-proof: Built on W3C recommendations, not invented standards

PLC ANALOGY:
    Like industrial equipment UDT library:
    - KnowledgeAtom = Equipment diagnostic UDT (error code, resolution, metadata)
    - ManufacturerReference = Equipment vendor UDT (name, contact info)
    - Quality = Quality score UDT (confidence, validation status)
    - All knowledge uses same base structure (consistent diagnostic interface)

STANDARDS COMPLIANCE:
    - Schema.org (45M+ domains)
    - JSON-LD 1.1 (W3C Recommendation)
    - JSON Schema Draft 7 (IETF)
    - OpenAPI 3.1.0 (Linux Foundation)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# ENUMS (Controlled Vocabularies)
# ============================================================================

class AtomType(str, Enum):
    """Type of knowledge unit."""
    ERROR_CODE = "error_code"
    COMPONENT_SPEC = "component_spec"
    PROCEDURE = "procedure"
    TROUBLESHOOTING_TIP = "troubleshooting_tip"
    SAFETY_REQUIREMENT = "safety_requirement"
    WIRING_DIAGRAM = "wiring_diagram"
    MAINTENANCE_SCHEDULE = "maintenance_schedule"


class Severity(str, Enum):
    """Severity level for error codes and safety requirements."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class SourceTier(str, Enum):
    """Data provenance tier (highest to lowest confidence)."""
    MANUFACTURER_OFFICIAL = "manufacturer_official"  # Official manual/documentation
    STACK_OVERFLOW = "stack_overflow"  # Stack Overflow verified answers
    OFFICIAL_FORUM = "official_forum"  # Manufacturer/vendor forum
    REDDIT = "reddit"  # Reddit posts (r/industrial, r/PLC, etc.)
    BLOG = "blog"  # Technical blogs
    ANECDOTAL = "anecdotal"  # Unverified sources


class AuthorReputation(str, Enum):
    """Author/source reputation level."""
    VERIFIED_TECHNICIAN = "verified_technician"
    MANUFACTURER_OFFICIAL = "manufacturer_official"
    EXPERT = "expert"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class AtomStatus(str, Enum):
    """Validation status of knowledge atom."""
    VALIDATED = "validated"  # Corroborated by multiple sources
    PENDING_VALIDATION = "pending_validation"  # Needs verification
    CONTRADICTED = "contradicted"  # Conflicting information exists
    DEPRECATED = "deprecated"  # Superseded by newer information


class IndustrialProtocol(str, Enum):
    """Industrial communication protocols."""
    ETHERNET_IP = "ethernet_ip"
    MODBUS = "modbus"
    MODBUS_RTU = "modbus_rtu"
    MODBUS_TCP = "modbus_tcp"
    OPC_UA = "opc_ua"
    OPC_DA = "opc_da"
    PROFIBUS = "profibus"
    PROFINET = "profinet"
    CANOPEN = "canopen"
    J1939 = "j1939"
    HART = "hart"


class ComponentType(str, Enum):
    """Industrial equipment component types."""
    PLC = "plc"
    VFD = "vfd"
    DRIVE = "drive"
    MOTOR = "motor"
    SENSOR = "sensor"
    VALVE = "valve"
    PUMP = "pump"
    COMPRESSOR = "compressor"
    MOTOR_CONTROLLER = "motor_controller"
    POWER_SUPPLY = "power_supply"
    HMI = "hmi"
    SOFT_STARTER = "soft_starter"


class IndustryVertical(str, Enum):
    """Industry verticals where knowledge applies."""
    HVAC = "hvac"
    MANUFACTURING = "manufacturing"
    PUMPING = "pumping"
    FOOD_BEVERAGE = "food_beverage"
    WATER_TREATMENT = "water_treatment"
    MINING = "mining"
    POWER_GENERATION = "power_generation"
    OIL_GAS = "oil_gas"
    AEROSPACE = "aerospace"
    AUTOMOTIVE = "automotive"
    MARINE = "marine"


# ============================================================================
# NESTED MODELS
# ============================================================================

class ManufacturerReference(BaseModel):
    """
    Manufacturer reference with name and URL.

    PURPOSE:
        Links knowledge to specific equipment manufacturer.
        Like PLC equipment catalog UDT.

    EXAMPLE:
        >>> mfg = ManufacturerReference(
        ...     name="ABB",
        ...     url="https://abb.com"
        ... )
    """
    type_: str = Field(
        default="industrialmaintenance:ManufacturerReference",
        alias="@type",
        description="JSON-LD type identifier"
    )
    name: str = Field(
        ...,
        alias="schema:name",
        min_length=2,
        max_length=100,
        description="Manufacturer name (e.g., 'ABB', 'Siemens')"
    )
    url: Optional[str] = Field(
        None,
        alias="schema:url",
        description="Manufacturer website URL"
    )

    class Config:
        populate_by_name = True


class ProductFamily(BaseModel):
    """
    Product family reference (e.g., 'ABB ACS880 Series').

    PURPOSE:
        Groups knowledge by product line for better retrieval.
        Like PLC product catalog UDT.

    EXAMPLE:
        >>> product = ProductFamily(
        ...     name="ABB ACS880 Series",
        ...     identifier="abb_acs880"
        ... )
    """
    type_: str = Field(
        default="industrialmaintenance:ProductFamily",
        alias="@type",
        description="JSON-LD type identifier"
    )
    name: str = Field(
        ...,
        alias="schema:name",
        min_length=2,
        max_length=150,
        description="Product family name"
    )
    identifier: Optional[str] = Field(
        None,
        alias="schema:identifier",
        description="Machine-readable identifier (slug)"
    )

    class Config:
        populate_by_name = True


class Corroboration(BaseModel):
    """
    Supporting evidence from another source.

    PURPOSE:
        Tracks corroborating evidence that increases confidence.
        Like PLC alarm correlation - multiple sensors confirm issue.

    EXAMPLE:
        >>> corr = Corroboration(
        ...     atom_id="urn:industrial-maintenance:atom:uuid",
        ...     description="Stack Overflow answer confirms this solution",
        ...     source_platform="stack_overflow"
        ... )
    """
    atom_id: str = Field(
        ...,
        alias="@id",
        description="Reference to corroborating atom"
    )
    description: str = Field(
        ...,
        alias="schema:description",
        min_length=10,
        max_length=500,
        description="How this source corroborates"
    )
    source_platform: str = Field(
        ...,
        alias="industrialmaintenance:sourcePlatform",
        description="Platform where corroboration found"
    )

    class Config:
        populate_by_name = True


class ConfidenceComponents(BaseModel):
    """
    Granular confidence score breakdown.

    PURPOSE:
        Transparent confidence calculation components.
        Like PLC diagnostic breakdown - why we believe this fix works.

    COMPONENTS:
        - source_tier_confidence: How trustworthy is the source?
        - corroboration_confidence: How many sources agree?
        - recency_confidence: How recent is this information?
        - author_reputation_confidence: How credible is the author?
    """
    source_tier_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence based on source tier (0-1)"
    )
    corroboration_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence based on corroborations (0-1)"
    )
    recency_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence based on recency (0-1)"
    )
    author_reputation_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence based on author reputation (0-1)"
    )


class Quality(BaseModel):
    """
    Quality and confidence metadata.

    PURPOSE:
        Tracks confidence score, corroborations, contradictions.
        Like PLC diagnostic confidence score - how sure are we?

    WHAT THIS CONTAINS:
        - confidence_score: Overall confidence (0-1)
        - confidence_components: Breakdown of confidence calculation
        - corroborations: Supporting evidence
        - contradictions: Conflicting information
        - citation_count: How often referenced
        - date_modified: Last quality update
    """
    confidence_score: float = Field(
        ...,
        alias="industrialmaintenance:confidenceScore",
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0-1)"
    )
    confidence_components: ConfidenceComponents = Field(
        ...,
        alias="industrialmaintenance:confidenceComponents",
        description="Granular confidence breakdown"
    )
    corroborations: List[Corroboration] = Field(
        default_factory=list,
        alias="industrialmaintenance:corroborations",
        description="Supporting evidence from other sources"
    )
    contradictions: List[Any] = Field(
        default_factory=list,
        alias="industrialmaintenance:contradictions",
        description="Conflicting information"
    )
    date_modified: datetime = Field(
        ...,
        alias="schema:dateModified",
        description="Last quality metadata update"
    )
    citation_count: int = Field(
        default=0,
        alias="industrialmaintenance:citationCount",
        ge=0,
        description="Number of times cited by other atoms"
    )

    class Config:
        populate_by_name = True


class KnowledgeSource(BaseModel):
    """
    Provenance tracking for knowledge atom.

    PURPOSE:
        Records where this knowledge came from (source tier, platform, author).
        Like PLC audit trail - who/what/when/where.

    WHAT THIS CONTAINS:
        - source_tier: Trustworthiness of source (manufacturer > stack overflow > reddit)
        - source_platform: Specific platform (e.g., 'abb_manual', 'stack_overflow')
        - url: Link to original source
        - date_published: When source published this
        - author: Optional author name
        - author_reputation: Author's credibility level
    """
    type_: str = Field(
        default="industrialmaintenance:KnowledgeSource",
        alias="@type",
        description="JSON-LD type identifier"
    )
    source_tier: SourceTier = Field(
        ...,
        alias="industrialmaintenance:sourceTier",
        description="Data provenance tier"
    )
    source_platform: str = Field(
        ...,
        alias="industrialmaintenance:sourcePlatform",
        min_length=2,
        max_length=100,
        description="Specific platform (e.g., 'abb_manual', 'r_industrial')"
    )
    url: str = Field(
        ...,
        alias="schema:url",
        description="URL to original source"
    )
    date_published: Optional[datetime] = Field(
        None,
        alias="schema:datePublished",
        description="When source published this information"
    )
    author: Optional[str] = Field(
        None,
        alias="schema:author",
        description="Author name (if known)"
    )
    author_reputation: Optional[AuthorReputation] = Field(
        None,
        alias="industrialmaintenance:authorReputation",
        description="Author's reputation level"
    )

    class Config:
        populate_by_name = True


class VectorEmbedding(BaseModel):
    """
    Vector embedding metadata (model, dimension, signature).

    PURPOSE:
        Tracks which embedding model was used and metadata for integrity.
        Like PLC data signature - ensures data hasn't been tampered with.

    WHAT THIS CONTAINS:
        - model: Embedding model name (e.g., 'text-embedding-3-large')
        - dimension: Vector dimension (e.g., 3072)
        - signature: Hash for integrity checking
    """
    type_: str = Field(
        default="industrialmaintenance:VectorEmbedding",
        alias="@type",
        description="JSON-LD type identifier"
    )
    model: str = Field(
        ...,
        alias="industrialmaintenance:model",
        description="Embedding model name"
    )
    dimension: int = Field(
        ...,
        alias="industrialmaintenance:dimension",
        gt=0,
        description="Vector dimension"
    )
    signature: Optional[str] = Field(
        None,
        alias="industrialmaintenance:signature",
        description="Hash for integrity checking"
    )

    class Config:
        populate_by_name = True


# ============================================================================
# MAIN MODEL
# ============================================================================

class KnowledgeAtom(BaseModel):
    """
    Industrial Maintenance Knowledge Atom (v1.0 Standard).

    PURPOSE:
        Single unit of validated industrial maintenance knowledge.
        Like PLC diagnostic entry - error code + resolution + context.

    WHAT THIS CONTAINS:
        - Core content: name, description, resolution, keywords
        - Context: manufacturers, products, protocols, industries
        - Provenance: source tier, platform, author
        - Quality: confidence score, corroborations, contradictions
        - Metadata: dates, status, embedding info

    WHY WE NEED THIS:
        - Data quality: Validates against industry standards
        - Interoperability: Compatible with major platforms
        - Future-proof: Built on W3C recommendations
        - Prevents corruption: 6-stage validation pipeline

    STANDARDS COMPLIANCE:
        - Schema.org (45M+ domains)
        - JSON-LD 1.1 (W3C Recommendation)
        - JSON Schema Draft 7 (IETF)
        - OpenAPI 3.1.0 (Linux Foundation)

    EXAMPLE:
        >>> atom = KnowledgeAtom(
        ...     atom_id="urn:industrial-maintenance:atom:uuid",
        ...     atom_type=AtomType.ERROR_CODE,
        ...     name="Error F032: Firmware Version Mismatch",
        ...     description="The drive shows error F032...",
        ...     resolution="1. Power cycle. 2. Reset to factory...",
        ...     keywords=["F032", "firmware", "mismatch"],
        ...     severity=Severity.HIGH,
        ...     manufacturers=[...],
        ...     provider=KnowledgeSource(...),
        ...     quality=Quality(...),
        ...     status=AtomStatus.VALIDATED
        ... )
    """
    # JSON-LD metadata
    context: str = Field(
        default="https://industrialmaintenance.schema.org/context/v1.0",
        alias="@context",
        description="JSON-LD context for semantic meaning"
    )
    atom_id: str = Field(
        ...,
        alias="@id",
        description="Unique identifier (urn:industrial-maintenance:atom:{uuid})"
    )
    type_: List[str] = Field(
        default=["schema:Thing", "industrialmaintenance:KnowledgeAtom"],
        alias="@type",
        description="JSON-LD type identifiers"
    )

    # Atom metadata
    atom_version: str = Field(
        default="1.0",
        description="Schema version"
    )
    atom_type: AtomType = Field(
        ...,
        description="Type of knowledge unit"
    )

    # Core content
    name: str = Field(
        ...,
        alias="schema:name",
        min_length=5,
        max_length=255,
        description="Human-readable title"
    )
    description: str = Field(
        ...,
        alias="schema:description",
        min_length=20,
        max_length=5000,
        description="Detailed explanation"
    )
    resolution: Optional[str] = Field(
        None,
        alias="industrialmaintenance:resolution",
        description="How to fix (for error codes)"
    )
    keywords: List[str] = Field(
        ...,
        alias="schema:keywords",
        min_length=1,
        max_length=10,
        description="Search keywords"
    )
    severity: Optional[Severity] = Field(
        None,
        alias="industrialmaintenance:severity",
        description="Severity level (for error codes/safety)"
    )

    # Context
    manufacturers: List[ManufacturerReference] = Field(
        ...,
        alias="industrialmaintenance:manufacturers",
        min_length=1,
        description="Applicable manufacturers"
    )
    product_families: Optional[List[ProductFamily]] = Field(
        None,
        alias="industrialmaintenance:productFamilies",
        description="Applicable product families"
    )
    protocols: Optional[List[IndustrialProtocol]] = Field(
        None,
        alias="industrialmaintenance:protocols",
        description="Industrial protocols applicable"
    )
    component_types: Optional[List[ComponentType]] = Field(
        None,
        alias="industrialmaintenance:componentTypes",
        description="Component types applicable"
    )
    industries_applicable: Optional[List[IndustryVertical]] = Field(
        None,
        alias="industrialmaintenance:industriesApplicable",
        description="Industry verticals where this applies"
    )

    # Provenance
    provider: KnowledgeSource = Field(
        ...,
        alias="schema:provider",
        description="Source of this knowledge"
    )

    # Quality
    quality: Quality = Field(
        ...,
        alias="industrialmaintenance:quality",
        description="Quality and confidence metadata"
    )

    # Status
    status: AtomStatus = Field(
        ...,
        alias="industrialmaintenance:status",
        description="Validation status"
    )
    validation_notes: Optional[str] = Field(
        None,
        alias="industrialmaintenance:validationNotes",
        description="Notes about validation process"
    )
    deprecation_reason: Optional[str] = Field(
        None,
        alias="industrialmaintenance:deprecationReason",
        description="Why deprecated (if status=deprecated)"
    )

    # Temporal
    date_created: datetime = Field(
        ...,
        alias="schema:dateCreated",
        description="When atom created"
    )
    date_modified: datetime = Field(
        ...,
        alias="schema:dateModified",
        description="Last modification time"
    )

    # Vector embedding (optional - added after creation)
    text_embedding: Optional[VectorEmbedding] = Field(
        None,
        alias="industrialmaintenance:textEmbedding",
        description="Vector embedding metadata"
    )

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator("atom_id")
    @classmethod
    def validate_atom_id(cls, v: str) -> str:
        """Validate atom_id follows URN pattern."""
        if not v.startswith("urn:industrial-maintenance:atom:"):
            raise ValueError(
                f"atom_id must start with 'urn:industrial-maintenance:atom:', got: {v}"
            )
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords_count(cls, v: List[str]) -> List[str]:
        """Validate keywords count (1-10)."""
        if not (1 <= len(v) <= 10):
            raise ValueError(f"keywords must have 1-10 items, got: {len(v)}")
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'KnowledgeAtom':
        """Validate date_modified >= date_created."""
        if self.date_modified < self.date_created:
            raise ValueError(
                f"date_modified ({self.date_modified}) cannot be before "
                f"date_created ({self.date_created})"
            )
        return self

    @classmethod
    def create(
        cls,
        atom_type: AtomType,
        name: str,
        description: str,
        keywords: List[str],
        manufacturers: List[ManufacturerReference],
        provider: KnowledgeSource,
        confidence_score: float,
        confidence_components: ConfidenceComponents,
        status: AtomStatus = AtomStatus.PENDING_VALIDATION,
        **kwargs
    ) -> 'KnowledgeAtom':
        """
        Factory method to create a new Knowledge Atom with sensible defaults.

        PURPOSE:
            Simplifies atom creation with automatic ID generation and timestamps.

        EXAMPLE:
            >>> atom = KnowledgeAtom.create(
            ...     atom_type=AtomType.ERROR_CODE,
            ...     name="Error F032: Firmware Mismatch",
            ...     description="...",
            ...     keywords=["F032", "firmware"],
            ...     manufacturers=[mfg],
            ...     provider=source,
            ...     confidence_score=0.95,
            ...     confidence_components=components
            ... )
        """
        atom_uuid = uuid4()
        now = datetime.utcnow()

        return cls(
            atom_id=f"urn:industrial-maintenance:atom:{atom_uuid}",
            atom_type=atom_type,
            name=name,
            description=description,
            keywords=keywords,
            manufacturers=manufacturers,
            provider=provider,
            quality=Quality(
                confidence_score=confidence_score,
                confidence_components=confidence_components,
                date_modified=now
            ),
            status=status,
            date_created=now,
            date_modified=now,
            **kwargs
        )


__all__ = [
    "KnowledgeAtom",
    "ManufacturerReference",
    "ProductFamily",
    "KnowledgeSource",
    "Quality",
    "ConfidenceComponents",
    "Corroboration",
    "VectorEmbedding",
    "AtomType",
    "Severity",
    "SourceTier",
    "AuthorReputation",
    "AtomStatus",
    "IndustrialProtocol",
    "ComponentType",
    "IndustryVertical",
]
