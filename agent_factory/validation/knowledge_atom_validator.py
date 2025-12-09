"""
Knowledge Atom Validation Pipeline - 6 Stages

PURPOSE:
    Validates Knowledge Atoms against industry standards before database insertion.
    Like PLC safety validation - multiple checks before allowing operation.

6-STAGE VALIDATION PIPELINE:
    Stage 1: JSON Schema validation
    Stage 2: Manufacturer/product reference validation
    Stage 3: Confidence score calculation verification
    Stage 4: Temporal consistency checks
    Stage 5: Integrity hash generation
    Stage 6: Post-insertion verification (optional)

WHY WE NEED THIS:
    - Prevents data corruption (bad data never enters database)
    - Ensures quality (only validated atoms stored)
    - Provides clear error messages (tells you exactly what's wrong)
    - Maintains integrity (hash verification)

PLC ANALOGY:
    Like industrial equipment safety validation:
    - Stage 1: Input range check (is data structurally valid?)
    - Stage 2: Reference check (does equipment exist in catalog?)
    - Stage 3: Logic validation (do calculations match?)
    - Stage 4: Time sequence check (is timeline logical?)
    - Stage 5: Data signature (generate checksum)
    - Stage 6: Readback verification (confirm write succeeded)
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import jsonschema
from dateutil.parser import parse as parse_datetime

from agent_factory.schemas.knowledge_atom import KNOWLEDGE_ATOM_SCHEMA
from agent_factory.models.knowledge_atom import (
    KnowledgeAtom,
    SourceTier,
    AtomStatus
)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class SchemaViolationError(ValidationError):
    """Raised when atom violates JSON Schema."""
    pass


class InvalidManufacturerError(ValidationError):
    """Raised when manufacturer not in approved list."""
    pass


class ConfidenceScoreMismatchError(ValidationError):
    """Raised when claimed confidence doesn't match calculated."""
    pass


class TemporalInconsistencyError(ValidationError):
    """Raised when dates are inconsistent."""
    pass


class DataCorruptionError(ValidationError):
    """Raised when data corruption detected."""
    pass


# ============================================================================
# APPROVED MANUFACTURERS (Seed List)
# ============================================================================

# This list should be maintained in a database, but we seed it here for MVP
APPROVED_MANUFACTURERS: Set[str] = {
    "ABB",
    "Siemens",
    "Rockwell Automation",
    "Schneider Electric",
    "Carrier",
    "Trane",
    "Mitsubishi Electric",
    "Yaskawa",
    "Danfoss",
    "Honeywell",
    "Johnson Controls",
    "Eaton",
    "GE",
    "Emerson",
    "Phoenix Contact",
    "WAGO",
    "Omron",
    "Allen-Bradley",
    "Magntech",  # Example manufacturer from standard
}


# ============================================================================
# CONFIDENCE SCORE CALCULATION
# ============================================================================

def calculate_confidence_score(
    source_tier: SourceTier,
    corroboration_count: int,
    recency_days: int,
    contradiction_count: int,
    author_reputation: Optional[str] = None
) -> float:
    """
    Calculate overall confidence score from components.

    PURPOSE:
        Transparent confidence calculation based on source quality,
        corroboration, recency, and author reputation.

    ALGORITHM:
        1. Source tier confidence (0.0-1.0):
           - manufacturer_official: 0.95
           - stack_overflow: 0.80
           - official_forum: 0.70
           - reddit: 0.50
           - blog: 0.40
           - anecdotal: 0.20

        2. Corroboration confidence (0.0-1.0):
           - 0 corroborations: 0.50
           - 1 corroboration: 0.70
           - 2 corroborations: 0.85
           - 3+ corroborations: 0.95
           - Penalty: -0.2 per contradiction

        3. Recency confidence (0.0-1.0):
           - < 1 year: 0.95
           - 1-2 years: 0.85
           - 2-3 years: 0.75
           - 3-5 years: 0.60
           - > 5 years: 0.40

        4. Author reputation confidence (0.0-1.0):
           - manufacturer_official: 0.95
           - verified_technician: 0.90
           - expert: 0.80
           - community: 0.60
           - unknown: 0.50

        5. Overall confidence:
           weighted average of components

    ARGS:
        source_tier: Source tier enum value
        corroboration_count: Number of corroborating sources
        recency_days: Days since publication
        contradiction_count: Number of contradicting sources
        author_reputation: Optional author reputation

    RETURNS:
        Overall confidence score (0.0-1.0)

    EXAMPLE:
        >>> score = calculate_confidence_score(
        ...     source_tier=SourceTier.MANUFACTURER_OFFICIAL,
        ...     corroboration_count=3,
        ...     recency_days=180,
        ...     contradiction_count=0,
        ...     author_reputation="manufacturer_official"
        ... )
        >>> assert 0.90 <= score <= 1.0
    """
    # Component 1: Source tier confidence
    source_tier_map = {
        SourceTier.MANUFACTURER_OFFICIAL: 0.95,
        SourceTier.STACK_OVERFLOW: 0.80,
        SourceTier.OFFICIAL_FORUM: 0.70,
        SourceTier.REDDIT: 0.50,
        SourceTier.BLOG: 0.40,
        SourceTier.ANECDOTAL: 0.20,
    }
    source_tier_confidence = source_tier_map.get(source_tier, 0.50)

    # Component 2: Corroboration confidence
    corroboration_base = {
        0: 0.50,
        1: 0.70,
        2: 0.85,
    }
    corroboration_confidence = corroboration_base.get(
        corroboration_count, 0.95  # 3+ corroborations
    )
    # Penalty for contradictions
    corroboration_confidence -= (contradiction_count * 0.2)
    corroboration_confidence = max(0.0, corroboration_confidence)

    # Component 3: Recency confidence
    recency_years = recency_days / 365.25
    if recency_years < 1:
        recency_confidence = 0.95
    elif recency_years < 2:
        recency_confidence = 0.85
    elif recency_years < 3:
        recency_confidence = 0.75
    elif recency_years < 5:
        recency_confidence = 0.60
    else:
        recency_confidence = 0.40

    # Component 4: Author reputation confidence
    author_reputation_map = {
        "manufacturer_official": 0.95,
        "verified_technician": 0.90,
        "expert": 0.80,
        "community": 0.60,
        "unknown": 0.50,
        None: 0.50,
    }
    author_reputation_confidence = author_reputation_map.get(
        author_reputation, 0.50
    )

    # Weighted average (source tier and corroboration weighted higher)
    overall_confidence = (
        source_tier_confidence * 0.35 +  # 35% weight
        corroboration_confidence * 0.35 +  # 35% weight
        recency_confidence * 0.20 +  # 20% weight
        author_reputation_confidence * 0.10  # 10% weight
    )

    return round(overall_confidence, 2)


# ============================================================================
# VALIDATOR CLASS
# ============================================================================

class KnowledgeAtomValidator:
    """
    6-stage validation pipeline for Knowledge Atoms.

    PURPOSE:
        Ensures atoms meet quality standards before database insertion.
        Like PLC safety validation - multiple checks prevent bad data.

    USAGE:
        >>> validator = KnowledgeAtomValidator()
        >>> atom_dict = {...}  # Knowledge Atom as dict
        >>> validator.validate(atom_dict)  # Raises exception if invalid
        >>> # If no exception, atom is valid
    """

    def __init__(
        self,
        confidence_tolerance: float = 0.05,
        approved_manufacturers: Optional[Set[str]] = None
    ):
        """
        Initialize validator.

        ARGS:
            confidence_tolerance: Tolerance for confidence score mismatch (default: 0.05)
            approved_manufacturers: Optional set of approved manufacturers
        """
        self.confidence_tolerance = confidence_tolerance
        self.approved_manufacturers = (
            approved_manufacturers or APPROVED_MANUFACTURERS
        )
        self.json_validator = jsonschema.Draft7Validator(KNOWLEDGE_ATOM_SCHEMA)

    def validate(self, atom: Dict[str, Any]) -> str:
        """
        Run full 6-stage validation pipeline.

        PURPOSE:
            Validates atom through all stages and returns integrity hash.

        STAGES:
            1. JSON Schema validation
            2. Manufacturer/product validation
            3. Confidence score verification
            4. Temporal consistency
            5. Integrity hash generation
            6. (Post-insertion verification done separately)

        ARGS:
            atom: Knowledge Atom as dictionary

        RETURNS:
            Integrity hash (SHA-256 hex digest)

        RAISES:
            SchemaViolationError: If JSON Schema validation fails
            InvalidManufacturerError: If manufacturer not approved
            ConfidenceScoreMismatchError: If confidence score mismatch
            TemporalInconsistencyError: If dates inconsistent
            ValidationError: For other validation errors

        EXAMPLE:
            >>> validator = KnowledgeAtomValidator()
            >>> atom_dict = {...}
            >>> integrity_hash = validator.validate(atom_dict)
            >>> print(f"Atom valid. Hash: {integrity_hash}")
        """
        # Stage 1: JSON Schema validation
        self._validate_schema(atom)

        # Stage 2: Manufacturer/product validation
        self._validate_manufacturers(atom)

        # Stage 3: Confidence score verification
        self._validate_confidence_score(atom)

        # Stage 4: Temporal consistency
        self._validate_temporal_consistency(atom)

        # Stage 5: Integrity hash generation
        integrity_hash = self._generate_integrity_hash(atom)

        return integrity_hash

    def _validate_schema(self, atom: Dict[str, Any]) -> None:
        """
        Stage 1: Validate against JSON Schema.

        PURPOSE:
            Ensures atom structure matches JSON Schema Draft 7 specification.

        RAISES:
            SchemaViolationError: If validation fails
        """
        errors = list(self.json_validator.iter_errors(atom))
        if errors:
            error_messages = [
                f"{error.json_path}: {error.message}"
                for error in errors
            ]
            raise SchemaViolationError(
                f"Atom violates JSON Schema:\n" + "\n".join(error_messages)
            )

    def _validate_manufacturers(self, atom: Dict[str, Any]) -> None:
        """
        Stage 2: Validate manufacturer/product references.

        PURPOSE:
            Ensures manufacturers are in approved list.
            Prevents typos and unknown manufacturers.

        RAISES:
            InvalidManufacturerError: If manufacturer not approved
        """
        manufacturers = atom.get("industrialmaintenance:manufacturers", [])
        for mfg in manufacturers:
            mfg_name = mfg.get("schema:name", "")
            if mfg_name not in self.approved_manufacturers:
                raise InvalidManufacturerError(
                    f"Unknown manufacturer: '{mfg_name}'. "
                    f"Approved manufacturers: {sorted(self.approved_manufacturers)}"
                )

    def _validate_confidence_score(self, atom: Dict[str, Any]) -> None:
        """
        Stage 3: Validate confidence score calculation.

        PURPOSE:
            Ensures claimed confidence matches calculated confidence.
            Prevents manually inflated confidence scores.

        RAISES:
            ConfidenceScoreMismatchError: If claimed != calculated
        """
        # Extract data for calculation
        provider = atom.get("schema:provider", {})
        source_tier_str = provider.get("industrialmaintenance:sourceTier", "")
        source_tier = SourceTier(source_tier_str)

        quality = atom.get("industrialmaintenance:quality", {})
        corroborations = quality.get("industrialmaintenance:corroborations", [])
        contradictions = quality.get("industrialmaintenance:contradictions", [])
        claimed_confidence = quality.get("industrialmaintenance:confidenceScore", 0.0)

        # Calculate recency
        date_created_str = atom.get("schema:dateCreated", "")
        if date_created_str:
            date_created = parse_datetime(date_created_str)
            recency_days = (datetime.now() - date_created).days
        else:
            recency_days = 0

        author_reputation = provider.get("industrialmaintenance:authorReputation")

        # Calculate confidence
        calculated_confidence = calculate_confidence_score(
            source_tier=source_tier,
            corroboration_count=len(corroborations),
            recency_days=recency_days,
            contradiction_count=len(contradictions),
            author_reputation=author_reputation
        )

        # Check within tolerance
        diff = abs(calculated_confidence - claimed_confidence)
        if diff > self.confidence_tolerance:
            raise ConfidenceScoreMismatchError(
                f"Confidence score mismatch. "
                f"Claimed: {claimed_confidence:.2f}, "
                f"Calculated: {calculated_confidence:.2f}, "
                f"Diff: {diff:.2f} (tolerance: {self.confidence_tolerance})"
            )

    def _validate_temporal_consistency(self, atom: Dict[str, Any]) -> None:
        """
        Stage 4: Validate temporal consistency.

        PURPOSE:
            Ensures dates are logically consistent:
            - date_modified >= date_created
            - date_published <= date_created (optional)

        RAISES:
            TemporalInconsistencyError: If dates inconsistent
        """
        date_created_str = atom.get("schema:dateCreated", "")
        date_modified_str = atom.get("schema:dateModified", "")

        if not date_created_str or not date_modified_str:
            raise TemporalInconsistencyError(
                "Missing required dates: dateCreated or dateModified"
            )

        date_created = parse_datetime(date_created_str)
        date_modified = parse_datetime(date_modified_str)

        if date_modified < date_created:
            raise TemporalInconsistencyError(
                f"dateModified ({date_modified}) cannot be before "
                f"dateCreated ({date_created})"
            )

        # Optional: Validate provider date_published
        provider = atom.get("schema:provider", {})
        date_published_str = provider.get("schema:datePublished")
        if date_published_str:
            date_published = parse_datetime(date_published_str)
            # Allow some tolerance for data entry (published could be slightly after created)
            if date_published > date_created + timedelta(days=7):
                raise TemporalInconsistencyError(
                    f"datePublished ({date_published}) is significantly after "
                    f"dateCreated ({date_created})"
                )

    def _generate_integrity_hash(self, atom: Dict[str, Any]) -> str:
        """
        Stage 5: Generate integrity hash.

        PURPOSE:
            Creates SHA-256 hash for integrity verification.
            Detects data corruption or tampering.

        RETURNS:
            SHA-256 hex digest

        EXAMPLE:
            >>> hash1 = validator._generate_integrity_hash(atom)
            >>> hash2 = validator._generate_integrity_hash(atom)
            >>> assert hash1 == hash2  # Deterministic
        """
        # Sort keys for deterministic hashing
        atom_json = json.dumps(atom, sort_keys=True)
        return hashlib.sha256(atom_json.encode()).hexdigest()

    def verify_post_insertion(
        self,
        atom: Dict[str, Any],
        retrieved_atom: Dict[str, Any],
        expected_hash: str
    ) -> None:
        """
        Stage 6: Verify atom after database insertion (optional).

        PURPOSE:
            Confirms data wasn't corrupted during insertion.
            Like PLC readback verification after write.

        ARGS:
            atom: Original atom dict
            retrieved_atom: Atom retrieved from database
            expected_hash: Integrity hash from Stage 5

        RAISES:
            DataCorruptionError: If hashes don't match
        """
        retrieved_hash = self._generate_integrity_hash(retrieved_atom)
        if retrieved_hash != expected_hash:
            raise DataCorruptionError(
                f"Atom corrupted after insertion. "
                f"Expected hash: {expected_hash}, "
                f"Retrieved hash: {retrieved_hash}"
            )


__all__ = [
    "KnowledgeAtomValidator",
    "calculate_confidence_score",
    "SchemaViolationError",
    "InvalidManufacturerError",
    "ConfidenceScoreMismatchError",
    "TemporalInconsistencyError",
    "DataCorruptionError",
    "ValidationError",
]
